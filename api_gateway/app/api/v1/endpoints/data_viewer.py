# api/v1/endpoints/data_viewer.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from redis.client import Redis

from app.db.session import get_db, get_redis
from app.services.data_service import DataService

from app.schemas.prices import PriceFullPayload
from app.schemas.news import NewsFullPayload

router = APIRouter()

def get_data_service(db: Session = Depends(get_db), redis_conn: Redis = Depends(get_redis)) -> DataService:
    return DataService(db=db, redis_conn=redis_conn)

@router.get("/prices/daily/{ticker}", response_model=PriceFullPayload | None)
def get_daily_prices(ticker: str, skip: int = 0, limit: int = 500, 
                     data_service: DataService = Depends(get_data_service)):
    return data_service.get_daily_prices_payload(ticker, skip, limit)
    

@router.get("/prices/intraday/last/{ticker}", response_model=PriceFullPayload | None)
def get_intraday_prices(ticker: str, data_service: DataService = Depends(get_data_service)):
    return data_service.get_intraday_prices_payload(ticker, latest_only=False)

@router.get("/prices/intraday/history/{ticker}", response_model=PriceFullPayload | None)
def get_intraday_prices(ticker: str, data_service: DataService = Depends(get_data_service)):
    return data_service.get_intraday_prices_payload(ticker, latest_only=True)


@router.get("/news/{ticker}", response_model=NewsFullPayload | None)
def get_news(ticker: str, skip: int = 0, limit: int = 10,
             data_service: DataService = Depends(get_data_service)):
    """Lấy các tin tức gần đây cho một cổ phiếu."""
    return data_service.get_news_payload(ticker, skip, limit)