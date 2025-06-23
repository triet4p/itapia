import yfinance as yf
from typing import List, Literal
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine
import os

from utils import FetchException, TO_FETCH_TICKERS, read_context, write_context

def _extract_raw_data(tickers: List[str],
                     start_collect_date: datetime,
                     end_collect_date: datetime) -> pd.DataFrame:
    _start_collect_date = start_collect_date.strftime('%Y-%m-%d')
    _end_collect_date = end_collect_date.strftime('%Y-%m-%d')
    raw_df = yf.download(tickers, start=_start_collect_date, end=_end_collect_date, 
                         group_by='ticker', threads=False)
    if raw_df is None:
        raise FetchException('Error while fetch raw data from YFinance!')
    return raw_df

def _reconstruct_table(raw_df: pd.DataFrame, tickers: List[str],
                       numeric_type: Literal['float32', 'float64']='float32'):
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
    return stacked_df[cols]

def _handle_missing_data(df: pd.DataFrame, 
                         start_date: datetime, end_date: datetime, 
                         features: List[str]):
    df[features] = df.groupby('ticker')[features].ffill().bfill()
    return df[(df['collect_date'] >= start_date) & (df['collect_date'] <= end_date)].copy()

def _create_engine():
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
    
def _load_to_db(engine, df: pd.DataFrame, selected_cols: List[str]):
    df[selected_cols].to_sql(
        'daily_prices',
        engine,
        if_exists='append',
        index=False
    )
    
def full_pipeline():
    try:
        context = read_context()
        now_date = datetime.now()
        start_date = datetime.strptime(context['START'], '%Y-%m-%d')
        end_date = datetime(now_date.year, now_date.month, now_date.day) - timedelta(days=5)
        
        start_collect_date = start_date - timedelta(days=30)
        end_collect_date = end_date + timedelta(days=2)
        
        raw_df = _extract_raw_data(TO_FETCH_TICKERS, start_collect_date, end_collect_date)
        
        # 2. Transform
        reconstructed_df = _reconstruct_table(raw_df, TO_FETCH_TICKERS, 'float32')
        cleaned_df = _handle_missing_data(reconstructed_df, start_date, end_date, features=['open', 'high', 'low', 'close', 'volume'])
        
        if cleaned_df.empty:
            print("Không có dữ liệu hợp lệ sau khi làm sạch.")
            # Vẫn cập nhật context để lần sau không thử lại khoảng ngày này nữa
            new_start_date = end_date + timedelta(days=1)
            write_context({'START': new_start_date.strftime('%Y-%m-%d')})
            return

        # 3. Load
        engine = _create_engine()
        selected_cols = ['collect_date', 'ticker', 'open', 'high', 'low', 'close', 'volume']
        _load_to_db(engine, cleaned_df, selected_cols)
        print(f"Đã lưu thành công {len(cleaned_df)} dòng dữ liệu.")
        
        # --- Cập nhật Context sau khi thành công ---
        new_start_date = end_date + timedelta(days=1)
        write_context({
            'START': new_start_date.strftime('%Y-%m-%d')
        })
        print(f"Cập nhật thành công! Lần chạy tiếp theo sẽ bắt đầu từ {new_start_date.strftime('%Y-%m-%d')}.")

        write_context({
            'START': new_start_date.strftime('%Y-%m-%d')
        })
    except FetchException as e:
        print(f"Một lỗi đã xảy ra trong pipeline: {e}")
    except Exception as e:
        print(f"Một lỗi không mong muốn đã xảy ra: {e}")
    
full_pipeline()

