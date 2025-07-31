from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional

class CurrentStatusReport(BaseModel):
    vwap_status: Literal['above', 'below', 'undefined'] = Field(..., description='Comparison between VWAP-D and current price')
    open_status: Literal['above', 'below'] = Field(..., description='Comparison between current price and open price')
    rsi_status: Literal['overbought', 'oversold', 'neutral'] = Field(..., description="RSI Status")
    evidence: Dict[str, Any] = Field(..., description='A dictionary describe evidence of status analysis')
    
    class Config:
        from_attributes = True
        
class KeyLevelsReport(BaseModel):
    day_high: float
    day_low: float
    open_price: float
    vwap: Optional[float]
    or_30m_high: Optional[float]
    or_30m_low: Optional[float]
    
    class Config:
        from_attributes = True
        
class MomentumReport(BaseModel):
    macd_crossover: Literal['bull', 'bear', 'neutral'] = Field(..., description='Decide relationship of MACD and Signal line')
    volume_status: Literal['normal', 'high-spike'] = Field(..., description='Decide if volume spike ratio > 2.0')
    opening_range_status: Literal['bull-breakout', 'bear-breakdown', 'inside'] = Field(..., description='Opening Range breakout')
    evidence: Dict[str, Any] = Field(..., description='A dictionary describe evidence of momentum analysis')
    
    class Config:
        from_attributes = True

class IntradayAnalysisReport(BaseModel):
    current_status_report: CurrentStatusReport = Field(..., description='Status report')
    momentum_report: MomentumReport = Field(..., description='Momentum report')
    key_levels: KeyLevelsReport = Field(..., description='Some of key levels')
    
    