from typing import Literal
from fastapi import HTTPException
import httpx
from app.core.config import AI_SERVICE_QUICK_BASE_URL

from itapia_common.schemas.api.rules import ExplainationRuleResponse, NodeResponse, RuleResponse, NodeType, SemanticType

ai_rules_client = httpx.AsyncClient(base_url=AI_SERVICE_QUICK_BASE_URL, timeout=10.0)

async def get_single_rule_explain(rule_id: str) -> ExplainationRuleResponse:
    try:
        print(f'Get for url {ai_rules_client.base_url}/rules/{rule_id}/explain')
        response = await ai_rules_client.get(f"/rules/{rule_id}/explain", params={
        })
        response.raise_for_status()
        return ExplainationRuleResponse.model_validate(response.json())
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail") or "Unknown error from AI Service"
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        # Xử lý lỗi kết nối
        raise HTTPException(status_code=503, detail=f"AI Service is unavailable: {type(e).__name__}")
    
async def get_ready_rules(purpose: SemanticType = SemanticType.ANY) -> list[RuleResponse]:
    try:
        print(f'Get for url {ai_rules_client.base_url}/rules')
        response = await ai_rules_client.get(f"/rules", params={
            "purpose": purpose.value
        })
        response.raise_for_status()
        return [RuleResponse.model_validate(res_ele) for res_ele in response.json()]
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail") or "Unknown error from AI Service"
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        # Xử lý lỗi kết nối
        raise HTTPException(status_code=503, detail=f"AI Service is unavailable: {type(e).__name__}")
    
async def get_nodes(node_type: NodeType, purpose: SemanticType = SemanticType.ANY) -> list[NodeResponse]:
    try:
        print(f'Get for url {ai_rules_client.base_url}/rules/nodes')
        response = await ai_rules_client.get(f"/rules/nodes", params={
            "purpose": purpose.value,
            "node_type": node_type.value
        })
        response.raise_for_status()
        return [NodeResponse.model_validate(res) for res in response.json()]
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail") or "Unknown error from AI Service"
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        # Xử lý lỗi kết nối
        raise HTTPException(status_code=503, detail=f"AI Service is unavailable: {type(e).__name__}")