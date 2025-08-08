# api/v1/endpoints/quick_advisor.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse

from app.orchestrator import AIServiceQuickOrchestrator
from app.core.exceptions import NoDataError, MissingReportError, NotReadyServiceError
from app.dependencies import get_ceo_orchestrator

from itapia_common.schemas.api.advisor import AdvisorResponse

router = APIRouter()

@router.get("/advisor/{ticker}/full", 
            response_model=AdvisorResponse,
            responses={
                404: {"description": "Ticker or its data not found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_full_advisor_report(ticker: str, 
                       orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator),
                       user_id: str=""):
    try:
        report = await orchestrator.get_full_advisor_report(ticker=ticker, user_id=user_id)
        return AdvisorResponse.model_validate(report.model_dump())
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)    
    
@router.get("/advisor/{ticker}/explain", 
            response_class=PlainTextResponse,
            responses={
                404: {"description": "Ticker or its data not found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_full_advisor_explaination_report(ticker: str,
                       orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator), 
                                               user_id: str=""):
    try:
        report = await orchestrator.get_full_advisor_explaination_report(ticker=ticker, user_id=user_id)
        return report
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)    