from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any, Optional

class _BaseTrendReport(BaseModel):
    ma_direction: Literal['uptrend', 'downtrend', 'undefined'] = Field(..., description='Direction using MA indicators')
    ma_status: Literal['positive', 'negative', 'undefined'] = Field(..., description='Status using MA indicators and latest close price')
    evidence: Dict[str, Any] = Field(..., description='A dictionary describe evidence of trend analysis')
    
    class Config:
        from_attributes = True
    
class MidTermTrendReport(_BaseTrendReport):
    adx_direction: Literal['uptrend', 'downtrend', 'undefined'] = Field(..., description='Direction using MA indicators')
    
class LongTermTrendReport(_BaseTrendReport):
    # Totally Inheritance
    pass

class OverallStrengthTrendReport(BaseModel):
    strength: Literal['strong', 'moderate', 'weak', 'undefined'] = Field(..., description='Overall strength of trend')
    value: int|float = Field(..., description='Value of overall strength')
    
    class Config:
        from_attributes = True

class TrendReport(BaseModel):
    primary_focus: Literal['mid-term', 'long-term'] = Field(default='mid_term', description='Primary focus of analysis')
    midterm_report: MidTermTrendReport = Field(..., description='Mid-Term Trend Report')
    longterm_report: LongTermTrendReport = Field(..., description='Long-Term Trend Report')
    overall_strength: OverallStrengthTrendReport = Field(..., description='Overall strength')
    
    class Config:
        from_attributes = True

class SRIdentifyLevelObj(BaseModel):
    level: float = Field(..., description='Level Value of supportance/resitance identify')
    source: str = Field(..., description='Source of the Level Value of supportance/resitance identify')
    
    class Config:
        from_attributes = True
        
class SRReport(BaseModel):
    history_window: int = Field(90, description='History window for identify level')
    supports: List[SRIdentifyLevelObj] = Field(..., description='Support points')
    resistances: List[SRIdentifyLevelObj] = Field(..., description='Resistance points')
    
    class Config:
        from_attributes = True
        
class PatternObj(BaseModel):
    name: str = Field(..., description="Friendly name of patterns")
    pattern_type: Literal['chart', 'candlestick'] = Field(..., description='Identify that this is chart patterns or candlestick patterns')
    sentiment: Literal['bull', 'bear', 'neutral'] = Field(..., description='Identify the meaning of patterns is BULL or BEAR')
    score: int|float = Field(..., description='Score each pattern rewarded')
    confirmation_date: str = Field(..., description="ISO Format string to describe confimation date of this pattern")
    evidence: Dict[str, Any] = Field(..., description='A dictionary describe evidence of a recognized pattern')
    
    class Config:
        from_attributes = True

class PatternReport(BaseModel):
    history_window: int = Field(default=90, description='History window to view data')
    prominence_pct: float = Field(default=0.015, description='Prominence percents to find peaks')
    distance: int = Field(default=5, description='Distance of neighbor points to find peaks')
    lookback_period: int = Field(default=5, description='Lookback period for candlestick patterns')
    num_top_patterns: int = Field(default=4, description='Number of top patterns to recognize')
    top_patterns: List[PatternObj] = Field(..., description='Top patterns recongized')
    
    class Config:
        from_attributes = True
    
class KeyIndicators(BaseModel):
    sma_20: Optional[float]
    sma_50: Optional[float]
    sma_200: Optional[float] 
    rsi_14: Optional[float] 
    adx_14: Optional[float] 
    dmp_14: Optional[float]
    dmn_14: Optional[float]
    bbu_20: Optional[float]
    bbl_20: Optional[float]
    atr_14: Optional[float]
    psar: Optional[float]
    
    class Config:
        from_attributes = True
    
class DailyAnalysisReport(BaseModel):
    key_indicators: KeyIndicators = Field(..., description='Some important key indicators to mid-term and long-term')
    trend_report: TrendReport = Field(..., description='Trend report')
    sr_report: SRReport = Field(..., description='Support/Resistance report')
    pattern_report: PatternReport = Field(..., description='Pattern Report')
    
    class Config:
        from_attributes = True