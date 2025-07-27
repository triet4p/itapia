from pydantic import BaseModel, Field
from typing import Literal, Optional

from itapia_common.dblib.schemas.reports.technical import DailyAnalysisReport
from itapia_common.dblib.schemas.reports.technical import IntradayAnalysisReport

class TechnicalReport(BaseModel):
    report_type: Literal['daily', 'intraday', 'all'] = Field(default='all', description='Decide which analysis type will be chosen')
    daily_report: Optional[DailyAnalysisReport] = Field(..., description='Daily Analysis Report')
    intraday_report: Optional[IntradayAnalysisReport] = Field(..., description='Intraday Analysis Report')
    