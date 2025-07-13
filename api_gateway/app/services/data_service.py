from fastapi import HTTPException
from sqlalchemy.orm import Session
from redis.client import Redis
from typing import List

from app.crud.metadata import get_metadata, get_all_sectors
from app.crud.prices import get_daily_prices, get_intraday_prices, \
    get_latest_intraday_price, get_tickers_by_sector
from app.crud.news import get_news

from app.schemas.metadata import SectorPayload, TickerMetadata
from app.schemas.prices import PriceDataPoint, PriceFullPayload
from app.schemas.news import NewsPoint, NewsFullPayload

class DataService:
    def __init__(self, db: Session, redis_conn: Redis):
        self.db = db
        self.redis_conn = redis_conn
        self.metadata_cache = get_metadata(db)
        
    def _get_validated_ticker_info(self, ticker: str):
        ticker_info = self.metadata_cache.get(ticker.upper())
        if not ticker_info:
            raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found.")
        return ticker_info
    
    def get_daily_prices_payload(self, ticker: str, skip: int, limit: int):
        ticker_info = self._get_validated_ticker_info(ticker)
        ticker_info['data_type'] = 'daily'
        
        price_rows = get_daily_prices(self.db, ticker, skip, limit)
        
        # Chuyển đổi dữ liệu thành các đối tượng Pydantic
        price_points = [
            PriceDataPoint(
                timestamp=int(row['collect_date'].timestamp()), 
                **row
            ) for row in price_rows
        ]
        
        return PriceFullPayload(metadata=TickerMetadata(**ticker_info), 
                                datas=price_points)
        
    def get_daily_prices_payload_by_sector(self, sector_code: str, skip: int, limit: int):
        """
        Lấy dữ liệu giá hàng ngày cho tất cả các cổ phiếu trong một nhóm ngành.
        """
        print(f"Service: Preparing daily prices for sector {sector_code}...")
        
        # 1. Lấy danh sách các ticker thuộc ngành này
        tickers_in_sector = get_tickers_by_sector(self.db, sector_code.upper())
        
        if not tickers_in_sector:
            # Có thể trả về list rỗng hoặc ném lỗi tùy theo yêu cầu
            # Trả về list rỗng thường thân thiện với client hơn
            return []

        all_payloads: List[PriceFullPayload] = []
        
        # 2. Lặp qua từng ticker và tạo payload cho nó
        for ticker in tickers_in_sector:
            try:
                # --- TÁI SỬ DỤNG LOGIC ĐÃ CÓ ---
                # Gọi lại hàm lấy dữ liệu cho một ticker duy nhất
                single_ticker_payload = self.get_daily_prices_payload(
                    ticker=ticker, 
                    skip=skip, 
                    limit=limit
                )
                if single_ticker_payload.datas: # Chỉ thêm vào nếu có dữ liệu giá
                    all_payloads.append(single_ticker_payload)
            except Exception as e:
                # Bỏ qua các ticker bị lỗi và ghi log
                print(f"Warning: Could not fetch data for ticker {ticker}. Error: {e}")
                continue
                
        return all_payloads
        
    def get_intraday_prices_payload(self, ticker: str, latest_only: bool = False):
        ticker_info = self._get_validated_ticker_info(ticker)
        ticker_info['data_type'] = 'intraday'

        if latest_only:
            price_rows = [get_latest_intraday_price(self.redis_conn, ticker.upper())]
        else:
            price_rows = get_intraday_prices(self.redis_conn, ticker.upper())
            
        if not price_rows or price_rows[0] is None:
            raise HTTPException(status_code=400, detail=f'Intraday data not found for ticker {ticker}')
        
        price_points = [
            PriceDataPoint(
                timestamp=int(row['last_update_utc'].timestamp()),
                **row
            ) for row in price_rows
        ]
        
        return PriceFullPayload(metadata=TickerMetadata(**ticker_info),
                                datas=price_points)
        
    def get_news_payload(self, ticker: str, skip: int, limit: int):
        ticker_info = self._get_validated_ticker_info(ticker)
        ticker_info['data_type'] = 'news'
        
        news_rows = get_news(self.db, ticker, skip=skip, limit=limit)
        
        news_points = [
            NewsPoint(
                collect_ts=int(row['collect_time'].timestamp()),
                publish_ts=int(row['publish_time'].timestamp()) if row['publish_time'] else None,
                **row
            ) for row in news_rows
        ]
        
        return NewsFullPayload(metadata=TickerMetadata(**ticker_info),
                               datas=news_points) 
    
    def get_all_sectors(self) -> List[SectorPayload]:
        """
        Lấy danh sách tất cả các nhóm ngành.
        """
        print("Service: Getting all sectors...")
        sector_rows = get_all_sectors(self.db) # Giả sử đã tạo file metadata_crud.py
        
        # Chuyển đổi kết quả thô thành danh sách các đối tượng Pydantic
        return [SectorPayload(**row) for row in sector_rows]
    