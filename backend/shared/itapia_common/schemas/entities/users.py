# api_gateway/app/schemas/user.py
"""User schemas for ITAPIA."""

from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    """Base user schema."""
    
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    google_id: str

class UserUpdate(UserBase):
    """Schema for updating user information."""
    pass

class UserEntity(UserBase):
    """User entity with database fields."""
    
    user_id: str
    google_id: str
    is_active: bool

    class Config:
        from_attributes = True