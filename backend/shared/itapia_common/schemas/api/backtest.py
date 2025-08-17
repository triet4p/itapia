from pydantic import BaseModel, Field
from typing import List
from itapia_common.schemas.entities.backtest import BACKTEST_GENERATION_STATUS

class BacktestGenerationRequest(BaseModel):
    ticker: str = Field(..., description="Ticker of the stock to be analyzed")
    backtest_dates_ts: List[int] = Field(..., description="List of dates in unix timestamp format")
    
class BacktestGenerationCheckResponse(BaseModel):
    job_id: str = Field(..., description="Id of the backtest generation job")
    status: BACKTEST_GENERATION_STATUS = Field(..., description="Status of the backtest generation")
    