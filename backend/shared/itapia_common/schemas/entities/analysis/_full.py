from pydantic import BaseModel, Field

from .forecasting import ForecastingReport
from .news import NewsAnalysisReport
from .technical import TechnicalReport


class QuickCheckAnalysisReport(BaseModel):
    """Complete quick check analysis report combining technical, forecasting, and news analysis."""

    ticker: str = Field(..., description="Symbol of ticker")
    generated_at_utc: str = Field(
        ..., description="ISO format string of generated time"
    )
    generated_timestamp: int = Field(
        ..., description="Timestamp value of generated time"
    )
    technical_report: TechnicalReport = Field(..., description="Technical Report")
    forecasting_report: ForecastingReport = Field(..., description="Forecasting report")
    news_report: NewsAnalysisReport = Field(..., description="News report")
