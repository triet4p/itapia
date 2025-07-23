# api/v1/endpoints/data_viewer.py
from typing import Literal, Union
from fastapi import APIRouter, HTTPException, Depends

from app.orchestrator import AIServiceQuickOrchestrator

from app.dependencies import get_ceo_orchestrator

from itapia_common.dblib.schemas.reports import ErrorResponse, QuickCheckReport

router = APIRouter()

@router.get("/quick/{ticker}", response_model=Union[QuickCheckReport, ErrorResponse])
def get_quick_analysis(ticker: str, 
                       orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator),
                       daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                       required_type: Literal['daily', 'intraday', 'all']='all'):
    report = orchestrator.get_full_analysis_report(ticker, daily_analysis_type, required_type)
    if isinstance(report, ErrorResponse):
        raise HTTPException(status_code=404, detail=report.error)
    
    return report