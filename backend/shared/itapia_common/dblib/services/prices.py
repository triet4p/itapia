from datetime import datetime
from typing import List

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import Engine

from redis.client import Redis

from itapia_common.dblib.crud.prices import get_daily_prices, get_intraday_prices, \
    get_latest_intraday_price, get_tickers_by_sector, add_intraday_candle, get_last_history_date
from itapia_common.dblib.crud.general_update import bulk_insert
from itapia_common.schemas.entities.prices import Price, PriceDataPoint

from .metadata import APIMetadataService

import itapia_common.dblib.db_config as dbcfg

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Prices Service of DB')

class APIPricesService:
    def __init__(self, rdbms_session: Session, redis_client: Redis,
                 metadata_service: APIMetadataService):
        self.rdbms_session = rdbms_session
        self.redis_client = redis_client
        self.metadata_service = metadata_service
        
    def get_daily_prices(self, ticker: str, skip: int, limit: int) -> Price:
        """Retrieve and package historical daily price data for a ticker.
        
        Args:
            ticker (str): Ticker symbol to retrieve prices for.
            skip (int): Number of records to skip (for pagination).
            limit (int): Maximum number of records to return (for pagination).
            
        Returns:
            Price: Price data object containing metadata and price points.
        """
        logger.info(f"SERVICE: Preparing daily prices for ticker {ticker}")
        metadata = self.metadata_service.get_validate_ticker_info(ticker, 'daily')
        
        price_rows = get_daily_prices(self.rdbms_session, dbcfg.DAILY_PRICES_TABLE_NAME,
                                      ticker, skip, limit)
        
        # Convert data to Pydantic objects
        price_points = [
            PriceDataPoint(
                timestamp=int(row['collect_date'].timestamp()), 
                **row
            ) for row in price_rows
        ]
        
        return Price(metadata=metadata, 
                                datas=price_points)
        
    def get_daily_prices_by_sector(self, sector_code: str, skip: int, limit: int) -> List[Price]:
        """Retrieve and package daily price data for all stocks in a sector.
        
        Args:
            sector_code (str): Sector code to retrieve prices for.
            skip (int): Number of records to skip (for pagination).
            limit (int): Maximum number of records to return (for pagination).
            
        Returns:
            List[Price]: List of price data objects for each ticker in the sector.
        """
        logger.info(f"SERVICE: Preparing daily prices for sector {sector_code}...")
        
        # 1. Get list of tickers in this sector
        tickers_in_sector = get_tickers_by_sector(self.rdbms_session, dbcfg.TICKER_METADATA_TABLE_NAME,
                                                  sector_code.upper())
        
        all_payloads: List[Price] = []
        
        if not tickers_in_sector:
            # Could return empty list or raise error depending on requirements
            # Returning empty list is usually more client-friendly
            return all_payloads

        
        # 2. Iterate through each ticker and create payload for it
        for ticker in tickers_in_sector:
            try:
                # --- REUSE EXISTING LOGIC ---
                # Call function to get data for a single ticker
                single_ticker_payload = self.get_daily_prices(
                    ticker=ticker, 
                    skip=skip, 
                    limit=limit
                )
                if single_ticker_payload.datas: # Only add if there is price data
                    all_payloads.append(single_ticker_payload)
            except Exception as e:
                # Skip tickers with errors and log
                logger.warn(f"Warning: Could not fetch data for ticker {ticker}. Error: {e}")
                continue
                
        return all_payloads
    
    def get_intraday_prices(self, ticker: str, latest_only: bool = False) -> Price:
        """Retrieve and package intraday price data from Redis for a ticker.
        
        Args:
            ticker (str): Ticker symbol to retrieve prices for.
            latest_only (bool, optional): If True, only retrieve the latest price. Defaults to False.
            
        Returns:
            Price: Price data object containing metadata and price points.
            
        Raises:
            ValueError: If no intraday data is found for the ticker.
        """
        logger.info(f"SERVICE: Preparing intraday prices for ticker {ticker}")
        metadata = self.metadata_service.get_validate_ticker_info(ticker, 'intraday')

        if latest_only:
            price_rows = [get_latest_intraday_price(self.redis_client, ticker.upper(), dbcfg.INTRADAY_STREAM_PREFIX)]
        else:
            price_rows = get_intraday_prices(self.redis_client, ticker.upper(), dbcfg.INTRADAY_STREAM_PREFIX)
            
        if not price_rows or price_rows[0] is None:
            raise ValueError(f'Intraday data not found for ticker {ticker}')
        
        price_points = [
            PriceDataPoint(
                timestamp=int(row['last_update_utc'].timestamp()),
                **row
            ) for row in price_rows
        ]
        
        return Price(metadata=metadata,
                                datas=price_points)
        
class DataPricesService:
    def __init__(self, engine: Engine, redis_client: Redis = None):
        """Initialize the data prices service.
        
        Args:
            engine (Engine): Database engine for RDBMS operations.
            redis_client (Redis, optional): Redis client for cache operations. Defaults to None.
        """
        self.engine = engine
        self.redis_client = redis_client
        
    def add_daily_prices(self, data: list[dict]|pd.DataFrame,
                         unique_cols: list[str]):
        """Add daily price data to the database.
        
        Args:
            data (list[dict] | pd.DataFrame): Price data to add.
            unique_cols (list[str]): List of column names that uniquely identify records.
        """
        bulk_insert(self.engine, dbcfg.DAILY_PRICES_TABLE_NAME, data, unique_cols,
                    chunk_size=2000, on_conflict='update')
        
    def add_intraday_prices(self, candle_data: dict,
                            ticker: str):
        """Add intraday price data to Redis.
        
        Args:
            candle_data (dict): Candle data to add.
            ticker (str): Ticker symbol for the candle data.
        """
        add_intraday_candle(self.redis_client, ticker, candle_data, 
                            dbcfg.INTRADAY_STREAM_PREFIX, max_entries=300)
        
    def get_last_history_date(self, 
                             tickers: list[str],
                             default_return_date: datetime):
        """Get the last date for which price history exists.
        
        Args:
            tickers (list[str]): List of ticker symbols to check.
            default_return_date (datetime): Default date to return if no history exists.
            
        Returns:
            datetime: Last date with price history.
        """
        return get_last_history_date(self.engine, dbcfg.DAILY_PRICES_TABLE_NAME, tickers, default_return_date)