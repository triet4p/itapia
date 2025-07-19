# api/v1/endpoints/data_viewer.py
from typing import Literal
from fastapi import APIRouter

from app.orchestrator import AIServiceQuickOrchestrator

router = APIRouter()
orchestrator = AIServiceQuickOrchestrator()

@router.get("/analysis/quick/full/{ticker}")
def get_full_quick_analysis(ticker: str, daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                            required_type: Literal['daily', 'intraday', 'all']='all'):
    return orchestrator.get_full_analysis_report(ticker, daily_analysis_type, required_type)