# api/v1/endpoints/rules.py
"""Rule endpoints for accessing and explaining trading rules."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse

from app.orchestrator import AIServiceQuickOrchestrator
from app.core.exceptions import NoDataError, MissingReportError, NotReadyServiceError
from app.dependencies import get_ceo_orchestrator

from itapia_common.schemas.api.rules import ExplainationRuleResponse, NodeResponse, RuleResponse
from itapia_common.schemas.entities.rules import NodeType, SemanticType

router = APIRouter()

@router.get("/rules/{rule_id}/explain", 
            response_model=ExplainationRuleResponse,
            summary="Get explanation for a specific rule",
            responses={
                404: {"description": "Rule not found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_single_explaination_rule(rule_id: str, 
                       orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator)):
    """Get explanation for a specific rule.
    
    Args:
        rule_id (str): ID of the rule to explain
        orchestrator (AIServiceQuickOrchestrator): Service orchestrator dependency
        
    Returns:
        ExplainationRuleResponse: Rule with natural language explanation
    """
    try:
        report = await orchestrator.get_single_explaination_rule(rule_id=rule_id)
        return ExplainationRuleResponse(
            rule_id=report.rule_id,
            name=report.name,
            purpose=report.purpose,
            rule_status=report.rule_status,
            created_at_ts=int(report.created_at.timestamp()),
            explain=report.explain,
            root=report.root,
            metrics=report.metrics,
        )
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)   
    
@router.get("/rules", 
            response_model=list[RuleResponse],
            summary="Get list of ready rules",
            responses={
                404: {"description": "No rules found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
async def get_ready_rules(purpose: SemanticType = SemanticType.ANY, 
                           orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator),
                           ):
    """Get list of ready rules.
    
    Args:
        purpose (SemanticType): Filter rules by purpose
        orchestrator (AIServiceQuickOrchestrator): Service orchestrator dependency
        
    Returns:
        list[RuleResponse]: List of ready rules
    """
    try:
        report = await orchestrator.get_ready_rules(purpose=purpose)
        return [RuleResponse(
            rule_id=rule.rule_id,
            name=rule.name,
            purpose=rule.purpose,
            rule_status=rule.rule_status,
            created_at_ts=int(rule.created_at.timestamp()),
            root=rule.root,
            metrics=rule.metrics,
        ) for rule in report]
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)   
    
@router.get("/rules/nodes", 
            response_model=list[NodeResponse],
            summary="Get list of available nodes",
            responses={
                404: {"description": "No nodes found"},
                500: {"description": "Internal analysis module failed"},
                503: {"description": "Service is not ready, still pre-warming caches"}
            }
)
def get_nodes(node_type: NodeType = NodeType.ANY,
                           purpose: SemanticType = SemanticType.ANY, 
                           orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator),
                           ):
    """Get list of available nodes.
    
    Args:
        node_type (NodeType): Filter nodes by type
        purpose (SemanticType): Filter nodes by purpose
        orchestrator (AIServiceQuickOrchestrator): Service orchestrator dependency
        
    Returns:
        list[NodeResponse]: List of available nodes
    """
    try:
        report = orchestrator.get_nodes(node_type, purpose)
        return [NodeResponse.model_validate(node.model_dump()) for node in report]
    except NoDataError as e1:
        raise HTTPException(status_code=404, detail=e1.msg)
    except MissingReportError as e2:
        raise HTTPException(status_code=500, detail=e2.msg)
    except NotReadyServiceError as e3:
        raise HTTPException(status_code=503, detail=e3.msg)   
    
