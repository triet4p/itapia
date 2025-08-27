# api_gateway/app/auth/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Union
from urllib.parse import urlencode
from jose import jwt, JWTError
from app.core.config import (
    JWT_SECRET_KEY, 
    JWT_ALGORITHM, 
    ACCESS_TOKEN_EXPIRE_MINUTES, 
    GOOGLE_CLIENT_ID, 
    BACKEND_CALLBACK_URL,
    GOOGLE_AUTH_URL,
    GOOGLE_OAUTH_SCOPES
)
from app.core.exceptions import ServerCredError

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """Create a new access token for a subject.
    
    Args:
        subject (Union[str, Any]): Subject for which the token is created (usually user ID)
        expires_delta (timedelta, optional): Token expiration time. 
            Defaults to ACCESS_TOKEN_EXPIRE_MINUTES if not provided.
            
    Returns:
        str: Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> dict:
    """Verify the access token and return its payload.
    
    Args:
        token (str): JWT token to verify
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        ServerCredError: If token verification fails
    """
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
    """Create and return the URL for users to start the Google login flow.
    
    Returns:
        str: Google OAuth authorization URL
        
    Raises:
        ServerCredError: If Google Client ID is not configured
    """
    if not GOOGLE_CLIENT_ID:
        raise ServerCredError(detail="Google Client ID is not configured.", header=None)

    params = {
        "response_type": "code",
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": BACKEND_CALLBACK_URL,
        "scope": " ".join(GOOGLE_OAUTH_SCOPES),
        "access_type": "offline",
        "prompt": "consent"
    }

    authorization_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    
    return authorization_url