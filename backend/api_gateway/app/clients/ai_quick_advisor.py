from typing import Literal
from fastapi import HTTPException
import httpx
from app.core.config import AI_SERVICE_QUICK_BASE_URL

from itapia_common.schemas.api.advisor import AdvisorResponse

ai_quick_advisor_client = httpx.AsyncClient(base_url=AI_SERVICE_QUICK_BASE_URL, timeout=30.0)

async def get_full_quick_advisor(ticker: str, user_id: str) -> AdvisorResponse:
    try:
        print(f'Get for url {ai_quick_advisor_client.base_url}/advisor/{ticker}/full')
        response = await ai_quick_advisor_client.get(f"/advisor/{ticker}/full", params={
            'user_id': user_id
        })
        response.raise_for_status()
        return AdvisorResponse.model_validate(response.json())
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail") or "Unknown error from AI Service"
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        # Xử lý lỗi kết nối
        raise HTTPException(status_code=503, detail=f"AI Service is unavailable: {type(e).__name__}")
    
async def get_full_quick_advisor_explain(ticker: str, user_id: str) -> str:
    try:
        print(f'Get for url {ai_quick_advisor_client.base_url}/advisor/{ticker}/explain')
        response = await ai_quick_advisor_client.get(f"/advisor/{ticker}/explain", params={
            'user_id': user_id
        })
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail") or "Unknown error from AI Service"
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        # Xử lý lỗi kết nối
        raise HTTPException(status_code=503, detail=f"AI Service is unavailable: {type(e).__name__}")