"""Rules orchestrator for managing and executing common rules from the database."""

import math
from typing import List, Callable, Literal, Tuple, Union

from app.core.exceptions import NoDataError

from itapia_common.rules.rule import Rule
from itapia_common.rules.nodes.registry import get_nodes_by_type
from itapia_common.schemas.entities.rules import ExplainationRuleEntity, RuleEntity, RuleStatus, SemanticType, NodeType
from itapia_common.dblib.services.rules import RuleService
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport
from itapia_common.schemas.entities.advisor import TriggeredRuleInfo

from .explainer import RuleExplainerOrchestrator


class RulesOrchestrator:
    """Responsible for retrieving and executing "common" (built-in, public) rules from the database."""
    
    def __init__(self, rule_service: RuleService,
                 explainer: RuleExplainerOrchestrator):
        """Initialize the rules orchestrator with required services.
        
        Args:
            rule_service (RuleService): Service for accessing rules in database
            explainer (RuleExplainerOrchestrator): Rule explainer service
        """
        self.rule_service = rule_service
        self.explainer = explainer

    async def run_for_purpose(
        self, 
        report: QuickCheckAnalysisReport, 
        purpose: SemanticType,
        rule_entities: List[RuleEntity]
    ) -> Tuple[List[float], List[TriggeredRuleInfo]]:
        """Retrieve, filter, and execute common rules for a specific purpose.
        
        Args:
            report (QuickCheckAnalysisReport): Analysis report to run rules against
            purpose (SemanticType): Semantic purpose to filter rules by
            rule_selector (Callable[[List[Rule]], List[Rule]]): Function to select rules
            
        Returns:
            Tuple[List[float], List[TriggeredRuleInfo]]: Tuple of scores and triggered rules
        """
        # Retrieve all active rules from DB
        all_rules_schemas = rule_entities
        all_rules = [Rule.from_entity(rs) for rs in all_rules_schemas]
        
        # Apply selection logic (can be personalized)
        selected_rules = all_rules
        
        scores: List[float] = []
        triggered_rules: List[TriggeredRuleInfo] = []
        for rule in selected_rules:
            score = rule.execute(report)
            scores.append(score)
            triggered_rules.append(TriggeredRuleInfo(
                rule_id=rule.rule_id, 
                name=rule.name, 
                score=score, 
                purpose=purpose.name
            ))
        return scores, triggered_rules
    
    def run_single_rule(
        self,
        report: QuickCheckAnalysisReport,
        rule: Rule
    ) -> Tuple[float, TriggeredRuleInfo]:
        """Execute a single rule against an analysis report.
        
        Args:
            report (QuickCheckAnalysisReport): Analysis report to run rule against
            rule (Rule): Rule to execute
            
        Returns:
            Tuple[float, TriggeredRuleInfo]: Score and triggered rule information
        """
        score = rule.execute(report)
        trigger_rule = TriggeredRuleInfo(
            rule_id=rule.rule_id, 
            name=rule.name, 
            score=score, 
            purpose=rule.purpose
        )
        
        return score, trigger_rule
    
    def run_personal_rules(self, report: QuickCheckAnalysisReport, 
            personal_rules: List[Rule], 
            purpose: SemanticType) -> Tuple[List[float], List[TriggeredRuleInfo]]:
        """[PLACEHOLDER] Execute personal rules for a specific purpose.
        
        Args:
            report (QuickCheckAnalysisReport): Analysis report to run rules against
            personal_rules (List[Rule]): List of personal rules to execute
            purpose (SemanticType): Semantic purpose to filter rules by
            
        Returns:
            Tuple[List[float], List[TriggeredRuleInfo]]: Tuple of scores and triggered rules
        """
        # Full execution logic will be added here in the future.
        # It will be similar to the logic in `RulesOrchestrator.run`.
        
        if not personal_rules:
            return [], []

        scores: List[float] = []
        triggered_rules: List[TriggeredRuleInfo] = []
        
        # Filter personal rules by correct purpose
        rules_for_purpose = [rule for rule in personal_rules if rule.purpose == purpose]

        for rule in rules_for_purpose:
            score = rule.execute(report)
            scores.append(score)
            if not math.isclose(score, 0.0):
                 triggered_rules.append(TriggeredRuleInfo(
                     rule_id=f"PERSONAL_{rule.rule_id}",  # Add prefix to differentiate
                     name=rule.name, 
                     score=score, 
                     purpose=purpose.name
                 ))
        return scores, triggered_rules
        
    
    def get_single_rule(self, rule_id: str) -> RuleEntity:
        """Retrieve a single rule by its ID.
        
        Args:
            rule_id (str): Unique identifier for the rule
            
        Returns:
            Rule: Retrieved rule object
            
        Raises:
            ValueError: If no rule is found with the given ID
        """
        rule_entity = self.rule_service.get_rule_by_id(rule_id)
        if rule_entity is None:
            raise ValueError(f'Not found rule with id {rule_id}')
        return rule_entity
    
    async def get_explaination_for_single_rule(self, rule_id: str) -> ExplainationRuleEntity:
        """Get explanation for a single rule by its ID.
        
        Args:
            rule_id (str): Unique identifier for the rule
            
        Returns:
            ExplainationRuleEntity: Rule explanation entity
            
        Raises:
            NoDataError: If no data is found for the rule
        """
        # <<< CHANGE: This function should be async because `rules_orc.get_single_rule` accesses DB
        try:
            # Assume get_single_rule is a coroutine
            rule = self.get_single_rule(rule_id)
            
            explanation = self.explainer.explain_rule(Rule.from_entity(rule))
            
            # Use model_dump() instead of **rule.to_dict() for safer Pydantic handling
            entity = ExplainationRuleEntity(
                explain=explanation,
                **rule.model_dump()
            )
            return entity
        except ValueError as e:
            raise NoDataError(f'Not found data for rule {rule_id}')
        
    def get_nodes(self, node_type: NodeType = NodeType.ANY, 
                  purpose: SemanticType = SemanticType.ANY) -> List:
        """Get nodes by type and purpose.
        
        Args:
            node_type (NodeType, optional): Type of nodes to retrieve. Defaults to NodeType.ANY.
            purpose (SemanticType, optional): Purpose to filter by. Defaults to SemanticType.ANY.
            
        Returns:
            List: List of nodes matching criteria
        """
        return get_nodes_by_type(node_type, purpose)
    
    async def get_ready_rules(self, purpose: SemanticType) -> List[RuleEntity]:
        """Get all ready rules for a specific purpose.
        
        Args:
            purpose (SemanticType): Purpose to filter rules by
            
        Returns:
            List: List of ready rules
            
        Raises:
            NoDataError: If no active rules are found
        """
        if purpose != SemanticType.ANY:
            rule_entities = self.rule_service.get_rules_by_purpose(purpose, RuleStatus.READY)
        else:
            rule_entities = self.rule_service.get_all_rules(RuleStatus.READY)
        if rule_entities is None:
            raise NoDataError(f'No rules is actived!')
        return rule_entities