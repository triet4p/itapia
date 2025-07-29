from fastapi import Request
from .orchestrator import AIServiceQuickOrchestrator

def get_ceo_orchestrator(request: Request) -> AIServiceQuickOrchestrator:
    """
    Một dependency đơn giản để lấy instance của "CEO" Orchestrator
    đã được lưu trong app.state.
    """
    return request.app.state.ceo_orchestrator