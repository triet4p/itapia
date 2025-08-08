from .security import verify_access_token
from app.services.users import UserService
from app.core.exceptions import AuthError
from itapia_common.schemas.entities.users import UserEntity
from itapia_common.schemas.entities.auth import TokenPayload


def get_current_user(
    user_service: UserService,
    token: str,
) -> UserEntity:
    try:
        payload = verify_access_token(token)
        token_payload = TokenPayload.model_validate(payload)
        user_id = token_payload.sub
        
        if user_id is None:
            raise AuthError('Invalid token payload')
    except Exception:
        raise AuthError('Could not validate credentials')
        
    user = user_service.get_user_by_id(user_id)
    return user