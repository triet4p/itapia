from typing import Literal
from fastapi import HTTPException
import httpx
from app.core.config import AI_SERVICE_QUICK_BASE_URL

from itapia_common.dblib.schemas.reports import QuickCheckReport
from itapia_common.dblib.schemas.reports.technical import TechnicalReport
from itapia_common.dblib.schemas.reports.forecasting import ForecastingReport
from itapia_common.dblib.schemas.reports.news import NewsAnalysisReport

ai_quick_client = httpx.AsyncClient(base_url=AI_SERVICE_QUICK_BASE_URL, timeout=30.0)

async def get_full_quick_analysis(ticker: str, 
                             daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                             required_type: Literal['daily', 'intraday', 'all']='all') -> QuickCheckReport:
    try:
        print(f'Get for url {ai_quick_client.base_url}/quick/analysis/full/{ticker}')
        response = await ai_quick_client.get(f"/quick/analysis/full/{ticker}", params={
            'daily_analysis_type': daily_analysis_type,
            'required_type': required_type
        })
        response.raise_for_status()
        return QuickCheckReport.model_validate(response.json())
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail") or "Unknown error from AI Service"
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        # Xử lý lỗi kết nối
        raise HTTPException(status_code=503, detail=f"AI Service is unavailable: {type(e).__name__}")
    
async def get_technical_quick_analysis(ticker: str, 
                             daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                             required_type: Literal['daily', 'intraday', 'all']='all') -> TechnicalReport:
    try:
        print(f'Get for url {ai_quick_client.base_url}/quick/analysis/technical/{ticker}')
        response = await ai_quick_client.get(f"/quick/analysis/technical/{ticker}", params={
            'daily_analysis_type': daily_analysis_type,
            'required_type': required_type
        })
        response.raise_for_status()
        return TechnicalReport.model_validate(response.json())
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail") or "Unknown error from AI Service"
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        # Xử lý lỗi kết nối
        raise HTTPException(status_code=503, detail=f"AI Service is unavailable: {type(e).__name__}")
    
async def get_forecasting_quick_analysis(ticker: str) -> ForecastingReport:
    try:
        print(f'Get for url {ai_quick_client.base_url}/quick/analysis/forecasting/{ticker}')
        response = await ai_quick_client.get(f"/quick/analysis/forecasting/{ticker}")
        response.raise_for_status()
        return ForecastingReport.model_validate(response.json())
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail") or "Unknown error from AI Service"
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        # Xử lý lỗi kết nối
        raise HTTPException(status_code=503, detail=f"AI Service is unavailable: {type(e).__name__}")
    
async def get_news_quick_analysis(ticker: str) -> NewsAnalysisReport:
    try:
        print(f'Get for url {ai_quick_client.base_url}/quick/analysis/news/{ticker}')
        response = await ai_quick_client.get(f"/quick/analysis/news/{ticker}")
        response.raise_for_status()
        return NewsAnalysisReport.model_validate(response.json())
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail") or "Unknown error from AI Service"
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        # Xử lý lỗi kết nối
        raise HTTPException(status_code=503, detail=f"AI Service is unavailable: {type(e).__name__}")
    
async def get_full_quick_analysis_explain(ticker: str, 
                             daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                             required_type: Literal['daily', 'intraday', 'all']='all',
                             explain_type: Literal['technical', 'news', 'forecasting', 'all'] = 'all') -> str:
    try:
        print(f'Get for url {ai_quick_client.base_url}/quick/analysis/explaination/{ticker}')
        response = await ai_quick_client.get(f"/quick/analysis/explaination/{ticker}", params={
            'daily_analysis_type': daily_analysis_type,
            'required_type': required_type,
            'explain_type': explain_type
        })
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail") or "Unknown error from AI Service"
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        # Xử lý lỗi kết nối
        raise HTTPException(status_code=503, detail=f"AI Service is unavailable: {type(e).__name__}")
    
