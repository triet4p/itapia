from pydantic import BaseModel
from datetime import datetime

class News(BaseModel):
    news_uuid: str
    ticker: str
    title: str
    summary: str|None = None
    provider: str|None = None
    link: str|None = None
    content_type: str|None = None
    publish_time: datetime|None = None
    collect_time: datetime