from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Union

# --- PRIMITIVE SCHEMAS FOR EXPLANATION ---

class TopFeature(BaseModel):
    """Top feature information for SHAP explanation."""
    
    feature: str = Field(..., description="Name of related features")
    value: float = Field(..., description="Real value of feature at forecasting time")
    contribution: float = Field(..., description="SHAP value, indicating the magnitude and direction of the influence.")
    effect: Literal["positive", "negative"] = Field(..., description="Direction of effect")

class BaseSHAPExplaination(BaseModel):
    """Base SHAP explanation schema."""
    
    base_value: float = Field(..., description="Average predicted value (normalized log-odds or percent).")
    prediction_outcome: float = Field(..., description="Final forecast result after adding all contributions.")
    top_features: List[TopFeature] = Field(..., description="List of most influential features.")
    
class SHAPExplaination(BaseModel):
    """SHAP explanation for a specific target."""
    
    for_target: str = Field(..., description="Name of target")
    explaination: BaseSHAPExplaination = Field(..., description="Explanation for this target")

# --- SCHEMA FOR A SINGLE TASK RESULT ---

class _BaseTaskMetadata(BaseModel):
    """Base metadata for forecasting tasks."""
    
    problem_id: Literal['triple-barrier', 'ndays-distribution'] = Field(..., description="To discriminate each metadata type")
    targets: List[str] = Field(..., description="Targets of task, need to plain, example target_tb_15d_2tp_1sl")
    units: str = Field(..., description="Units of target")
    
class TripleBarrierTaskMetadata(_BaseTaskMetadata):
    """Metadata for triple barrier task."""
    
    horizon: int = Field(..., description="Horizon to meet timeout")
    tp_pct: float = Field(..., description="TP percent to win, example 0.02 is meaning 1.02 multiplier of current price")
    sl_pct: float = Field(..., description="SL percent to loss, example 0.02 is 0.98 multiplier of current price")
    problem_id: Literal['triple-barrier'] = 'triple-barrier'
    
class NDaysDistributionTaskMetadata(_BaseTaskMetadata):
    """Metadata for N-days distribution task."""
    
    horizon: int = Field(..., description="Window for look for distribution (mean/std/min/max/q25/q75)")
    problem_id: Literal['ndays-distribution'] = 'ndays-distribution'

class SingleTaskForecastReport(BaseModel):
    """Forecast report for a single task."""
    
    task_name: str = Field(..., description="Identifier of task")
    task_metadata: Union[TripleBarrierTaskMetadata, NDaysDistributionTaskMetadata] = Field(..., discriminator='problem_id', description="Metadata of task.")
    prediction: List[float] = Field(..., description="Model forecast results (in percent form multiplied by 100).")
    units: Literal["percent", "category"] = Field(..., description="Units of prediction")
    evidence: List[SHAPExplaination] = Field(..., description="Evidence by SHAP")

# --- CONSOLIDATED SCHEMA FOR ENTIRE FORECASTING MODULE ---

class ForecastingReport(BaseModel):
    """Complete forecasting report for a ticker."""
    
    ticker: str = Field(..., description="Ticker symbol for forecasting")
    sector: str = Field(..., description="Sector of ticker")
    forecasts: List[SingleTaskForecastReport] = Field(..., description="List of forecasting each single task")