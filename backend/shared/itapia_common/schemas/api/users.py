from itapia_common.schemas.entities.users import UserEntity, UserCreate, UserUpdate

class UserResponse(UserEntity):
    """Response schema for user data."""
    pass

class UserCreateRequest(UserCreate):
    """Request schema for creating a new user."""
    pass

class UserUpdateRequest(UserUpdate):
    """Request schema for updating user data."""
    pass