from typing import Literal
from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from app.clients.ai_quick_advisor import get_full_quick_advisor, get_full_quick_advisor_explain

from itapia_common.schemas.api.advisor import AdvisorResponse
from itapia_common.schemas.api.personal import QuantitivePreferencesConfigRequest

router = APIRouter()

@router.post('/advisor/quick/{ticker}/full', response_model=AdvisorResponse, tags=['AI Quick Advisor'])
async def get_ai_full_quick_advisor(quantitive_config: QuantitivePreferencesConfigRequest,
                                  ticker: str, 
                                  limit: int = 10):
    report = await get_full_quick_advisor(quantitive_config, ticker, limit)
    return report

@router.post('/advisor/quick/{ticker}/explain', response_class=PlainTextResponse, tags=['AI Quick Advisor'])
async def get_ai_full_quick_advisor_explain(quantitive_config: QuantitivePreferencesConfigRequest,
                                  ticker: str, 
                                  limit: int = 10):
    report = await get_full_quick_advisor_explain(quantitive_config, ticker, limit)
    return report

