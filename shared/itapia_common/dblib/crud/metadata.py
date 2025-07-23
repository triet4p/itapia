# common/dblib/crud/metadata.py
from sqlalchemy.orm import Session
from sqlalchemy import Engine, text, Connection
import pandas as pd
from threading import Lock

class TickerMetadataCache:
    _instance = None
    _cache = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TickerMetadataCache, cls).__new__(cls)
        return cls._instance

    def get(self, rdbms_connection: Session | Connection):
        if self._cache is not None:
            return self._cache
        with self._lock:
            if self._cache is not None:
                return self._cache
            print('Loading metadata into cache')
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
            result = rdbms_connection.execute(query)
            
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            self._cache = df.set_index('ticker').to_dict('index')
        return self._cache

_metadata_cache = TickerMetadataCache()

def get_ticker_metadata(rdbms_connection: Session|Connection = None,
                        rdbms_engine: Engine = None):
    if rdbms_connection is None and rdbms_engine is None:
        raise ValueError("Required at least connection or engine")
    if rdbms_connection is not None:
        return _metadata_cache.get(rdbms_connection)
    with rdbms_engine.connect() as connection:
        return _metadata_cache.get(connection)

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
    