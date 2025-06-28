import yfinance as yf
from typing import List, Literal
from datetime import datetime, timedelta, timezone
import pandas as pd
import sys

from utils import FetchException, TO_FETCH_TICKERS_BY_REGION
from db_manager import PostgreDBManager


def _extract_raw_data(tickers: List[str],
                     start_collect_date: datetime,
                     end_collect_date: datetime) -> pd.DataFrame:
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
    # Chuyển đổi datetime của Python sang Timestamp của Pandas
    pd_start_date = pd.Timestamp(start_date)
    pd_end_date = pd.Timestamp(end_date)
    
    # Xử lý missing data 
    df['collect_date'] = pd.to_datetime(df['collect_date'], utc=True)
    df[features] = df.groupby('ticker')[features].ffill().bfill()
    
    filtered_df = df[(df['collect_date'] >= pd_start_date) & (df['collect_date'] <= pd_end_date)]
    
    return filtered_df.copy()
    
def full_pipeline(region: Literal['americas', 'europe', 'asia_pacific'],
                  table_name: str,
                  db_mng: PostgreDBManager):
    """
    Pipeline lấy dữ liệu giá lịch sử (OHLCV) của các cổ phiếu thuộc 1 region được chỉ định
    rồi xử lý giá trị thiếu và lưu vào Postgre SQL

    Args:
        region (Literal[&#39;americas&#39;, &#39;europe&#39;, &#39;asia_pacific&#39;]): Khu vực được hỗ trợ.
            Dữ liệu thường phải lấy theo khu vực vì timezone khác nhau.
        table_name (str): Tên bảng được lưu trong CSDL
        db_manager (PostgreDBManager): Quản lý truy cập CSDL
    """
    try:
        print(f'Fetch history data for region {region}.')
        last_date = db_mng.get_last_history_date(region)
        start_date = last_date + timedelta(days=1)
            
        now_date = datetime.now(timezone.utc)      
        delta_day = 0
        if now_date.isoweekday() == 1:
            delta_day = 2
        elif now_date.isoweekday() == 7:
            delta_day = 1

        end_date = datetime(now_date.year, now_date.month, now_date.day, tzinfo=timezone.utc) - timedelta(days=delta_day)
        
        print(f'Start collect from {start_date} to {end_date}')
        
        if start_date >= end_date:
            print('Invalid date')
            return
        
        start_collect_date = start_date - timedelta(days=30)
        end_collect_date = end_date + timedelta(days=delta_day)
        
        raw_df = _extract_raw_data(TO_FETCH_TICKERS_BY_REGION[region], start_collect_date, end_collect_date)
        
        # 2. Transform
        reconstructed_df = _reconstruct_table(raw_df, 'float32')
        cleaned_df = _handle_missing_data(reconstructed_df, start_date, end_date, features=['open', 'high', 'low', 'close', 'volume'])
        
        if cleaned_df.empty:
            print("Empty data after cleaning phase.")
            return

        # 3. Load
        
        selected_cols = ['collect_date', 'ticker', 'open', 'high', 'low', 'close', 'volume']
        selected_df = cleaned_df[selected_cols].copy()
        db_mng.bulk_insert(table_name, selected_df, 
                           unique_cols=['collect_date', 'ticker'],
                           chunk_size=1000,
                           on_conflict='update')
        print(f"Successfully save {len(cleaned_df)} records.")
    except FetchException as e:
        print(f"A fetch exception occured: {e}")
    except Exception as e:
        print(f"An unknown exception occured: {e}")
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Require region parameter (americas, europe, asia_pacific)")
        sys.exit(1)
    
    target_region = sys.argv[1].lower()
    
    TABLE_NAME = 'history_prices'
    
    db_mng = PostgreDBManager()
    
    full_pipeline(region=target_region, table_name=TABLE_NAME, db_mng=db_mng)
    
    
