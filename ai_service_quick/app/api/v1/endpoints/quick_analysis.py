# api/v1/endpoints/quick_analysis.py
from typing import Literal, Union
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse

from app.orchestrator import AIServiceQuickOrchestrator
from app.core.exceptions import PreloadCacheError, NoDataError, MissingReportError, NotReadyServiceError
from app.dependencies import get_ceo_orchestrator

from itapia_common.schemas.api.analysis import QuickCheckReportResponse
from itapia_common.schemas.api.analysis.technical import TechnicalReportResponse
from itapia_common.schemas.api.analysis.forecasting import ForecastingReportResponse
from itapia_common.schemas.api.analysis.news import NewsReportResponse

router = APIRouter()

@router.get("/analysis/{ticker}/full", 
            response_model=QuickCheckReportResponse,
            responses={
                404: {"description": "Ticker or its data not found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_full_quick_analysis(ticker: str, 
                       orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator),
                       daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                       required_type: Literal['daily', 'intraday', 'all']='all'):
    try:
        report = await orchestrator.get_full_analysis_report(ticker, daily_analysis_type, required_type)
        return QuickCheckReportResponse.model_validate(report.model_dump())
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)

# ENDPOINT 2: Trả về Plain Text (endpoint mới)
@router.get(
    "/analysis/{ticker}/explain", 
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
    try:
        report = await orchestrator.get_full_analysis_explaination_report(ticker, daily_analysis_type, required_type, explain_type)
        return report
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)

@router.get("/analysis/{ticker}/technical", 
            response_model=TechnicalReportResponse,
            responses={
                404: {"description": "Ticker or its data not found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_technical_quick_analysis(ticker: str, 
                       orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator),
                       daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                       required_type: Literal['daily', 'intraday', 'all']='all'):
    try:
        report = await orchestrator.get_technical_report(ticker, daily_analysis_type, required_type)
        return TechnicalReportResponse.model_validate(report.model_dump())
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)

@router.get("/analysis/{ticker}/forecasting", 
            response_model=ForecastingReportResponse,
            responses={
                404: {"description": "Ticker or its data not found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_forecasting_quick_analysis(ticker: str, 
                       orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator)):
    try:
        report = await orchestrator.get_forecasting_report(ticker)
        return ForecastingReportResponse.model_validate(report.model_dump())
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)

@router.get("/analysis/{ticker}/news", 
            response_model=NewsReportResponse,
            responses={
                404: {"description": "Ticker or its data not found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_news_quick_analysis(ticker: str, 
                       orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator)):
    try:
        report = await orchestrator.get_news_report(ticker)
        return NewsReportResponse.model_validate(report.model_dump())
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)