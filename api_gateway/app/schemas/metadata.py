# schemas/metadata.py
from typing import Literal
from pydantic import BaseModel

class TickerMetadata(BaseModel):
    ticker: str
    company_name: str|None = None
    exchange_code: str
    currency: str
    timezone: str
    sector_name: str
    data_type: Literal['daily', 'intraday', 'news']
    
    class Config:
        from_attributes = True
        
class SectorPayload(BaseModel):
    sector_code: str
    sector_name: str
    
    class Config:
        from_attributes = True