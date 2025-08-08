# api/v1/endpoints/data_viewer.py
from fastapi import APIRouter, Depends, HTTPException

from itapia_common.dblib.dependencies import get_metadata_service, get_news_service, get_prices_service

from itapia_common.schemas.api.prices import PriceResponse
from itapia_common.schemas.api.news import RelevantNewsResponse, UniversalNewsResponse
from itapia_common.schemas.api.metadata import SectorMetadataResponse

from itapia_common.dblib.services import APIMetadataService, APINewsService, APIPricesService

router = APIRouter()

@router.get("/market/tickers/{ticker}/prices/daily", response_model=PriceResponse, tags=['Market Prices'])
def get_daily_prices(ticker: str, skip: int = 0, limit: int = 500, 
                     prices_service: APIPricesService = Depends(get_prices_service)):
    """API endpoint để lấy dữ liệu giá lịch sử hàng ngày cho một mã cổ phiếu."""
    try:
        res = prices_service.get_daily_prices(ticker, skip, limit)
        return PriceResponse.model_validate(res.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f'Not found metadata for {ticker}')
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown error occured in server')

@router.get("/market/sectors/{sector}/prices/daily", response_model=list[PriceResponse], tags=['Market Prices'])
def get_daily_prices_by_sector(sector: str, skip: int = 0, limit: int = 2000,
                               prices_service: APIPricesService = Depends(get_prices_service)):
    """API endpoint để lấy dữ liệu giá hàng ngày cho tất cả các cổ phiếu trong một nhóm ngành."""
    try:
        ress = prices_service.get_daily_prices_by_sector(sector, skip, limit)
        return [PriceResponse.model_validate(res.model_dump()) for res in ress]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f'Not found metadata for {sector}')
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown error occured in server')


@router.get("/market/tickers/{ticker}/prices/intraday", response_model=PriceResponse, tags=['Market Prices'])
def get_intraday_prices(ticker: str, 
                        prices_service: APIPricesService = Depends(get_prices_service),
                        latest_only: bool = False):
    """API endpoint để lấy toàn bộ lịch sử giá trong ngày (giới hạn bởi stream) của một cổ phiếu."""
    try:
        res = prices_service.get_intraday_prices(ticker, latest_only=latest_only)
        return PriceResponse.model_validate(res.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f'Not found metadata for {ticker}')
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown error occured in server')

@router.get("/market/tickers/{ticker}/news", response_model=RelevantNewsResponse, tags=['Market News'])
def get_relevant_news(ticker: str, skip: int = 0, limit: int = 10,
             news_service: APINewsService = Depends(get_news_service)):
    """API endpoint để lấy danh sách các tin tức gần đây cho một mã cổ phiếu."""
    try:
        res = news_service.get_relevant_news(ticker, skip, limit)
        return RelevantNewsResponse.model_validate(res.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f'Not found metadata for {ticker}')
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown error occured in server')

@router.get("/market/news/universal", response_model=UniversalNewsResponse, tags=['Market News'])
def get_universal_news(search_terms: str, skip: int = 0, limit: int = 10,
             news_service: APINewsService = Depends(get_news_service)):
    """API endpoint để lấy danh sách các tin tức gần đây cho một mã cổ phiếu."""
    try:
        res = news_service.get_universal_news(search_terms, skip, limit)
        return UniversalNewsResponse.model_validate(res.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown error occured in server')

@router.get("/metadata/sectors", response_model=list[SectorMetadataResponse], tags=['Metadata'])
def get_all_sectors(metadata_service: APIMetadataService = Depends(get_metadata_service)):
    """API endpoint để lấy danh sách tất cả các nhóm ngành được hỗ trợ."""
    try:
        ress = metadata_service.get_all_sectors()
        return [SectorMetadataResponse.model_validate(x.model_dump()) for x in ress]
    except Exception as e:
        raise HTTPException(status_code=500, detail='Unknown error occured in server')