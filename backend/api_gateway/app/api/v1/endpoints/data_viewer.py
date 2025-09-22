# api/v1/endpoints/data_viewer.py
"""Data viewer endpoints for accessing market data."""

from fastapi import APIRouter, Depends, HTTPException
from itapia_common.dblib.dependencies import (
    get_metadata_service,
    get_news_service,
    get_prices_service,
)
from itapia_common.dblib.services import (
    APIMetadataService,
    APINewsService,
    APIPricesService,
)
from itapia_common.schemas.api.metadata import SectorMetadataResponse
from itapia_common.schemas.api.news import RelevantNewsResponse, UniversalNewsResponse
from itapia_common.schemas.api.prices import PriceResponse

router = APIRouter()


@router.get(
    "/market/tickers/{ticker}/prices/daily",
    response_model=PriceResponse,
    tags=["Market Prices"],
    summary="Get daily historical price data for a stock ticker",
)
def get_daily_prices(
    ticker: str,
    skip: int = 0,
    limit: int = 500,
    prices_service: APIPricesService = Depends(get_prices_service),
):
    """Get daily historical price data for a stock ticker.

    Args:
        ticker (str): Stock ticker symbol
        skip (int): Number of records to skip (for pagination)
        limit (int): Maximum number of records to return
        prices_service (APIPricesService): Prices service dependency

    Returns:
        PriceResponse: Daily historical price data
    """
    try:
        res = prices_service.get_daily_prices(ticker, skip, limit)
        return PriceResponse.model_validate(res.model_dump())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Not found metadata for {ticker}")
    except Exception:
        raise HTTPException(status_code=500, detail="Unknown error occured in server")


@router.get(
    "/market/sectors/{sector}/prices/daily",
    response_model=list[PriceResponse],
    tags=["Market Prices"],
    summary="Get daily price data for all stocks in a sector",
)
def get_daily_prices_by_sector(
    sector: str,
    skip: int = 0,
    limit: int = 2000,
    prices_service: APIPricesService = Depends(get_prices_service),
):
    """Get daily price data for all stocks in a sector.

    Args:
        sector (str): Sector name
        skip (int): Number of records to skip (for pagination)
        limit (int): Maximum number of records to return
        prices_service (APIPricesService): Prices service dependency

    Returns:
        list[PriceResponse]: Daily price data for all stocks in the sector
    """
    try:
        ress = prices_service.get_daily_prices_by_sector(sector, skip, limit)
        return [PriceResponse.model_validate(res.model_dump()) for res in ress]
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Not found metadata for {sector}")
    except Exception:
        raise HTTPException(status_code=500, detail="Unknown error occured in server")


@router.get(
    "/market/tickers/{ticker}/prices/intraday",
    response_model=PriceResponse,
    tags=["Market Prices"],
    summary="Get intraday price history for a stock ticker",
)
def get_intraday_prices(
    ticker: str,
    prices_service: APIPricesService = Depends(get_prices_service),
    latest_only: bool = False,
):
    """Get intraday price history for a stock ticker.

    Args:
        ticker (str): Stock ticker symbol
        prices_service (APIPricesService): Prices service dependency
        latest_only (bool): If True, return only the latest intraday data

    Returns:
        PriceResponse: Intraday price history
    """
    try:
        res = prices_service.get_intraday_prices(ticker, latest_only=latest_only)
        return PriceResponse.model_validate(res.model_dump())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Not found metadata for {ticker}")
    except Exception:
        raise HTTPException(status_code=500, detail="Unknown error occured in server")


@router.get(
    "/market/tickers/{ticker}/news",
    response_model=RelevantNewsResponse,
    tags=["Market News"],
    summary="Get recent news for a stock ticker",
)
def get_relevant_news(
    ticker: str,
    skip: int = 0,
    limit: int = 10,
    news_service: APINewsService = Depends(get_news_service),
):
    """Get recent news for a stock ticker.

    Args:
        ticker (str): Stock ticker symbol
        skip (int): Number of records to skip (for pagination)
        limit (int): Maximum number of records to return
        news_service (APINewsService): News service dependency

    Returns:
        RelevantNewsResponse: Recent news for the stock ticker
    """
    try:
        res = news_service.get_relevant_news(ticker, skip, limit)
        return RelevantNewsResponse.model_validate(res.model_dump())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Not found metadata for {ticker}")
    except Exception:
        raise HTTPException(status_code=500, detail="Unknown error occured in server")


@router.get(
    "/market/news/universal",
    response_model=UniversalNewsResponse,
    tags=["Market News"],
    summary="Get recent news based on search terms",
)
def get_universal_news(
    search_terms: str,
    skip: int = 0,
    limit: int = 10,
    news_service: APINewsService = Depends(get_news_service),
):
    """Get recent news based on search terms.

    Args:
        search_terms (str): Search terms to filter news
        skip (int): Number of records to skip (for pagination)
        limit (int): Maximum number of records to return
        news_service (APINewsService): News service dependency

    Returns:
        UniversalNewsResponse: Recent news based on search terms
    """
    try:
        res = news_service.get_universal_news(search_terms, skip, limit)
        return UniversalNewsResponse.model_validate(res.model_dump())
    except Exception:
        raise HTTPException(status_code=500, detail="Unknown error occured in server")


@router.get(
    "/metadata/sectors",
    response_model=list[SectorMetadataResponse],
    tags=["Metadata"],
    summary="Get list of all supported sectors",
)
def get_all_sectors(
    metadata_service: APIMetadataService = Depends(get_metadata_service),
):
    """Get list of all supported sectors.

    Args:
        metadata_service (APIMetadataService): Metadata service dependency

    Returns:
        list[SectorMetadataResponse]: List of all supported sectors
    """
    try:
        ress = metadata_service.get_all_sectors()
        return [SectorMetadataResponse.model_validate(x.model_dump()) for x in ress]
    except Exception:
        raise HTTPException(status_code=500, detail="Unknown error occured in server")
