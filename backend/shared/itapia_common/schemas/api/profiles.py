# schemas/api/profiles.py
"""API schemas for investment profiles."""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
from itapia_common.schemas.entities.profiles import ProfileCreate, ProfileBase, ProfileEntity, ProfileUpdate

class ProfileCreateRequest(ProfileCreate):
    """Request schema for creating a new investment profile."""
    pass

class ProfileUpdateRequest(ProfileUpdate):
    """Request schema for updating an existing investment profile."""
    pass

class ProfileResponse(ProfileBase):
    """Response schema for investment profile data."""
    
    profile_id: str
    user_id: str
    created_at_ts: int
    updated_at_ts: int
    
class ProfileRequest(ProfileBase):
    """Request schema for investment profile operations."""
    
    profile_id: str
    user_id: str
    created_at_ts: int
    updated_at_ts: int
