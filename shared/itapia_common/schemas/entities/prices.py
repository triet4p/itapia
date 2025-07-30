# common/dblib/schemas/prices.py

from pydantic import BaseModel, Field
from typing import List

from .metadata import TickerMetadata

class PriceDataPoint(BaseModel):
    open: float|None = None
    high: float|None = None
    low: float|None = None
    close: float|None = None
    volume: int|None = None
    timestamp: int = Field(..., description="Unix timestamp (seconds) for the start of the day (UTC).")
    
    class Config:
        from_attributes = True
    
        
class Price(BaseModel):
    metadata: TickerMetadata = Field(..., description='metadata of a ticker')
    datas: List[PriceDataPoint] = Field(..., description='daily data or intraday data')
