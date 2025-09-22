# common/dblib/schemas/metadata.py
"""Metadata schemas for ITAPIA."""

from typing import Literal

from pydantic import BaseModel


class TickerMetadata(BaseModel):
    """Metadata for a ticker symbol."""

    ticker: str
    company_name: str | None = None
    exchange_code: str
    currency: str
    timezone: str
    sector_name: str
    data_type: Literal["daily", "intraday", "news"]

    class Config:
        from_attributes = True


class SectorMetadata(BaseModel):
    """Metadata for a sector."""

    sector_code: str
    sector_name: str

    class Config:
        from_attributes = True
