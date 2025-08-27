from typing import Literal
from pydantic import BaseModel, Field

BACKTEST_GENERATION_STATUS = Literal['IDLE', 'RUNNING', 'COMPLETED', 'FAILED']

BACKTEST_CONTEXT_STATUS = Literal['IDLE', 'READY_SERVE', 'READY_LOAD', 'PREPARING', 'FAILED']

class BacktestPerformanceMetrics(BaseModel):
    num_trades: int = Field(default=0)
    total_return_pct: float = Field(default=0.0)
    max_drawdown_pct: float = Field(default=0.0)
    win_rate_pct: float = Field(default=0.0)
    profit_factor: float = Field(default=0.0)
    sharpe_ratio: float = Field(default=0.0)
    sortino_ratio: float = Field(default=0.0)
    annual_return_stability: float = Field(default=0.0)