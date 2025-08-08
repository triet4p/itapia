# api_gateway/app/auth/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Union
from urllib.parse import urlencode
from jose import jwt, JWTError
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, GOOGLE_CLIENT_ID, BACKEND_CALLBACK_URL
from app.core.exceptions import ServerCredError

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> dict:
    credentials_exception = ServerCredError(
        detail="Could not validate credentials",
        header={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception
    
def get_authorized_url():
    """
    Tạo và trả về URL để người dùng bắt đầu luồng đăng nhập với Google.
    """
    if not GOOGLE_CLIENT_ID:
        raise ServerCredError(detail="Google Client ID is not configured.", header=None)

    scopes = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid"
    ]

    params = {
        "response_type": "code",
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": BACKEND_CALLBACK_URL,
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent"
    }

    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    authorization_url = f"{google_auth_url}?{urlencode(params)}"
    
    return authorization_url