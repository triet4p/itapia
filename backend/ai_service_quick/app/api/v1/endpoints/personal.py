from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.dependencies import get_ceo_orchestrator
from itapia_common.schemas.api.personal import QuantitivePreferencesConfigResponse
from itapia_common.schemas.api.profiles import ProfileRequest
from app.orchestrator import AIServiceQuickOrchestrator
from itapia_common.schemas.entities.profiles import ProfileEntity

router = APIRouter()

@router.post("/personal/suggested_config",
             response_model=QuantitivePreferencesConfigResponse,
             summary="Get suggested quantitative preferences configuration based on user profile")
async def get_suggest_config(profile: ProfileRequest,
                             orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator)) -> QuantitivePreferencesConfigResponse:
    """Get suggested quantitative preferences configuration based on user profile.
    
    Args:
        profile (ProfileRequest): User investment profile
        orchestrator (AIServiceQuickOrchestrator): Service orchestrator dependency
        
    Returns:
        QuantitivePreferencesConfigResponse: Suggested quantitative preferences configuration
    """
    config = orchestrator.get_suggest_config(ProfileEntity(
        created_at=datetime.fromtimestamp(profile.created_at_ts, tz=timezone.utc),
        updated_at=datetime.fromtimestamp(profile.updated_at_ts, tz=timezone.utc),
        **profile.model_dump()
    ))
    return QuantitivePreferencesConfigResponse.model_validate(config.model_dump())