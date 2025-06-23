import yfinance as yf
from typing import List, Literal
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine, Engine, text
import os
import sys

from utils import FetchException, TO_FETCH_TICKERS_BY_REGION, DEFAULT_START_DATE

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
    df[features] = df.groupby('ticker')[features].ffill().bfill()
    return df[(df['collect_date'] >= start_date) & (df['collect_date'] <= end_date)].copy()

def _create_postgre_engine():
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
    
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    
    db_url = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    
    try:
        engine = create_engine(db_url)
        print('Successfully connect')
        return engine
    except Exception as e:
        err_msg = f'Failed connection to {db_url}'
        print(err_msg)
        raise FetchException(err_msg)
    
def _load_to_db(engine: Engine, df: pd.DataFrame, selected_cols: List[str]):
    with engine.begin() as conn:
        df[selected_cols].to_sql(
            'history_prices',
            conn,
            if_exists='append',
            index=False,
            chunksize=1000
        )
    
def _get_last_date_from_db(engine: Engine, region: str):
    tickers = tuple(TO_FETCH_TICKERS_BY_REGION[region])
    query = f"SELECT MAX(collect_date) FROM history_prices WHERE ticker IN {tickers};"
    stmt = text(query)
    
    try:
        with engine.connect() as connection:
            result = connection.execute(stmt).scalar()
            if result:
                # Chuyển đổi từ date của DB sang datetime của Python
                return datetime.combine(result, datetime.min.time())
            return None # Trả về None nếu bảng trống
    except Exception as e:
        print(f"Lỗi khi truy vấn ngày cuối cùng từ CSDL: {e}")
        # Nếu có lỗi (ví dụ bảng chưa tồn tại), coi như chưa có dữ liệu
        return None
    
def full_pipeline(region: str):
    try:
        print(f'Lưu cho khu vực {region}')
        engine = _create_postgre_engine()
        last_date = _get_last_date_from_db(engine, region)
        if last_date:
            start_date = last_date + timedelta(days=1)
        else:
            start_date = DEFAULT_START_DATE
            
        now_date = datetime.now()           
        delta_day = 0
        if now_date.isoweekday() == 1:
            delta_day = 2
        elif now_date.isoweekday() == 7:
            delta_day = 1

        end_date = datetime(now_date.year, now_date.month, now_date.day) - timedelta(days=delta_day)
        
        start_collect_date = start_date - timedelta(days=30)
        end_collect_date = end_date + timedelta(days=delta_day)
        
        print(f'Bắt đầu lấy từ {start_date} tới {end_date}')
        
        raw_df = _extract_raw_data(TO_FETCH_TICKERS_BY_REGION[region], start_collect_date, end_collect_date)
        
        # 2. Transform
        reconstructed_df = _reconstruct_table(raw_df, 'float32')
        cleaned_df = _handle_missing_data(reconstructed_df, start_date, end_date, features=['open', 'high', 'low', 'close', 'volume'])
        
        if cleaned_df.empty:
            print("Không có dữ liệu hợp lệ sau khi làm sạch.")
            return

        # 3. Load
        
        selected_cols = ['collect_date', 'ticker', 'open', 'high', 'low', 'close', 'volume']
        _load_to_db(engine, cleaned_df, selected_cols)
        print(f"Đã lưu thành công {len(cleaned_df)} dòng dữ liệu.")
    
        print(f"Cập nhật thành công!")
    except FetchException as e:
        print(f"Một lỗi đã xảy ra trong pipeline: {e}")
    except Exception as e:
        print(f"Một lỗi không mong muốn đã xảy ra: {e}")
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Require region parameter (americas, europe, asia_pacific)")
        sys.exit(1)
    
    target_region = sys.argv[1].lower()
    
    full_pipeline(region=target_region)
    
    
