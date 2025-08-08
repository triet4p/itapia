# schemas/api/profiles.py

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
from itapia_common.schemas.entities.profiles import ProfileCreate, ProfileBase, ProfileUpdate

class ProfileCreateRequest(ProfileCreate):
    pass

class ProfileUpdateRequest(ProfileUpdate):
    pass

class ProfileResponse(ProfileBase):
    profile_id: str
    user_id: str
    created_at_ts: int
    updated_at_ts: int
