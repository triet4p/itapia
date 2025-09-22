# api_gateway/app/auth/google.py
import httpx
from app.core.config import (
    BACKEND_CALLBACK_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_TOKEN_URL,
    GOOGLE_USERINFO_URL,
)
from app.core.exceptions import ServerCredError
from itapia_common.schemas.entities.users import UserCreate


async def get_google_tokens(*, code: str) -> dict:
    """Exchange authorization code for access token and id token.

    Args:
        code (str): Authorization code received from Google OAuth flow

    Returns:
        dict: Dictionary containing access_token, id_token and other token information

    Raises:
        ServerCredError: If token exchange fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": BACKEND_CALLBACK_URL,
                "grant_type": "authorization_code",
            },
        )

    tokens: dict = response.json()
    if "error" in tokens:
        raise ServerCredError(
            detail=tokens.get("error_description", "Failed to fetch Google tokens."),
            header=None,
        )
    return tokens


async def get_google_user_info(*, access_token: str) -> UserCreate:
    """Use access token to get detailed user information from Google.

    Args:
        access_token (str): Access token obtained from Google OAuth flow

    Returns:
        UserCreate: User information object containing email, name, avatar and Google ID

    Raises:
        ServerCredError: If fetching user info fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    user_info: dict = response.json()
    if not user_info.get("sub"):
        raise ServerCredError(detail="Failed to fetch Google user info.", header=None)

    user_create = UserCreate(
        email=user_info.get("email"),
        full_name=user_info.get("name"),
        avatar_url=user_info.get("picture"),
        google_id=user_info["sub"],
    )

    return user_create
