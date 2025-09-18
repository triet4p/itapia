from pydantic import BaseModel, Field
from typing import Literal

ACTION_TYPE = Literal['BUY', 'SELL', 'HOLD']

class Action(BaseModel):
    action_type: ACTION_TYPE
    # Percentage of capital to use for this action
    position_size_pct: float = Field(default=1.0, description='Percentage of capital to use for this action')
    # Hold time if no other exit signal
    duration_days: int = Field(default=365, description="Hold time if no other exit signal")
    
    sl_pct: float = 1.0
    tp_pct: float = 1.0