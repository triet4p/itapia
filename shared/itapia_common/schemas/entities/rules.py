from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any, Literal
from itapia_common.schemas.enums import SemanticType
        
class RuleEntity(BaseModel):
    rule_id: str
    name: str
    description: str
    version: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Định nghĩa quy tắc được giữ dưới dạng dictionary
    rule_definition: Dict[str, Any]
    
    class Config:
        from_attributes = True