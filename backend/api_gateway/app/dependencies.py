from itapia_common.dblib.session import get_rdbms_session

from sqlalchemy.orm import Session

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from .services.users import UserService
from .services.profiles import ProfileService
from .services.auth import get_current_user

from itapia_common.schemas.entities.users import UserEntity

def get_users_service(rdbms_session: Session = Depends(get_rdbms_session)) -> UserService:
    return UserService(rdbms_session)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user_dep(
    user_service: UserService = Depends(get_users_service),
    token: str = Depends(oauth2_scheme)
) -> UserEntity:
    return get_current_user(user_service, token)

def get_profile_service(rdbms_session: Session = Depends(get_rdbms_session)):
    return ProfileService(rdbms_session)