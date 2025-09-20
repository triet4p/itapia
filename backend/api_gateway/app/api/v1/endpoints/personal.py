from fastapi import APIRouter
from app.clients.ai_personal import get_suggest_config
from itapia_common.schemas.api.personal import QuantitivePreferencesConfigResponse
from itapia_common.schemas.api.profiles import ProfileRequest

router = APIRouter()

@router.post("/personal/suggested_config",
             response_model=QuantitivePreferencesConfigResponse,
             tags=['Personal'])
async def get_ai_suggest_config(profile: ProfileRequest) -> QuantitivePreferencesConfigResponse:
    return await get_suggest_config(profile)