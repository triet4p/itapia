from typing import Literal, Optional

from pydantic import BaseModel, Field

from .daily import DailyAnalysisReport
from .intraday import IntradayAnalysisReport


class TechnicalReport(BaseModel):
    """Complete technical analysis report combining daily and intraday analysis."""

    report_type: Literal["daily", "intraday", "all"] = Field(
        default="all", description="Decide which analysis type will be chosen"
    )
    daily_report: Optional[DailyAnalysisReport] = Field(
        ..., description="Daily Analysis Report"
    )
    intraday_report: Optional[IntradayAnalysisReport] = Field(
        ..., description="Intraday Analysis Report"
    )
