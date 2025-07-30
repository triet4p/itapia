from pydantic import BaseModel, Field
from typing import Optional, Any
from .technical import TechnicalReport
from .forecasting import ForecastingReport
from .news import NewsAnalysisReport

class QuickCheckReport(BaseModel):
    ticker: str = Field(..., description='Symbol of ticker')
    generated_at_utc: str = Field(..., description='ISO format string of generated time')
    generated_timestamp: int = Field(..., description='Timestamp value of generated time')
    technical_report: Optional[TechnicalReport] = Field(..., description='Technical Report')
    forecasting_report: Optional[ForecastingReport] = Field(..., description='Forecasting report')
    news_report: Optional[NewsAnalysisReport] = Field(..., description='News report')