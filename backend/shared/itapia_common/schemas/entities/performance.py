from typing import Dict, Literal, Optional, Tuple
from pydantic import BaseModel, Field

class PerformanceMetrics(BaseModel):
    """Performance metrics for trading strategies."""
    
    num_trades: int = Field(default=0)
    total_return_pct: float = Field(default=0.0)
    max_drawdown_pct: float = Field(default=0.0)
    win_rate_pct: float = Field(default=0.0)
    profit_factor: float = Field(default=0.0)
    sharpe_ratio: float = Field(default=0.0)
    sortino_ratio: float = Field(default=0.0)
    annual_return_stability: float = Field(default=0.0)
    cagr: float = Field(default=0.0)
    
class NormalizedPerformanceMetrics(BaseModel):
    """Normalized performance metrics scaled to 0-1 range."""
    
    num_trades: float = Field(default=0.0)
    total_return_pct: float = Field(default=0.0)
    max_drawdown_pct: float = Field(default=0.0)
    win_rate_pct: float = Field(default=0.0)
    profit_factor: float = Field(default=0.0)
    sharpe_ratio: float = Field(default=0.0)
    sortino_ratio: float = Field(default=0.0)
    annual_return_stability: float = Field(default=0.0)
    cagr: float = Field(default=0.0)
    
class PerformanceFilterWeights(BaseModel):
    """Weights for performance metrics used in filtering."""
    
    num_trades: float = Field(default=0.0)
    total_return_pct: float = Field(default=0.0)
    max_drawdown_pct: float = Field(default=0.0)
    win_rate_pct: float = Field(default=0.0)
    profit_factor: float = Field(default=0.0)
    sharpe_ratio: float = Field(default=0.0)
    sortino_ratio: float = Field(default=0.0)
    annual_return_stability: float = Field(default=0.0)
    cagr: float = Field(default=0.0)
    
class PerformanceHardConstraints(BaseModel):
    """Hard constraints for performance metrics."""
    
    num_trades: Tuple[Optional[float], Optional[float]] = Field(default=(None, None))
    total_return_pct: Tuple[Optional[float], Optional[float]] = Field(default=(None, None))
    max_drawdown_pct: Tuple[Optional[float], Optional[float]] = Field(default=(None, None))
    win_rate_pct: Tuple[Optional[float], Optional[float]] = Field(default=(None, None))
    profit_factor: Tuple[Optional[float], Optional[float]] = Field(default=(None, None))
    sharpe_ratio: Tuple[Optional[float], Optional[float]] = Field(default=(None, None))
    sortino_ratio: Tuple[Optional[float], Optional[float]] = Field(default=(None, None))
    annual_return_stability: Tuple[Optional[float], Optional[float]] = Field(default=(None, None))
    cagr: Tuple[Optional[float], Optional[float]] = Field(default=(None, None))
    
# Define a type for the "direction" of a metric
MetricDirection = Literal["higher_is_better", "lower_is_better"]

# --- NORMALIZATION CONFIGURATION DICTIONARY ---
# This contains all the "knowledge" about how to normalize metrics
NORMALIZATION_CONFIG: Dict[str, Dict] = {
    "cagr": {
        "worst": -0.20,
        "best": 0.30,
        "direction": "higher_is_better"
    },
    "sortino_ratio": {
        "worst": 0.0,
        "best": 3.0,
        "direction": "higher_is_better"
    },
    "max_drawdown_pct": {
        "worst": 0.40, # 40% drawdown
        "best": 0.05,  # 5% drawdown
        "direction": "lower_is_better" # <-- Important
    },
    "annual_return_stability": {
        "worst": 1.0, # std = 1.0 (very volatile)
        "best": 0.1,  # std = 0.1 (very stable)
        "direction": "lower_is_better" # <-- Important
    },
    "profit_factor": {
        "worst": 1.0,
        "best": 3.0,
        "direction": "higher_is_better"
    },
    "win_rate_pct": {
        "worst": 0.40, # 40%
        "best": 0.65, # 65%
        "direction": "higher_is_better"
    },
    "num_trades": {
        "worst": 10,
        "best": 100,
        "direction": "higher_is_better"
    }
    # Add other metrics here if needed
}
