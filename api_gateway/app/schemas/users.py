# api_gateway/app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    google_id: str

class UserUpdate(UserBase):
    pass

class UserEntity(UserBase):
    user_id: str
    google_id: str
    is_active: bool

    class Config:
        from_attributes = True