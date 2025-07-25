# common/dblib/schemas/news.py

from typing import List
from pydantic import BaseModel, Field

from itapia_common.dblib.schemas.metadata import TickerMetadata

class RelevantNewsPoint(BaseModel):
    news_uuid: str
    title: str
    summary: str|None = None
    provider: str|None = None
    link: str|None = None
    publish_ts: int|None = None
    collect_ts: int
    class Config:
        from_attributes = True
    
class RelevantNewsFullPayload(BaseModel):
    metadata: TickerMetadata = Field(..., description='metadata of a ticker')
    datas: List[RelevantNewsPoint] = Field(..., description='news')
    
class UniversalNewsPoint(RelevantNewsPoint):
    keyword: str
    title_hash: str
    class Config:
        from_attributes = True
        
class UniversalNewsFullPayload(BaseModel):
    datas: List[UniversalNewsPoint] = Field(..., description='universal news')