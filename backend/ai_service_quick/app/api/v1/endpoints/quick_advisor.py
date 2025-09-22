# api/v1/endpoints/quick_advisor.py
"""Advisor endpoints for generating investment recommendations."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse

from app.orchestrator import AIServiceQuickOrchestrator
from app.core.exceptions import NoDataError, MissingReportError, NotReadyServiceError
from app.dependencies import get_ceo_orchestrator

from itapia_common.schemas.api.advisor import AdvisorResponse
from itapia_common.schemas.api.personal import QuantitivePreferencesConfigRequest
from itapia_common.schemas.entities.personal import QuantitivePreferencesConfig

router = APIRouter()

@router.post("/advisor/{ticker}/full", 
            response_model=AdvisorResponse,
            summary="Get full advisor report with investment recommendations",
            responses={
                404: {"description": "Ticker or its data not found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_full_advisor_report(quantitive_config: QuantitivePreferencesConfigRequest,
                                  ticker: str, 
                                  limit: int = 10,
                                  orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator),
                                 ):
    """Get full advisor report with investment recommendations.
    
    Args:
        quantitive_config (QuantitivePreferencesConfigRequest): Quantitative preferences configuration
        ticker (str): Stock ticker symbol
        limit (int): Maximum number of rules to include in the report
        orchestrator (AIServiceQuickOrchestrator): Service orchestrator dependency
        
    Returns:
        AdvisorResponse: Complete advisor report with recommendations
    """
    try:
        report = await orchestrator.get_full_advisor_report(ticker=ticker, 
                                                            quantitive_config=QuantitivePreferencesConfig.model_validate(quantitive_config.model_dump()),
                                                            limit=limit)
        return AdvisorResponse.model_validate(report.model_dump())
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)    
    
@router.post("/advisor/{ticker}/explain", 
            response_class=PlainTextResponse,
            summary="Get natural language explanation of advisor recommendations",
            responses={
                404: {"description": "Ticker or its data not found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_full_advisor_explaination_report(quantitive_config: QuantitivePreferencesConfigRequest,
                                               ticker: str, 
                                               limit: int = 10,
                                               orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator),
                                              ):
    """Get natural language explanation of advisor recommendations.
    
    Args:
        quantitive_config (QuantitivePreferencesConfigRequest): Quantitative preferences configuration
        ticker (str): Stock ticker symbol
        limit (int): Maximum number of rules to include in the explanation
        orchestrator (AIServiceQuickOrchestrator): Service orchestrator dependency
        
    Returns:
        str: Natural language explanation of advisor recommendations
    """
    try:
        report = await orchestrator.get_full_advisor_explaination_report(ticker=ticker, 
                                                            quantitive_config=QuantitivePreferencesConfig.model_validate(quantitive_config.model_dump()),
                                                            limit=limit)
        return report
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)    