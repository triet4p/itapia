from itapia_common.schemas.entities.users import UserCreate, UserEntity, UserUpdate


class UserResponse(UserEntity):
    """Response schema for user data."""


class UserCreateRequest(UserCreate):
    """Request schema for creating a new user."""


class UserUpdateRequest(UserUpdate):
    """Request schema for updating user data."""
