from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal

# --- CÁC SCHEMA NGUYÊN THỦY CHO GIẢI THÍCH ---

class TopFeature(BaseModel):
    feature: str = Field(..., description="Name of related features")
    value: float = Field(..., description="Real value of feature at forecasting time")
    contribution: float = Field(..., description="SHAP value, indicating the magnitude and direction of the influence.")
    effect: Literal["positive", "negative"] = Field(..., description="Direction of effect")

class BaseSHAPExplaination(BaseModel):
    base_value: float = Field(..., description="Average predicted value (normalized log-odds or percent).")
    prediction_outcome: float = Field(..., description="Final forecast result after adding all contributions.")
    top_features: List[TopFeature] = Field(..., description="List of most influential features.")
    
class SHAPExplaination(BaseModel):
    for_target: str = Field(..., description='Name of target')
    explaination: BaseSHAPExplaination = Field(..., description='Explaination for this target')

# --- SCHEMA CHO KẾT QUẢ CỦA MỘT TASK DUY NHẤT ---

class SingleTaskForecastReport(BaseModel):
    task_name: str = Field(..., description="Identify of task")
    task_metadata: Dict[str, Any] = Field(..., description="Metadata of task.")
    prediction: List[float] = Field(..., description="Model forecast results (in percent form multiplied by 100).")
    units: Literal["percent", "category"] = Field(..., description="Units of prediction")
    evidence: List[SHAPExplaination] = Field(..., description="Evidence by SHAP")

# --- SCHEMA TỔNG HỢP CHO TOÀN BỘ FORECASTING MODULE ---

class ForecastingReport(BaseModel):
    ticker: str = Field(..., description="Ticker symbol for forecasting")
    sector: str = Field(..., description="Sector of ticker")
    generated_at: str = Field(..., description="Time generated in ISO Format")
    generated_timestamp: int = Field(..., description="Time generated in timestamp")
    forecasts: List[SingleTaskForecastReport] = Field(..., description="List of forecasting each single task")