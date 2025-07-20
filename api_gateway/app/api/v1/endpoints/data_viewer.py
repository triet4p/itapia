# api/v1/endpoints/data_viewer.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from redis.client import Redis

from itapia_common.dblib.session import get_rdbms_session, get_redis_connection

from itapia_common.dblib.schemas.prices import PriceFullPayload
from itapia_common.dblib.schemas.news import RelevantNewsFullPayload
from itapia_common.dblib.schemas.metadata import SectorMetadata

from itapia_common.dblib.services import APIMetadataService, APINewsService, APIPricesService

def get_metadata_service(rdbms_session: Session = Depends(get_rdbms_session)) -> APIMetadataService:
    return APIMetadataService(rdbms_session)

def get_prices_service(rdbms_session: Session = Depends(get_rdbms_session),
                       redis_client: Redis = Depends(get_redis_connection),
                       metadata_service: APIMetadataService = Depends(get_metadata_service)):
    return APIPricesService(rdbms_session, redis_client, metadata_service)

def get_news_service(rdbms_session: Session = Depends(get_rdbms_session),
                     metadata_service: APIMetadataService = Depends(get_metadata_service)):
    return APINewsService(rdbms_session, metadata_service)

router = APIRouter()

@router.get("/prices/daily/{ticker}", response_model=PriceFullPayload | None, tags=['Prices'])
def get_daily_prices(ticker: str, skip: int = 0, limit: int = 500, 
                     prices_service: APIPricesService = Depends(get_prices_service)):
    """API endpoint để lấy dữ liệu giá lịch sử hàng ngày cho một mã cổ phiếu."""
    return prices_service.get_daily_prices(ticker, skip, limit)

@router.get("/prices/sector/daily/{sector}", response_model=list[PriceFullPayload], tags=['Prices'])
def get_daily_prices_by_sector(sector: str, skip: int = 0, limit: int = 2000,
                               prices_service: APIPricesService = Depends(get_prices_service)):
    """API endpoint để lấy dữ liệu giá hàng ngày cho tất cả các cổ phiếu trong một nhóm ngành."""
    return prices_service.get_daily_prices_by_sector(sector, skip, limit)
    
@router.get("/prices/intraday/last/{ticker}", response_model=PriceFullPayload | None, tags=['Prices'])
def get_intraday_last_prices(ticker: str, 
                             prices_service: APIPricesService = Depends(get_prices_service)):
    """API endpoint để lấy điểm dữ liệu giá trong ngày gần nhất của một cổ phiếu."""
    return prices_service.get_intraday_prices(ticker, latest_only=True)

@router.get("/prices/intraday/history/{ticker}", response_model=PriceFullPayload | None, tags=['Prices'])
def get_intraday_history_prices(ticker: str, 
                                prices_service: APIPricesService = Depends(get_prices_service)):
    """API endpoint để lấy toàn bộ lịch sử giá trong ngày (giới hạn bởi stream) của một cổ phiếu."""
    return prices_service.get_intraday_prices(ticker, latest_only=False)

@router.get("/news/relevants/{ticker}", response_model=RelevantNewsFullPayload | None, tags=['News'])
def get_relevant_news(ticker: str, skip: int = 0, limit: int = 10,
             news_service: APINewsService = Depends(get_news_service)):
    """API endpoint để lấy danh sách các tin tức gần đây cho một mã cổ phiếu."""
    return news_service.get_relevant_news(ticker, skip, limit)

@router.get("/metadata/sectors", response_model=list[SectorMetadata], tags=['Metadata'])
def get_all_sectors(metadata_service: APIMetadataService = Depends(get_metadata_service)):
    """API endpoint để lấy danh sách tất cả các nhóm ngành được hỗ trợ."""
    return metadata_service.get_all_sectors()