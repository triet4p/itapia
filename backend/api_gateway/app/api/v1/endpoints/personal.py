"""Personal endpoints that proxy requests to the AI Service."""

from fastapi import APIRouter
from app.clients.ai_personal import get_suggest_config
from itapia_common.schemas.api.personal import QuantitivePreferencesConfigResponse
from itapia_common.schemas.api.profiles import ProfileRequest

router = APIRouter()

@router.post("/personal/suggested_config",
             response_model=QuantitivePreferencesConfigResponse,
             tags=['Personal'],
             summary="Get suggested quantitative preferences configuration from AI Service")
async def get_ai_suggest_config(profile: ProfileRequest) -> QuantitivePreferencesConfigResponse:
    """Get suggested quantitative preferences configuration from AI Service.
    
    Args:
        profile (ProfileRequest): User investment profile
        
    Returns:
        QuantitivePreferencesConfigResponse: Suggested quantitative preferences configuration
    """
    return await get_suggest_config(profile)