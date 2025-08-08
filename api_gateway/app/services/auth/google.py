# api_gateway/app/auth/google.py
import httpx
from fastapi import HTTPException, status
from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, BACKEND_CALLBACK_URL, \
    GOOGLE_TOKEN_URL, GOOGLE_USERINFO_URL
    
from itapia_common.schemas.entities.users import UserCreate

async def get_google_tokens(*, code: str) -> dict:
    """
    Trao đổi authorization code để lấy access token và id token.
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=tokens.get("error_description", "Failed to fetch Google tokens."),
        )
    return tokens

async def get_google_user_info(*, access_token: str) -> UserCreate:
    """
    Dùng access token để lấy thông tin chi tiết của người dùng từ Google.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    
    user_info: dict = response.json()
    if not user_info.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch Google user info.",
        )
        
    user_create = UserCreate(
        email=user_info.get('email'),
        full_name=user_info.get('name'),
        avatar_url=user_info.get('picture'),
        google_id=user_info['sub']
    )
    
    return user_create