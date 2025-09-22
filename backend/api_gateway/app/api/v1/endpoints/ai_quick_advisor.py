"""Advisor endpoints that proxy requests to the AI Quick Service."""

from app.clients.ai_quick_advisor import (
    get_full_quick_advisor,
    get_full_quick_advisor_explain,
)
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from itapia_common.schemas.api.advisor import AdvisorResponse
from itapia_common.schemas.api.personal import QuantitivePreferencesConfigRequest

router = APIRouter()


@router.post(
    "/advisor/quick/{ticker}/full",
    response_model=AdvisorResponse,
    tags=["AI Quick Advisor"],
    summary="Get full advisor report from AI Quick Service",
)
async def get_ai_full_quick_advisor(
    quantitive_config: QuantitivePreferencesConfigRequest, ticker: str, limit: int = 10
):
    """Get full advisor report from AI Quick Service.

    Args:
        quantitive_config (QuantitivePreferencesConfigRequest): Quantitative preferences configuration
        ticker (str): Stock ticker symbol
        limit (int): Maximum number of rules to include in the report

    Returns:
        AdvisorResponse: Complete advisor report with recommendations
    """
    report = await get_full_quick_advisor(quantitive_config, ticker, limit)
    return report


@router.post(
    "/advisor/quick/{ticker}/explain",
    response_class=PlainTextResponse,
    tags=["AI Quick Advisor"],
    summary="Get natural language explanation of advisor recommendations from AI Quick Service",
)
async def get_ai_full_quick_advisor_explain(
    quantitive_config: QuantitivePreferencesConfigRequest, ticker: str, limit: int = 10
):
    """Get natural language explanation of advisor recommendations from AI Quick Service.

    Args:
        quantitive_config (QuantitivePreferencesConfigRequest): Quantitative preferences configuration
        ticker (str): Stock ticker symbol
        limit (int): Maximum number of rules to include in the explanation

    Returns:
        str: Natural language explanation of advisor recommendations
    """
    report = await get_full_quick_advisor_explain(quantitive_config, ticker, limit)
    return report
