# api/v1/endpoints/data_viewer.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from redis.client import Redis

from app.db.session import get_db, get_redis
from app.services.data_service import DataService

from app.schemas.prices import PriceFullPayload
from app.schemas.news import NewsFullPayload
from app.schemas.metadata import SectorPayload

router = APIRouter()

def get_data_service(db: Session = Depends(get_db), redis_conn: Redis = Depends(get_redis)) -> DataService:
    return DataService(db=db, redis_conn=redis_conn)

@router.get("/prices/daily/{ticker}", response_model=PriceFullPayload | None, tags=['Prices'])
def get_daily_prices(ticker: str, skip: int = 0, limit: int = 500, 
                     data_service: DataService = Depends(get_data_service)):
    """API endpoint để lấy dữ liệu giá lịch sử hàng ngày cho một mã cổ phiếu."""
    return data_service.get_daily_prices_payload(ticker, skip, limit)
    
@router.get("/prices/intraday/last/{ticker}", response_model=PriceFullPayload | None, tags=['Prices'])
def get_intraday_prices(ticker: str, data_service: DataService = Depends(get_data_service)):
    """API endpoint để lấy điểm dữ liệu giá trong ngày gần nhất của một cổ phiếu."""
    return data_service.get_intraday_prices_payload(ticker, latest_only=False)

@router.get("/prices/intraday/history/{ticker}", response_model=PriceFullPayload | None, tags=['Prices'])
def get_intraday_prices(ticker: str, data_service: DataService = Depends(get_data_service)):
    """API endpoint để lấy toàn bộ lịch sử giá trong ngày (giới hạn bởi stream) của một cổ phiếu."""
    return data_service.get_intraday_prices_payload(ticker, latest_only=True)

@router.get("/news/{ticker}", response_model=NewsFullPayload | None, tags=['News'])
def get_news(ticker: str, skip: int = 0, limit: int = 10,
             data_service: DataService = Depends(get_data_service)):
    """API endpoint để lấy danh sách các tin tức gần đây cho một mã cổ phiếu."""
    return data_service.get_news_payload(ticker, skip, limit)

@router.get("/prices/sector/daily/{sector}", response_model=list[PriceFullPayload], tags=['Prices'])
def get_daily_prices_by_sector(sector: str, skip: int = 0, limit: int = 2000,
                               data_service: DataService = Depends(get_data_service)):
    """API endpoint để lấy dữ liệu giá hàng ngày cho tất cả các cổ phiếu trong một nhóm ngành."""
    return data_service.get_daily_prices_payload_by_sector(sector, skip, limit)

@router.get("/metadata/sectors", response_model=list[SectorPayload], tags=['Metadata'])
def get_all_sectors(data_service: DataService = Depends(get_data_service)):
    """API endpoint để lấy danh sách tất cả các nhóm ngành được hỗ trợ."""
    return data_service.get_all_sectors()