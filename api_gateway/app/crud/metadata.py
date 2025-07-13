import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

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

def get_all_sectors(db: Session):
    """
    Lấy toàn bộ thông tin về các nhóm ngành từ bảng 'sectors'.
    """
    query = text("SELECT sector_code, sector_name FROM sectors ORDER BY sector_name;")
    result = db.execute(query)
    # .mappings().all() trả về list các dict-like objects
    return result.mappings().all()
    