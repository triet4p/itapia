import httpx
from app.core.config import AI_SERVICE_QUICK_BASE_URL
from fastapi import HTTPException
from itapia_common.schemas.api.personal import QuantitivePreferencesConfigResponse
from itapia_common.schemas.api.profiles import ProfileRequest

ai_personal_client = httpx.AsyncClient(base_url=AI_SERVICE_QUICK_BASE_URL, timeout=10.0)


async def get_suggest_config(
    profile: ProfileRequest,
) -> QuantitivePreferencesConfigResponse:
    try:
        print(f"Get for url {ai_personal_client.base_url}/personal/suggested_config")
        body = profile.model_dump()
        response = await ai_personal_client.post(
            f"/personal/suggested_config", json=body
        )
        response.raise_for_status()
        return QuantitivePreferencesConfigResponse.model_validate(response.json())
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail") or "Unknown error from AI Service"
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        # Xử lý lỗi kết nối
        raise HTTPException(
            status_code=503, detail=f"AI Service is unavailable: {type(e).__name__}"
        )
