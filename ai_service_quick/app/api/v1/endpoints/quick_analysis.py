# api/v1/endpoints/quick_analysis.py
from typing import Literal, Union
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse

from app.orchestrator import AIServiceQuickOrchestrator

from app.dependencies import get_ceo_orchestrator

from itapia_common.dblib.schemas.reports import ErrorResponse, QuickCheckReport

router = APIRouter()

@router.get("/quick/analysis/{ticker}", 
            response_model=Union[QuickCheckReport, ErrorResponse],
            responses={
                404: {"description": "Ticker or its data not found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_quick_analysis(ticker: str, 
                       orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator),
                       daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                       required_type: Literal['daily', 'intraday', 'all']='all'):
    report = await orchestrator.get_full_analysis_report(ticker, daily_analysis_type, required_type)
    if isinstance(report, ErrorResponse):
        raise HTTPException(status_code=report.code, detail=report.error)
    
    return report

# ENDPOINT 2: Trả về Plain Text (endpoint mới)
@router.get(
    "/quick/analysis/{ticker}/explaination", 
    # response_class=PlainTextResponse đảm bảo header Content-Type là text/plain
    response_class=PlainTextResponse,
    responses={
        404: {"description": "Ticker or its data not found"},
        500: {"description": "Internal analysis module failed"},
        503: {"description": "Service is not ready, still pre-warming caches"}
    } # Các mã lỗi tương tự
)
async def get_quick_analysis_explanation(
    ticker: str,
    orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator),
    daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
    required_type: Literal['daily', 'intraday', 'all'] = 'all',
    explain_type: Literal['technical', 'news', 'forecasting', 'all'] = 'all'
):
    result = await orchestrator.get_full_explanation_report(
        ticker, daily_analysis_type, required_type, explain_type
    )

    if isinstance(result, ErrorResponse):
        raise HTTPException(status_code=result.code, detail=result.error)

    # `result` bây giờ là một chuỗi string
    return result