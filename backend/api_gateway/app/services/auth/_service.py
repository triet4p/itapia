from app.core.exceptions import AuthError
from app.services.users import UserService
from itapia_common.schemas.entities.auth import TokenPayload
from itapia_common.schemas.entities.users import UserEntity

from .security import verify_access_token


def get_current_user(
    user_service: UserService,
    token: str,
) -> UserEntity:
    """Get the current user based on the provided token.

    Validates the token and retrieves the corresponding user from the database.

    Args:
        user_service (UserService): UserService instance for user operations
        token (str): Access token to validate

    Returns:
        UserEntity: The authenticated user

    Raises:
        AuthError: If token validation fails or user is not found
    """
    try:
        payload = verify_access_token(token)
        token_payload = TokenPayload.model_validate(payload)
        user_id = token_payload.sub

        if user_id is None:
            raise AuthError("Invalid token payload")
    except Exception:
        raise AuthError("Could not validate credentials")

    user = user_service.get_user_by_id(user_id)
    return user
