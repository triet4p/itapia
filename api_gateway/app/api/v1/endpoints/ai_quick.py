from typing import Literal
from fastapi import APIRouter
from app.clients.ai_quick import get_quick_analysis

from itapia_common.dblib.schemas.reports import QuickCheckReport

router = APIRouter()

@router.get('/ai/quick/{ticker}', response_model=QuickCheckReport, tags=['AI'])
async def get_ai_quick_analysis(ticker: str, 
                             daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                             required_type: Literal['daily', 'intraday', 'all'] = 'all'):
    report = await get_quick_analysis(ticker, daily_analysis_type, required_type)
    return report