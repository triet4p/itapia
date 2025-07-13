# api/v1/endpoints/data_viewer.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from redis.client import Redis

from app import crud, schemas
from app.db.session import get_db, get_redis

router = APIRouter()

@router.get("/prices/daily/{ticker}", response_model=schemas.prices.PriceFullPayload | None)
def read_history_prices(ticker: str, skip: int = 0, limit: int = 500, db: Session = Depends(get_db)):
    metadata_cache = crud.prices.get_metadata(db)
    ticker_info = metadata_cache.get(ticker.upper())
    if not ticker_info:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found.")
    ticker_info['data_type'] = 'daily'
    ticker_info['ticker'] = ticker.upper()
    prices = crud.prices.get_history_prices(db, ticker.upper(), skip, limit)
    
    payload = schemas.prices.PriceFullPayload(
        metadata=schemas.metadata.TickerMetadata(**ticker_info),
        datas=[schemas.prices.PriceDataPoint(timestamp=int(row['collect_date'].timestamp()), **row) for row in prices]
    )
    
    return payload

@router.get("/prices/intraday/last/{ticker}", response_model=schemas.prices.PriceFullPayload | None)
def read_intraday_prices(ticker: str, conn: Redis = Depends(get_redis), db: Session = Depends(get_db)):
    metadata_cache = crud.prices.get_metadata(db)
    ticker_info = metadata_cache.get(ticker.upper())
    if not ticker_info:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found.")
    ticker_info['data_type'] = 'intraday'
    ticker_info['ticker'] = ticker.upper()
    price = crud.prices.get_latest_intraday_price(conn, ticker=ticker.upper())
    if not price:
        raise HTTPException(status_code=404, detail="Intraday price not found for this ticker")
    
    payload = schemas.prices.PriceFullPayload(
        metadata=schemas.metadata.TickerMetadata(**ticker_info),
        datas=[schemas.prices.PriceDataPoint(timestamp=int(price['last_update_utc'].timestamp()), **price)]
    )
    
    return payload

@router.get("/prices/intraday/history/{ticker}", response_model=schemas.prices.PriceFullPayload | None)
def read_intraday_prices(ticker: str, conn: Redis = Depends(get_redis), db: Session = Depends(get_db)):
    metadata_cache = crud.prices.get_metadata(db)
    ticker_info = metadata_cache.get(ticker.upper())
    if not ticker_info:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found.")
    ticker_info['data_type'] = 'intraday'
    ticker_info['ticker'] = ticker.upper()
    prices = crud.prices.get_intraday_prices(conn, ticker=ticker.upper())
    if not prices:
        raise HTTPException(status_code=404, detail="Intraday price not found for this ticker")
    
    payload = schemas.prices.PriceFullPayload(
        metadata=schemas.metadata.TickerMetadata(**ticker_info),
        datas=[schemas.prices.PriceDataPoint(timestamp=int(price['last_update_utc'].timestamp()), **price) for price in prices]
    )
    
    return payload

@router.get("/news/{ticker}", response_model=schemas.news.NewsFullPayload | None)
def read_news(ticker: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Lấy các tin tức gần đây cho một cổ phiếu."""
    metadata_cache = crud.prices.get_metadata(db)
    ticker_info = metadata_cache.get(ticker.upper())
    if not ticker_info:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found.")
    ticker_info['data_type'] = 'news'
    ticker_info['ticker'] = ticker.upper()
    
    news = crud.news.get_news(db, ticker=ticker.upper(), skip=skip, limit=limit)
    payload = schemas.news.NewsFullPayload(
        metadata=schemas.metadata.TickerMetadata(**ticker_info),
        datas=[schemas.news.NewsPoint(collect_ts=int(row['collect_time'].timestamp()),
                                      publish_ts=int(row['publish_time'].timestamp()) if row['publish_time'] else -1,
                                      **row)
               for row in news]
    )
    return payload