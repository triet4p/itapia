from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Literal, Optional
from itapia_common.schemas.enums import SemanticType, NodeType

class NodeEntity(BaseModel):
    node_name: str
    children: Optional[List['NodeEntity']] = Field(default=None)
     
    class Config:
        from_attributes = True

class NodeSpecEntity(BaseModel):
    node_name: str
    description: str
    node_type: NodeType
    return_type: SemanticType = Field(..., description='return type of a nodes')
    args_type: Optional[List[SemanticType]] = Field(default=None, description='Argument type, only need for operator node')
    
    class Config:
        from_attributes = True
        
class RuleEntity(BaseModel):
    rule_id: str
    name: str
    description: str
    purpose: SemanticType
    version: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Định nghĩa quy tắc được giữ dưới dạng dictionary
    root: NodeEntity
    
    class Config:
        from_attributes = True
        
class ExplainationRuleEntity(RuleEntity):
    explain: str
    