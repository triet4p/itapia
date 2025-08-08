from itapia_common.schemas.entities.users import UserEntity, UserCreate, UserUpdate

class UserResponse(UserEntity):
    pass

class UserCreateRequest(UserCreate):
    pass

class UserUpdateRequest(UserUpdate):
    pass