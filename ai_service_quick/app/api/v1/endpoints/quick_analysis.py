# api/v1/endpoints/data_viewer.py
from fastapi import APIRouter

from app.orchestrator import AIServiceQuickOrchestrator

router = APIRouter()
orchestrator = AIServiceQuickOrchestrator()

@router.get("/analysis/quick/full/{ticker}")
def get_full_quick_analysis(ticker: str):
    return orchestrator.get_full_analysis_report(ticker)