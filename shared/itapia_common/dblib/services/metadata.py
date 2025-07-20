from typing import List, Literal

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from itapia_common.dblib.crud.metadata import get_ticker_metadata, get_all_sectors
from itapia_common.dblib.schemas.metadata import TickerMetadata, SectorMetadata

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Metadata Service of DB')

class APIMetadataService:
    def __init__(self, rdbms_session: Session):
        self.rdbms_session = rdbms_session
        self.metadata_cache = get_ticker_metadata(rdbms_connection=rdbms_session)
        
    def get_validate_ticker_info(self, ticker: str, data_type: Literal['daily', 'intraday', 'news']):
        logger.info(f"SERVICE: Preparing ticker info metadata of ticker {ticker}...")
        ticker_info = self.metadata_cache.get(ticker.upper())
        if not ticker_info:
            raise ValueError(f"Ticker '{ticker}' not found.")
        ticker_info['ticker'] = ticker
        ticker_info['data_type'] = data_type
        return TickerMetadata(**ticker_info)
    
    def get_all_sectors(self) -> List[SectorMetadata]:
        """Lấy danh sách tất cả các nhóm ngành được hỗ trợ."""
        logger.info("SERVICE: Preparing all sectors...")
        sector_rows = get_all_sectors(self.rdbms_session) # Giả sử đã tạo file metadata_crud.py
        
        # Chuyển đổi kết quả thô thành danh sách các đối tượng Pydantic
        return [SectorMetadata(**row) for row in sector_rows]
    
class DataMetadataService:
    def __init__(self, engine: Engine):
        self.metadata_cache = get_ticker_metadata(rdbms_engine=engine)
    
    def get_all_tickers(self) -> list[str]:
        return list(self.metadata_cache.keys())