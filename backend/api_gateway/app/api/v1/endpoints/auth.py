"""Authentication endpoints for user login and token management."""

import app.services.auth.google as google
from app.core.config import FRONTEND_CALLBACK_URL, FRONTEND_LOGIN_ERR_URL
from app.core.exceptions import ServerCredError
from app.dependencies import get_users_service
from app.services.auth.security import create_access_token, get_authorized_url
from app.services.users import UserService
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from itapia_common.schemas.api.auth import AuthorizationURLResponse

router = APIRouter()


@router.get(
    "/auth/google/login",
    response_model=AuthorizationURLResponse,
    tags=["Auth"],
    summary="Get Google OAuth authorization URL",
)
def google_login():
    """Get Google OAuth authorization URL.

    Returns:
        AuthorizationURLResponse: Google OAuth authorization URL
    """
    try:
        url = get_authorized_url()
        return AuthorizationURLResponse(authorization_url=url)
    except ServerCredError as e:
        raise HTTPException(status_code=401, detail=e.detail, headers=e.header)
    except Exception:
        raise HTTPException(status_code=500, detail="Unknown Error occured in servers")


@router.get(
    "/auth/google/callback",
    summary="Handle Google OAuth callback and generate JWT token",
)
async def google_callback(
    code: str, user_service: UserService = Depends(get_users_service)
):
    """Handle Google OAuth callback and generate JWT token.

    Args:
        code (str): Authorization code from Google OAuth
        user_service (UserService): User service dependency

    Returns:
        RedirectResponse: Redirect to frontend with JWT token or error message
    """
    try:
        # 1 & 2. Get token and user info from Google
        google_tokens = await google.get_google_tokens(code=code)
        user_info = await google.get_google_user_info(
            access_token=google_tokens["access_token"]
        )

        # 3. Find or create user in database
        user_in_db = user_service.get_or_create(user_info)

        # 4. Create ITAPIA JWT
        # Token payload will contain user ID in your system
        access_token = create_access_token(subject=user_in_db.user_id)

        # 5. Redirect to frontend
        # TODO: Move this URL to environment variables
        frontend_callback_url = f"{FRONTEND_CALLBACK_URL}?token={access_token}"
        return RedirectResponse(url=frontend_callback_url)

    except ServerCredError as e:
        # If there's an error communicating with Google, redirect to frontend login page with error message
        # TODO: Move this URL to environment variables
        return RedirectResponse(url=f"{FRONTEND_LOGIN_ERR_URL}?error={e.detail}")
    except Exception:
        raise HTTPException(status_code=500, detail="Unknown Error occured in servers")
