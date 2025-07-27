from typing import Literal
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from app.clients.ai_quick import get_quick_analysis, get_quick_analysis_explain

from itapia_common.dblib.schemas.reports import QuickCheckReport

router = APIRouter()

@router.get('/ai/quick/analysis/{ticker}', response_model=QuickCheckReport, tags=['AI'])
async def get_ai_quick_analysis(ticker: str, 
                             daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                             required_type: Literal['daily', 'intraday', 'all'] = 'all'):
    report = await get_quick_analysis(ticker, daily_analysis_type, required_type)
    return report

@router.get('/ai/quick/analysis/{ticker}/explaination', response_class=PlainTextResponse, tags=['AI'])
async def get_ai_quick_analysis_plain(ticker: str, 
                             daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                             required_type: Literal['daily', 'intraday', 'all'] = 'all',
                             explain_type: Literal['technical', 'news', 'forecasting', 'all'] = 'all'):
    report = await get_quick_analysis_explain(ticker, daily_analysis_type, required_type, explain_type)
    return report