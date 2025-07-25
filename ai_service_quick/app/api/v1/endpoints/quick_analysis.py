# api/v1/endpoints/quick_analysis.py
from typing import Literal, Union
from fastapi import APIRouter, HTTPException, Depends

from app.orchestrator import AIServiceQuickOrchestrator

from app.dependencies import get_ceo_orchestrator

from itapia_common.dblib.schemas.reports import ErrorResponse, QuickCheckReport

router = APIRouter()

@router.get("/quick/{ticker}", 
            response_model=Union[QuickCheckReport, ErrorResponse],
            responses={
                404: {"description": "Ticker or its data not found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_quick_analysis(ticker: str, 
                       orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator),
                       daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                       required_type: Literal['daily', 'intraday', 'all']='all'):
    report = await orchestrator.get_full_analysis_report(ticker, daily_analysis_type, required_type)
    if isinstance(report, ErrorResponse):
        raise HTTPException(status_code=report.code, detail=report.error)
    
    return report