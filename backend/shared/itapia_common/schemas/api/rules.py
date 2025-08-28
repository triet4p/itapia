from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any, Literal
from itapia_common.schemas.entities.rules import NodeEntity, NodeSpecEntity, SemanticType, NodeType, RuleStatus

class NodeResponse(NodeSpecEntity):
    pass

class RuleCreateRequest(BaseModel):
    """Schema cho dữ liệu ĐI VÀO khi tạo một Rule mới."""
    rule_id: str = Field(..., min_length=3, description="Name or ID of this rule")
    name: str = Field(..., description='Plain text describe rule')
    description: str = Field(default="", description='Description what the rule do')
    purpose: SemanticType = Field(..., description="Purpose of this rule")
    
    # Root được nhận dưới dạng dictionary thô từ JSON
    root: NodeEntity = Field(..., description="Cấu trúc JSON của cây logic")

class RuleResponse(BaseModel):
    """Schema cho dữ liệu ĐI RA sau khi tạo Rule thành công."""
    rule_id: str
    name: str
    purpose: SemanticType
    rule_status: RuleStatus
    created_at_ts: int
    root: NodeEntity

    class Config:
        from_attributes = True
        
class ExplainationRuleResponse(RuleResponse):
    explain: str