# common/dblib/crud/metadata.py
from sqlalchemy.orm import Session
from sqlalchemy import Engine, text, Connection
import pandas as pd
from threading import Lock

from itapia_common.dblib.cache.memory import SingletonInMemoryCache

def _load_ticker_metadata_from_db(db_connectable: Session|Connection):
    query = text("""
                SELECT 
                    t.ticker_sym as ticker, 
                    t.company_name, 
                    e.exchange_code, 
                    e.currency, 
                    e.timezone,
                    e.open_time,
                    e.close_time,
                    s.sector_code,
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
    result = db_connectable.execute(query)

    df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df.set_index('ticker').to_dict('index')

def get_ticker_metadata(rdbms_connection: Session|Connection = None,
                        rdbms_engine: Engine = None) -> dict[str, any]:
    if rdbms_connection is None and rdbms_engine is None:
        raise ValueError("Required at least connection or engine")
    
    def loader():
        """Hàm loader được truyền vào cache manager."""
        if rdbms_connection:
            return _load_ticker_metadata_from_db(rdbms_connection)
        else: # rdbms_engine
            with rdbms_engine.connect() as connection:
                return _load_ticker_metadata_from_db(connection)
    
    _metadata_cache = SingletonInMemoryCache()
    
    return _metadata_cache.get_or_set(
        cache_key='ticker_metadata',
        loader_func=loader
    )

def get_all_sectors(rdbms_connection: Session|Connection = None,
                    rdbms_engine: Engine = None):
    if rdbms_connection is None and rdbms_engine is None:
        raise ValueError("Required at least connection or engine")
    
    query = text("SELECT sector_code, sector_name FROM sectors ORDER BY sector_name;")
    
    if rdbms_connection is not None:
        result = rdbms_connection.execute(query)
    else:
        with rdbms_engine.connect() as conn:
            result = conn.execute(query)
    # .mappings().all() trả về list các dict-like objects
    return result.mappings().all()
    