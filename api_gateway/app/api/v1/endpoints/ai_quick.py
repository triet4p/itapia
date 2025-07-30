from typing import Literal
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from app.clients.ai_quick import get_full_quick_analysis, get_full_quick_analysis_explain, \
    get_technical_quick_analysis, get_news_quick_analysis, get_forecasting_quick_analysis

from itapia_common.schemas.api.reports import QuickCheckReportResponse
from itapia_common.schemas.api.reports.technical import TechnicalReportResponse
from itapia_common.schemas.api.reports.forecasting import ForecastingReportResponse
from itapia_common.schemas.api.reports.news import NewsReportResponse

router = APIRouter()

@router.get('/ai/quick/analysis/full/{ticker}', response_model=QuickCheckReportResponse, tags=['AI'])
async def get_ai_full_quick_analysis(ticker: str, 
                             daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                             required_type: Literal['daily', 'intraday', 'all'] = 'all'):
    report = await get_full_quick_analysis(ticker, daily_analysis_type, required_type)
    return report

@router.get('/ai/quick/analysis/technical/{ticker}', response_model=TechnicalReportResponse, tags=['AI'])
async def get_ai_technical_quick_analysis(ticker: str, 
                             daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                             required_type: Literal['daily', 'intraday', 'all'] = 'all'):
    report = await get_technical_quick_analysis(ticker, daily_analysis_type, required_type)
    return report

@router.get('/ai/quick/analysis/forecasting/{ticker}', response_model=ForecastingReportResponse, tags=['AI'])
async def get_ai_forecasting_quick_analysis(ticker: str):
    report = await get_forecasting_quick_analysis(ticker)
    return report

@router.get('/ai/quick/analysis/news/{ticker}', response_model=NewsReportResponse, tags=['AI'])
async def get_ai_news_quick_analysis(ticker: str):
    report = await get_news_quick_analysis(ticker)
    return report

@router.get('/ai/quick/analysis/explaination/{ticker}', response_class=PlainTextResponse, tags=['AI'])
async def get_ai_quick_analysis_plain(ticker: str, 
                             daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                             required_type: Literal['daily', 'intraday', 'all'] = 'all',
                             explain_type: Literal['technical', 'news', 'forecasting', 'all'] = 'all'):
    report = await get_full_quick_analysis_explain(ticker, daily_analysis_type, required_type, explain_type)
    return report

