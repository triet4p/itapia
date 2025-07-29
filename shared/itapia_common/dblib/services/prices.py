from datetime import datetime
from typing import List

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import Engine

from redis.client import Redis

from itapia_common.dblib.crud.prices import get_daily_prices, get_intraday_prices, \
    get_latest_intraday_price, get_tickers_by_sector, add_intraday_candle, get_last_history_date
from itapia_common.dblib.crud.general_update import bulk_insert
from itapia_common.dblib.schemas.prices import PriceDataPoint, PriceFullPayload

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
        
    def get_daily_prices(self, ticker: str, skip: int, limit: int) -> PriceFullPayload:
        """Lấy và đóng gói dữ liệu giá lịch sử hàng ngày cho một ticker."""
        logger.info(f"SERVICE: Preparing daily prices for ticker {ticker}")
        metadata = self.metadata_service.get_validate_ticker_info(ticker, 'daily')
        
        price_rows = get_daily_prices(self.rdbms_session, dbcfg.DAILY_PRICES_TABLE_NAME,
                                      ticker, skip, limit)
        
        # Chuyển đổi dữ liệu thành các đối tượng Pydantic
        price_points = [
            PriceDataPoint(
                timestamp=int(row['collect_date'].timestamp()), 
                **row
            ) for row in price_rows
        ]
        
        return PriceFullPayload(metadata=metadata, 
                                datas=price_points)
        
    def get_daily_prices_by_sector(self, sector_code: str, skip: int, limit: int):
        """Lấy và đóng gói dữ liệu giá hàng ngày cho tất cả các cổ phiếu trong một nhóm ngành."""
        logger.info(f"SERVICE: Preparing daily prices for sector {sector_code}...")
        
        # 1. Lấy danh sách các ticker thuộc ngành này
        tickers_in_sector = get_tickers_by_sector(self.rdbms_session, dbcfg.TICKER_METADATA_TABLE_NAME,
                                                  sector_code.upper())
        
        all_payloads: List[PriceFullPayload] = []
        
        if not tickers_in_sector:
            # Có thể trả về list rỗng hoặc ném lỗi tùy theo yêu cầu
            # Trả về list rỗng thường thân thiện với client hơn
            return all_payloads

        
        # 2. Lặp qua từng ticker và tạo payload cho nó
        for ticker in tickers_in_sector:
            try:
                # --- TÁI SỬ DỤNG LOGIC ĐÃ CÓ ---
                # Gọi lại hàm lấy dữ liệu cho một ticker duy nhất
                single_ticker_payload = self.get_daily_prices(
                    ticker=ticker, 
                    skip=skip, 
                    limit=limit
                )
                if single_ticker_payload.datas: # Chỉ thêm vào nếu có dữ liệu giá
                    all_payloads.append(single_ticker_payload)
            except Exception as e:
                # Bỏ qua các ticker bị lỗi và ghi log
                logger.warn(f"Warning: Could not fetch data for ticker {ticker}. Error: {e}")
                continue
                
        return all_payloads
    
    def get_intraday_prices(self, ticker: str, latest_only: bool = False):
        """Lấy và đóng gói dữ liệu giá trong ngày từ Redis cho một ticker."""
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
        
        return PriceFullPayload(metadata=metadata,
                                datas=price_points)
        
class DataPricesService:
    def __init__(self, engine: Engine, redis_client: Redis = None):
        self.engine = engine
        self.redis_client = redis_client
        
    def add_daily_prices(self, data: list[dict]|pd.DataFrame,
                         unique_cols: list[str]):
        bulk_insert(self.engine, dbcfg.DAILY_PRICES_TABLE_NAME, data, unique_cols,
                    chunk_size=2000, on_conflict='update')
        
    def add_intraday_prices(self, candle_data: dict,
                            ticker: str):
        add_intraday_candle(self.redis_client, ticker, candle_data, 
                            dbcfg.INTRADAY_STREAM_PREFIX, max_entries=300)
        
    def get_last_history_date(self, 
                             tickers: list[str],
                             default_return_date: datetime):
        return get_last_history_date(self.engine, dbcfg.DAILY_PRICES_TABLE_NAME, tickers, default_return_date)