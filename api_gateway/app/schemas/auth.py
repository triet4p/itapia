from typing import Optional
from pydantic import BaseModel

class AuthorizationURL(BaseModel):
    authorization_url: str
    
    class Config:
        from_attributes = True
        
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None