from typing import Literal
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from app.clients.ai_rules import get_single_rule_explain

from itapia_common.schemas.api.rules import ExplainationRuleResponse

router = APIRouter()

@router.get('/rules/{rule_id}/explain', response_model=ExplainationRuleResponse, tags=['AI Rules'])
async def get_ai_single_rule_explain(rule_id: str):
    report = await get_single_rule_explain(rule_id=rule_id)
    return report


