# crud/prices.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from redis.client import Redis
from datetime import datetime

def get_daily_prices(db: Session, ticker: str, skip: int = 0, limit: int = 500):
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