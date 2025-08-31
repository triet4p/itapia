from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum
from .rules import RuleEntity
from .backtest import BacktestPerformanceMetrics

class EvoRunStatus(str, Enum):
    COMPLETED = "COMPLETED"
    RUNNING = "RUNNING"

class EvoRuleEntity(RuleEntity):
    evo_run_id: str = Field(..., description="Evo Run which is produced this rule")
    metrics: Optional[BacktestPerformanceMetrics]
    
class EvoRunEntity(BaseModel):
    run_id: str = Field(..., description='Running ID of this Evolutionary Run.')
    status: EvoRunStatus = Field(..., description='Status of this run')
    algorithm: str = Field(..., description='Algorithm this run used.')
    config: Dict[str, Any] = Field(..., description="Metadata of this run")
    fallback_state: bytes = Field(..., description="A pickle dump to save any fallback state of this run")
    rules: List[EvoRuleEntity] = Field(..., description="Evo Rule Entities of this run.")