# api/v1/endpoints/quick_advisor.py
from typing import Literal, Union
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse

from app.orchestrator import AIServiceQuickOrchestrator
from app.core.exceptions import PreloadCacheError, NoDataError, MissingReportError, NotReadyServiceError
from app.dependencies import get_ceo_orchestrator

from itapia_common.schemas.entities.advisor import AdvisorReportSchema

router = APIRouter()

@router.get("/quick/advisor/{ticker}", 
            response_model=AdvisorReportSchema,
            responses={
                404: {"description": "Ticker or its data not found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_full_advisor_report(ticker: str, 
                       orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator)):
    try:
        report = await orchestrator.get_full_advisor_report(ticker=ticker, 
                                                            daily_analysis_type='medium', required_type='all')
        return AdvisorReportSchema.model_validate(report.model_dump())
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)    