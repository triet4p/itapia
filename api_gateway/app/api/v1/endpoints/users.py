from fastapi import APIRouter, Depends, HTTPException
from app.schemas.users import UserEntity
from app.dependencies import get_users_service, get_current_user
from app.services.users import UserService

router = APIRouter()

@router.get('/users/me', tags=['Users'])
def get_me(current_user = Depends(get_current_user)):
    return current_user