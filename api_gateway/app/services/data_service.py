from fastapi import HTTPException
from sqlalchemy.orm import Session
from redis.client import Redis
from typing import List

from app.crud.metadata import get_metadata
from app.crud.prices import get_daily_prices, get_intraday_prices, get_latest_intraday_price
from app.crud.news import get_news

from app.schemas.metadata import TickerMetadata
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
        
    