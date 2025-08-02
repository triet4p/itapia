from typing import Literal
from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from app.clients.ai_quick_advisor import get_full_quick_advisor, get_full_quick_advisor_explain

from itapia_common.schemas.api.advisor import AdvisorResponse

router = APIRouter()

@router.get('/advisor/quick/{ticker}/full', response_model=AdvisorResponse, tags=['AI Quick Advisor'])
async def get_ai_full_quick_advisor(ticker: str, user_id: str = ""):
    report = await get_full_quick_advisor(ticker, user_id)
    return report

@router.get('/advisor/quick/{ticker}/explain', response_class=PlainTextResponse, tags=['AI Quick Advisor'])
async def get_ai_full_quick_advisor_explain(ticker: str, user_id: str=""):
    report = await get_full_quick_advisor_explain(ticker, user_id)
    return report

