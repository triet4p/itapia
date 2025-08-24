"""Daily stock price fetching and processing pipeline.

This module implements a pipeline to fetch historical daily stock prices
from Yahoo Finance, process the data, and store it in the database.
"""

from typing import List, Literal

from datetime import datetime, timedelta, timezone
import pandas as pd

import yfinance as yf

from .utils import FetchException, DEFAULT_RETURN_DATE

from itapia_common.dblib.session import get_singleton_rdbms_engine
from itapia_common.dblib.services import DataPricesService, DataMetadataService
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger(id='Prices Batch Processor')

def _extract_raw_data(tickers: List[str],
                     start_collect_date: datetime,
                     end_collect_date: datetime) -> pd.DataFrame:
    """Extract raw stock price data for a list of tickers within a time frame.

    Args:
        tickers (List[str]): List of stock ticker symbols to fetch data for.
        start_collect_date (datetime): Start date for data collection.
        end_collect_date (datetime): End date for data collection.

    Returns:
        pd.DataFrame: Raw stock price data from Yahoo Finance.

    Raises:
        FetchException: If there is an error fetching data from Yahoo Finance.
    """
    _start_collect_date = start_collect_date.strftime('%Y-%m-%d')
    _end_collect_date = end_collect_date.strftime('%Y-%m-%d')
    raw_df = yf.Tickers(tickers).history(period='max', interval='1d',
                                         start=_start_collect_date,
                                         end=_end_collect_date,
                                         group_by='ticker',
                                         threads=False).swaplevel(0, 1, axis=1)
    if raw_df is None:
        raise FetchException('Error while fetch raw data from YFinance!')
    return raw_df

def _reconstruct_table(raw_df: pd.DataFrame, numeric_type: Literal['float32', 'float64']='float32'):
    """Restructure multi-column DataFrame and convert numeric data types.

    Args:
        raw_df (pd.DataFrame): Raw stock price data with multi-level columns.
        numeric_type (Literal['float32', 'float64']): Numeric type for price data.

    Returns:
        pd.DataFrame: Restructured DataFrame with single-level columns.
    """
    stacked_df = raw_df.stack(level='Ticker', future_stack=True)
    stacked_df.reset_index(inplace=True)
    stacked_df.rename(columns={
        'Date': 'collect_date',
        'Ticker': 'ticker',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    }, inplace=True)
    
    cols = ['collect_date', 'ticker', 'open', 'high', 'low', 'close', 'volume']
    stacked_df.columns.name = None
    
    for col in cols[2:]:
        stacked_df[col] = stacked_df[col].astype(numeric_type)
    
    return stacked_df[cols]

def _handle_missing_data(df: pd.DataFrame, 
                         start_date: datetime, end_date: datetime, 
                         features: List[str]):
    """Handle missing data using forward-fill and backward-fill methods.

    Args:
        df (pd.DataFrame): DataFrame with stock price data.
        start_date (datetime): Start date for filtering data.
        end_date (datetime): End date for filtering data.
        features (List[str]): List of column names to apply fill operations.

    Returns:
        pd.DataFrame: DataFrame with missing values filled.
    """
    # Convert Python datetime to Pandas Timestamp
    pd_start_date = pd.Timestamp(start_date)
    pd_end_date = pd.Timestamp(end_date)
    
    # Handle missing data 
    df['collect_date'] = pd.to_datetime(df['collect_date'], utc=True)
    df[features] = df.groupby('ticker')[features].ffill().bfill()
    
    filtered_df = df[(df['collect_date'] >= pd_start_date) & (df['collect_date'] <= pd_end_date)]
    
    return filtered_df.copy()
    
def full_pipeline(metadata_service: DataMetadataService,
                  prices_service: DataPricesService):
    """Execute complete pipeline to fetch historical daily stock prices.

    Process:
    1. Determine time window for data collection (from last date in DB to yesterday).
    2. Call yfinance API to fetch raw data.
    3. Restructure and clean data (handle missing values).
    4. Write cleaned data to PostgreSQL database.

    Args:
        metadata_service (DataMetadataService): Service to access ticker metadata.
        prices_service (DataPricesService): Service to manage price data storage.
    """
    try:
        # 1. Determine timing
        logger.info('Identify time window to process ...')
        tickers = metadata_service.get_all_tickers()
        
        last_date = prices_service.get_last_history_date(tickers, DEFAULT_RETURN_DATE)
        start_date = last_date + timedelta(days=1)
            
        now_date = datetime.now(timezone.utc)      
        delta_day = 0
        if now_date.isoweekday() == 1:
            delta_day = 2
        elif now_date.isoweekday() == 7:
            delta_day = 1
            
        delta_day += 1

        end_date = datetime(now_date.year, now_date.month, now_date.day,
                            22, 0, 0, tzinfo=timezone.utc) - timedelta(days=delta_day)
        
        logger.info(f'Start collect from {start_date} to {end_date} for {len(tickers)} tickers from Yahoo Finance API...')
        
        if start_date >= end_date:
            logger.info('Invalid date')
            return
        
        start_collect_date = start_date - timedelta(days=30)
        end_collect_date = end_date + timedelta(days=delta_day)
        
        raw_df = _extract_raw_data(tickers, start_collect_date, end_collect_date)
        
        # 2. Transform
        logger.info('Reconstructing and handling missing data ...')
        reconstructed_df = _reconstruct_table(raw_df, 'float32')
        cleaned_df = _handle_missing_data(reconstructed_df, start_date, end_date, features=['open', 'high', 'low', 'close', 'volume'])
        
        if cleaned_df.empty:
            logger.err("Empty data after cleaning phase.")
            return

        # 3. Load
        logger.info('Loading data into DB ...')
        selected_cols = ['collect_date', 'ticker', 'open', 'high', 'low', 'close', 'volume']
        selected_df = cleaned_df[selected_cols].copy()
        prices_service.add_daily_prices(data=selected_df,
                                        unique_cols=['collect_date', 'ticker'])
        logger.info(f"Successfully save {len(cleaned_df)} records.")
    except FetchException as e:
        logger.err(f"A fetch exception occured: {e}")
    except Exception as e:
        logger.err(f"An unknown exception occured: {e}")
    
if __name__ == '__main__':
    engine = get_singleton_rdbms_engine()
    prices_service = DataPricesService(engine)
    metadata_service = DataMetadataService(engine)
    full_pipeline(metadata_service=metadata_service, prices_service=prices_service)