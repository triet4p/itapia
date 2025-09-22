from typing import List

from itapia_common.schemas.entities.backtest import BACKTEST_GENERATION_STATUS
from pydantic import BaseModel, Field


class BacktestGenerationRequest(BaseModel):
    """Request schema for generating a backtest."""

    ticker: str = Field(..., description="Ticker of the stock to be analyzed")
    backtest_dates_ts: List[int] = Field(
        ..., description="List of dates in unix timestamp format"
    )


class BacktestGenerationCheckResponse(BaseModel):
    """Response schema for checking backtest generation status."""

    job_id: str = Field(..., description="Id of the backtest generation job")
    status: BACKTEST_GENERATION_STATUS = Field(
        ..., description="Status of the backtest generation"
    )
