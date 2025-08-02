# api/v1/endpoints/quick_advisor.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse

from app.orchestrator import AIServiceQuickOrchestrator
from app.core.exceptions import NoDataError, MissingReportError, NotReadyServiceError
from app.dependencies import get_ceo_orchestrator

from itapia_common.schemas.api.rules import ExplainationRuleResponse

router = APIRouter()

@router.get("/rules/{rule_id}/explain", 
            response_model=ExplainationRuleResponse,
            responses={
                404: {"description": "Ticker or its data not found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_single_explaination_rule(rule_id: str, 
                       orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator)):
    try:
        report = await orchestrator.get_single_explaination_rule(rule_id=rule_id)
        return ExplainationRuleResponse(
            rule_id=report.rule_id,
            name=report.name,
            purpose=report.purpose,
            version=report.version,
            is_active=report.is_active,
            created_at_ts=int(report.created_at.timestamp()),
            explain=report.explain
        )
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)   