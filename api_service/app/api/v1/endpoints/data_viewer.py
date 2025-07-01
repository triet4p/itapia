from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from redis.client import Redis

from app import crud, schemas
from app.db.session import get_db, get_redis

router = APIRouter()

@router.get("/prices/history/{ticker}", response_model=list[schemas.HistoryPrice])
def read_history_prices(ticker: str, skip: int = 0, limit: int = 500, db: Session = Depends(get_db)):
    prices = crud.get_history_prices(db, ticker.upper(), skip, limit)
    return prices

@router.get("/prices/intraday/{ticker}", response_model=list[schemas.IntradayPrice])
def read_intraday_prices(ticker: str, conn: Redis = Depends(get_redis)):
    price = crud.get_intraday_prices(conn, ticker=ticker.upper())
    if not price:
        raise HTTPException(status_code=404, detail="Intraday price not found for this ticker")
    return price

@router.get("/news/{ticker}", response_model=list[schemas.News])
def read_news(ticker: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Lấy các tin tức gần đây cho một cổ phiếu."""
    news = crud.get_news(db, ticker=ticker.upper(), skip=skip, limit=limit)
    return news