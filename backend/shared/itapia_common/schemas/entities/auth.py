from typing import Optional
from pydantic import BaseModel

class AuthorizationURL(BaseModel):
    """Authorization URL for OAuth flow."""
    
    authorization_url: str
    
    class Config:
        from_attributes = True
        
class Token(BaseModel):
    """Access token information."""
    
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """Payload contained in a JWT token."""
    
    sub: Optional[str] = None