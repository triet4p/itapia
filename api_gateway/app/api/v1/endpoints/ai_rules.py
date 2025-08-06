from typing import Literal
from fastapi import APIRouter
from app.clients.ai_rules import get_single_rule_explain, get_active_rules, get_nodes

from itapia_common.schemas.api.rules import ExplainationRuleResponse, RuleResponse, NodeResponse
from itapia_common.schemas.enums import SemanticType, NodeType

router = APIRouter()

@router.get('/rules/{rule_id}/explain', response_model=ExplainationRuleResponse, tags=['AI Rules'])
async def get_ai_single_rule_explain(rule_id: str):
    report = await get_single_rule_explain(rule_id=rule_id)
    return report

@router.get('/rules', response_model=list[RuleResponse], tags=['AI Rules'])
async def get_ai_active_rules(purpose: SemanticType = SemanticType.ANY):
    report = await get_active_rules(purpose)
    return report

@router.get('/rules/nodes', response_model=list[NodeResponse], tags=['AI Rules'])
async def get_ai_nodes(node_type: NodeType = NodeType.ANY,
                       purpose: SemanticType = SemanticType.ANY):
    report = await get_nodes(node_type, purpose)
    return report