# common/dblib/schemas/prices.py
"""Price data schemas for ITAPIA."""

from typing import List

from pydantic import BaseModel, Field

from .metadata import TickerMetadata


class PriceDataPoint(BaseModel):
    """A single price data point."""

    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None
    timestamp: int = Field(
        ..., description="Unix timestamp (seconds) for the start of the day (UTC)."
    )

    class Config:
        from_attributes = True


class Price(BaseModel):
    """Price data for a ticker."""

    metadata: TickerMetadata = Field(..., description="Metadata of a ticker")
    datas: List[PriceDataPoint] = Field(..., description="Daily data or intraday data")
