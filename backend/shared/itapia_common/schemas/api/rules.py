from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any, Literal, Optional
from itapia_common.schemas.entities.rules import NodeEntity, NodeSpecEntity, SemanticType, NodeType, RuleStatus
from itapia_common.schemas.entities.performance import PerformanceMetrics

class NodeResponse(NodeSpecEntity):
    """Response schema for node specification entities."""
    pass

class RuleCreateRequest(BaseModel):
    """Schema for data INPUT when creating a new Rule."""
    
    rule_id: str = Field(..., min_length=3, description="Name or ID of this rule")
    name: str = Field(..., description="Plain text describe rule")
    description: str = Field(default="", description="Description what the rule do")
    purpose: SemanticType = Field(..., description="Purpose of this rule")
    
    # Root is received as a raw dictionary from JSON
    root: NodeEntity = Field(..., description="JSON structure of the logic tree")

class RuleResponse(BaseModel):
    """Schema for data OUTPUT after successfully creating a Rule."""
    
    rule_id: str
    name: str
    purpose: SemanticType
    rule_status: RuleStatus
    created_at_ts: int
    root: NodeEntity
    metrics: Optional[PerformanceMetrics] = Field(default=None)

    class Config:
        from_attributes = True
        
class ExplainationRuleResponse(RuleResponse):
    """Rule response with explanation."""
    
    explain: str