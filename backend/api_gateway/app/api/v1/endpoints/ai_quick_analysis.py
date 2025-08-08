from typing import Literal
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from app.clients.ai_quick_analysis import get_full_quick_analysis, get_full_quick_analysis_explain, \
    get_technical_quick_analysis, get_news_quick_analysis, get_forecasting_quick_analysis

from itapia_common.schemas.api.analysis import QuickCheckReportResponse
from itapia_common.schemas.api.analysis.technical import TechnicalReportResponse
from itapia_common.schemas.api.analysis.forecasting import ForecastingReportResponse
from itapia_common.schemas.api.analysis.news import NewsReportResponse

router = APIRouter()

@router.get('/analysis/quick/{ticker}/full', response_model=QuickCheckReportResponse, tags=['AI Quick Analysis'])
async def get_ai_full_quick_analysis(ticker: str, 
                             daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                             required_type: Literal['daily', 'intraday', 'all'] = 'all'):
    report = await get_full_quick_analysis(ticker, daily_analysis_type, required_type)
    return report

@router.get('/analysis/quick/{ticker}/technical', response_model=TechnicalReportResponse, tags=['AI Quick Analysis'])
async def get_ai_technical_quick_analysis(ticker: str, 
                             daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                             required_type: Literal['daily', 'intraday', 'all'] = 'all'):
    report = await get_technical_quick_analysis(ticker, daily_analysis_type, required_type)
    return report

@router.get('/analysis/quick/{ticker}/forecasting', response_model=ForecastingReportResponse, tags=['AI Quick Analysis'])
async def get_ai_forecasting_quick_analysis(ticker: str):
    report = await get_forecasting_quick_analysis(ticker)
    return report

@router.get('/analysis/quick/{ticker}/news', response_model=NewsReportResponse, tags=['AI Quick Analysis'])
async def get_ai_news_quick_analysis(ticker: str):
    report = await get_news_quick_analysis(ticker)
    return report

@router.get('/analysis/quick/{ticker}/explain', response_class=PlainTextResponse, tags=['AI Quick Analysis'])
async def get_ai_quick_analysis_plain(ticker: str, 
                             daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                             required_type: Literal['daily', 'intraday', 'all'] = 'all',
                             explain_type: Literal['technical', 'news', 'forecasting', 'all'] = 'all'):
    report = await get_full_quick_analysis_explain(ticker, daily_analysis_type, required_type, explain_type)
    return report

