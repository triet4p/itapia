from typing import Literal
from fastapi import HTTPException
import httpx
from app.core.config import AI_SERVICE_QUICK_BASE_URL

from itapia_common.dblib.schemas.reports import QuickCheckReport

ai_quick_client = httpx.AsyncClient(base_url=AI_SERVICE_QUICK_BASE_URL, timeout=30.0)

async def get_quick_analysis(ticker: str, 
                             daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                             required_type: Literal['daily', 'intraday', 'all']='all') -> QuickCheckReport:
    try:
        print(f'Get for url {ai_quick_client.base_url}/quick/{ticker}')
        response = await ai_quick_client.get(f"/quick/{ticker}", params={
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