from pydantic import BaseModel, Field
from typing import Optional, Any

from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport

class QuickCheckReportResponse(QuickCheckAnalysisReport):
    pass
    