from itapia_common.dblib.session import get_rdbms_session

from sqlalchemy.orm import Session

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from .services.users import UserService
from .services.auth.security import verify_access_token
from .schemas.users import UserEntity
from .schemas.auth import TokenPayload

def get_users_service(rdbms_session: Session = Depends(get_rdbms_session)) -> UserService:
    return UserService(rdbms_session)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(
    user_service: UserService = Depends(get_users_service),
    token: str = Depends(oauth2_scheme)
) -> UserEntity:
    try:
        payload = verify_access_token(token)
        token_payload = TokenPayload.model_validate(payload)
        user_id = token_payload.sub
        
        if user_id is None:
            raise HTTPException(status_code=403, detail='Invalid token payload')
    except Exception:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )
        
    user = user_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user