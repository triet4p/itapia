# schemas/api/profiles.py
"""API schemas for investment profiles."""

from itapia_common.schemas.entities.profiles import (
    ProfileBase,
    ProfileCreate,
    ProfileUpdate,
)


class ProfileCreateRequest(ProfileCreate):
    """Request schema for creating a new investment profile."""


class ProfileUpdateRequest(ProfileUpdate):
    """Request schema for updating an existing investment profile."""


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
