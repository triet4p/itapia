from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any, Literal
from itapia_common.schemas.enums import SemanticType

class RuleCreateRequest(BaseModel):
    """Schema cho dữ liệu ĐI VÀO khi tạo một Rule mới."""
    rule_id: str = Field(..., min_length=3, description="Name or ID of this rule")
    name: str = Field(..., description='Plain text describe rule')
    description: str = Field(default="", description='Description what the rule do')
    purpose: SemanticType = Field(..., description="Purpose of this rule")
    
    # Root được nhận dưới dạng dictionary thô từ JSON
    root: Dict[str, Any] = Field(..., description="Cấu trúc JSON của cây logic")

class RuleResponse(BaseModel):
    """Schema cho dữ liệu ĐI RA sau khi tạo Rule thành công."""
    rule_id: str
    name: str
    purpose: SemanticType
    version: float
    is_active: bool
    created_at_ts: int

    class Config:
        from_attributes = True