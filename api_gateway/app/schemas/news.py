# app/schemas/news.py

from typing import List
from pydantic import BaseModel, Field

from app.schemas.metadata import TickerMetadata

class NewsPoint(BaseModel):
    news_uuid: str
    title: str
    summary: str|None = None
    provider: str|None = None
    link: str|None = None
    publish_ts: int|None = None
    collect_ts: int
    class Config:
        from_attributes = True
    
class NewsFullPayload(BaseModel):
    metadata: TickerMetadata = Field(..., description='metadata of a ticker')
    datas: List[NewsPoint] = Field(..., description='news')