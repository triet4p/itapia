# common/dblib/schemas/news.py
"""News data schemas for ITAPIA."""

from typing import List

from pydantic import BaseModel, Field

from .metadata import TickerMetadata


class RelevantNewsPoint(BaseModel):
    """A single relevant news item."""

    news_uuid: str
    title: str
    summary: str | None = None
    provider: str | None = None
    link: str | None = None
    publish_ts: int | None = None
    collect_ts: int

    class Config:
        from_attributes = True


class RelevantNews(BaseModel):
    """Relevant news for a specific ticker."""

    metadata: TickerMetadata = Field(..., description="Metadata of a ticker")
    datas: List[RelevantNewsPoint] = Field(..., description="News items")


class UniversalNewsPoint(RelevantNewsPoint):
    """A universal news item with additional keyword information."""

    keyword: str
    title_hash: str

    class Config:
        from_attributes = True


class UniversalNews(BaseModel):
    """Universal news collection."""

    datas: List[UniversalNewsPoint] = Field(..., description="Universal news items")
