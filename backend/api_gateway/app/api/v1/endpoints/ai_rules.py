"""Rule endpoints that proxy requests to the AI Service."""

from typing import Literal
from fastapi import APIRouter
from app.clients.ai_rules import get_single_rule_explain, get_ready_rules, get_nodes

from itapia_common.schemas.api.rules import ExplainationRuleResponse, RuleResponse, NodeResponse, SemanticType, NodeType

router = APIRouter()

@router.get('/rules/{rule_id}/explain', 
            response_model=ExplainationRuleResponse, 
            tags=['AI Rules'],
            summary="Get explanation for a specific rule from AI Service")
async def get_ai_single_rule_explain(rule_id: str):
    """Get explanation for a specific rule from AI Service.
    
    Args:
        rule_id (str): ID of the rule to explain
        
    Returns:
        ExplainationRuleResponse: Rule with natural language explanation
    """
    report = await get_single_rule_explain(rule_id=rule_id)
    return report

@router.get('/rules', 
            response_model=list[RuleResponse], 
            tags=['AI Rules'],
            summary="Get list of ready rules from AI Service")
async def get_ai_ready_rules(purpose: SemanticType = SemanticType.ANY):
    """Get list of ready rules from AI Service.
    
    Args:
        purpose (SemanticType): Filter rules by purpose
        
    Returns:
        list[RuleResponse]: List of ready rules
    """
    report = await get_ready_rules(purpose)
    return report

@router.get('/rules/nodes', 
            response_model=list[NodeResponse], 
            tags=['AI Rules'],
            summary="Get list of available nodes from AI Service")
async def get_ai_nodes(node_type: NodeType = NodeType.ANY,
                       purpose: SemanticType = SemanticType.ANY):
    """Get list of available nodes from AI Service.
    
    Args:
        node_type (NodeType): Filter nodes by type
        purpose (SemanticType): Filter nodes by purpose
        
    Returns:
        list[NodeResponse]: List of available nodes
    """
    report = await get_nodes(node_type, purpose)
    return report