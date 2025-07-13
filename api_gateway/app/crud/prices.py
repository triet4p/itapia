# crud/prices.py

from sqlalchemy.orm import Session
from sqlalchemy import text
from redis.client import Redis
from datetime import datetime
import pandas as pd

_metadata_cache = None
def get_metadata(db: Session):
    global _metadata_cache
    if _metadata_cache is not None:
        return _metadata_cache
    print('Load metadata into cache') 
    query = text("""
            SELECT 
                t.ticker_sym as ticker, 
                t.company_name, 
                e.exchange_code, 
                e.currency, 
                e.timezone,
                e.open_time,
                e.close_time,
                s.sector_name
            FROM 
                tickers t
            JOIN 
                exchanges e ON t.exchange_code = e.exchange_code
            JOIN 
                sectors s ON t.sector_code = s.sector_code
            WHERE 
                t.is_active = TRUE;
        """)
    result = db.execute(query)
    df = pd.DataFrame(result.fetchall(), columns=result.keys())
    _metadata_cache = df.set_index('ticker').to_dict('index')
    return _metadata_cache
    

def get_history_prices(db: Session, ticker: str, skip: int = 0, limit: int = 500):
    query = text("""
        SELECT * FROM daily_prices 
        WHERE ticker = :ticker 
        ORDER BY collect_date DESC 
        OFFSET :skip LIMIT :limit
    """)
    
    result = db.execute(query, {"ticker": ticker, "skip": skip, "limit": limit})
    return result.mappings().all()

def get_intraday_prices(redis_conn: Redis, ticker: str):
    if not redis_conn:
        return None
    redis_key = f'intraday_stream:{ticker}'
    entries = redis_conn.xrange(redis_key)
    data_lst = []
    if entries:
        for entry_id, data in entries:
            for key, value in data.items():
                if key in ['open', 'high', 'low', 'last_price']:
                    data[key] = float(value)
                elif key == 'last_volume':
                    data[key] = int(value)
                elif key == 'last_update_utc':
                    data[key] = datetime.fromisoformat(data[key])
            data['ticker'] = ticker
            data_lst.append(data)
        return data_lst
    else:
        return []

def get_latest_intraday_price(redis_conn: Redis, ticker: str):
    if not redis_conn:
        return None
    redis_key = f'intraday_stream:{ticker}'
    entries = redis_conn.xrevrange(redis_key, count=1)
    if not entries:
        return None
    entry_id, data = entries[0]
    for key, value in data.items():
        if key in ['open', 'high', 'low', 'close']:
            data[key] = float(value)
        elif key == 'volume':
            data[key] = int(value)
        elif key == 'last_update_utc':
            data[key] = datetime.fromisoformat(data[key])
    data['ticker'] = ticker
    
    return data