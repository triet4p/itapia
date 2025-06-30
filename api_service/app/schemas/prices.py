from pydantic import BaseModel
from datetime import datetime

class HistoryPrice(BaseModel):
    ticker: str
    open: float|None = None
    high: float|None = None
    low: float|None = None
    close: float|None = None
    volume: int|None = None
    collect_date: datetime
    
    class Config:
        from_attributes = True
    
class IntradayPrice(BaseModel):
    ticker: str
    open: float|None = None
    high: float|None = None
    low: float|None = None
    last_price: float|None = None
    last_volume: float|None = None
    last_update_utc: datetime
    
    class Config:
        from_attributes = True