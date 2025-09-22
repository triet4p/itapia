"""Analysis endpoints that proxy requests to the AI Quick Service."""

from typing import Literal

from app.clients.ai_quick_analysis import (
    get_forecasting_quick_analysis,
    get_full_quick_analysis,
    get_full_quick_analysis_explain,
    get_news_quick_analysis,
    get_technical_quick_analysis,
)
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from itapia_common.schemas.api.analysis import QuickCheckReportResponse
from itapia_common.schemas.api.analysis.forecasting import ForecastingReportResponse
from itapia_common.schemas.api.analysis.news import NewsReportResponse
from itapia_common.schemas.api.analysis.technical import TechnicalReportResponse

router = APIRouter()


@router.get(
    "/analysis/quick/{ticker}/full",
    response_model=QuickCheckReportResponse,
    tags=["AI Quick Analysis"],
    summary="Get full market analysis report from AI Quick Service",
)
async def get_ai_full_quick_analysis(
    ticker: str,
    daily_analysis_type: Literal["short", "medium", "long"] = "medium",
    required_type: Literal["daily", "intraday", "all"] = "all",
):
    """Get full market analysis report from AI Quick Service.

    Args:
        ticker (str): Stock ticker symbol
        daily_analysis_type (Literal['short', 'medium', 'long']): Daily analysis time frame
        required_type (Literal['daily', 'intraday', 'all']): Type of analysis to include

    Returns:
        QuickCheckReportResponse: Complete market analysis report
    """
    report = await get_full_quick_analysis(ticker, daily_analysis_type, required_type)
    return report


@router.get(
    "/analysis/quick/{ticker}/technical",
    response_model=TechnicalReportResponse,
    tags=["AI Quick Analysis"],
    summary="Get technical analysis report from AI Quick Service",
)
async def get_ai_technical_quick_analysis(
    ticker: str,
    daily_analysis_type: Literal["short", "medium", "long"] = "medium",
    required_type: Literal["daily", "intraday", "all"] = "all",
):
    """Get technical analysis report from AI Quick Service.

    Args:
        ticker (str): Stock ticker symbol
        daily_analysis_type (Literal['short', 'medium', 'long']): Daily analysis time frame
        required_type (Literal['daily', 'intraday', 'all']): Type of analysis to include

    Returns:
        TechnicalReportResponse: Technical analysis report
    """
    report = await get_technical_quick_analysis(
        ticker, daily_analysis_type, required_type
    )
    return report


@router.get(
    "/analysis/quick/{ticker}/forecasting",
    response_model=ForecastingReportResponse,
    tags=["AI Quick Analysis"],
    summary="Get forecasting analysis report from AI Quick Service",
)
async def get_ai_forecasting_quick_analysis(ticker: str):
    """Get forecasting analysis report from AI Quick Service.

    Args:
        ticker (str): Stock ticker symbol

    Returns:
        ForecastingReportResponse: Forecasting analysis report
    """
    report = await get_forecasting_quick_analysis(ticker)
    return report


@router.get(
    "/analysis/quick/{ticker}/news",
    response_model=NewsReportResponse,
    tags=["AI Quick Analysis"],
    summary="Get news analysis report from AI Quick Service",
)
async def get_ai_news_quick_analysis(ticker: str):
    """Get news analysis report from AI Quick Service.

    Args:
        ticker (str): Stock ticker symbol

    Returns:
        NewsReportResponse: News analysis report
    """
    report = await get_news_quick_analysis(ticker)
    return report


@router.get(
    "/analysis/quick/{ticker}/explain",
    response_class=PlainTextResponse,
    tags=["AI Quick Analysis"],
    summary="Get natural language explanation of market analysis from AI Quick Service",
)
async def get_ai_quick_analysis_plain(
    ticker: str,
    daily_analysis_type: Literal["short", "medium", "long"] = "medium",
    required_type: Literal["daily", "intraday", "all"] = "all",
    explain_type: Literal["technical", "news", "forecasting", "all"] = "all",
):
    """Get natural language explanation of market analysis from AI Quick Service.

    Args:
        ticker (str): Stock ticker symbol
        daily_analysis_type (Literal['short', 'medium', 'long']): Daily analysis time frame
        required_type (Literal['daily', 'intraday', 'all']): Type of analysis to include
        explain_type (Literal['technical', 'news', 'forecasting', 'all']): Type of explanation to generate

    Returns:
        str: Natural language explanation of market analysis
    """
    report = await get_full_quick_analysis_explain(
        ticker, daily_analysis_type, required_type, explain_type
    )
    return report
