# ai_service_quick/app/advisor/rules_orc.py
import math
from typing import List, Callable, Literal, Tuple, Union

from app.core.exceptions import NoDataError

from itapia_common.rules.rule import Rule
from itapia_common.rules.nodes.registry import get_nodes_by_type
from itapia_common.schemas.entities.rules import ExplainationRuleEntity
from itapia_common.schemas.enums import SemanticType, NodeType
from itapia_common.dblib.services.rules import RuleService
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport
from itapia_common.schemas.entities.advisor import TriggeredRuleInfo

from .explainer import RuleExplainerOrchestrator

class RulesOrchestrator:
    """
    Chịu trách nhiệm lấy và thực thi các quy tắc "chung" (built-in, public) từ CSDL.
    """
    def __init__(self, rule_service: RuleService,
                 explainer: RuleExplainerOrchestrator):
        self.rule_service = rule_service
        self.explainer = explainer

    async def run_for_purpose(
        self, 
        report: QuickCheckAnalysisReport, 
        purpose: SemanticType,
        rule_selector: Callable[[List[Rule]], List[Rule]]
    ):
        """
        Lấy, chọn lọc, và thực thi các quy tắc chung cho một mục đích cụ thể.
        """
        # Lấy tất cả quy tắc đang hoạt động từ DB
        all_rules_schemas = self.rule_service.get_active_rules_by_purpose(purpose)
        all_rules = [Rule.from_entity(rs) for rs in all_rules_schemas]
        
        # Áp dụng logic lựa chọn (có thể được cá nhân hóa)
        selected_rules = rule_selector(all_rules)
        
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
    ):
        score = rule.execute(report)
        triggle_rule = TriggeredRuleInfo(
            rule_id=rule.rule_id, 
            name=rule.name, 
            score=score, 
            purpose=rule.purpose
        )
        
        return score, triggle_rule
    
    def run_personal_rules(self, report: QuickCheckAnalysisReport, 
            personal_rules: List[Rule], 
            purpose: SemanticType) -> Tuple[List[float], List[TriggeredRuleInfo]]:
        """
        [PLACEHOLDER] Thực thi các quy tắc cá nhân cho một mục đích cụ thể.
        """
        # Logic thực thi đầy đủ sẽ được thêm vào đây trong tương lai.
        # Nó sẽ gần giống với logic trong `RulesOrchestrator.run`.
        
        if not personal_rules:
            return [], []

        scores: List[float] = []
        triggered_rules: List[TriggeredRuleInfo] = []
        
        # Lọc các quy tắc cá nhân theo đúng mục đích
        rules_for_purpose = [rule for rule in personal_rules if rule.purpose == purpose]

        for rule in rules_for_purpose:
            score = rule.execute(report)
            scores.append(score)
            if not math.isclose(score, 0.0):
                 triggered_rules.append(TriggeredRuleInfo(
                     rule_id=f"PERSONAL_{rule.rule_id}", # Thêm prefix để phân biệt
                     name=rule.name, 
                     score=score, 
                     purpose=purpose.name
                 ))
        return scores, triggered_rules
        
    
    def get_single_rule(self, rule_id: str) -> Rule:
        rule_entity = self.rule_service.get_rule_by_id(rule_id)
        if rule_entity is None:
            raise ValueError(f'Not found rule with id {rule_id}')
        return Rule.from_entity(rule_entity)
    
    async def get_explaination_for_single_rule(self, rule_id: str) -> ExplainationRuleEntity:
        # <<< THAY ĐỔI: Hàm này nên là async vì `rules_orc.get_single_rule` truy cập DB
        try:
            # Giả định get_single_rule là một coroutine
            rule = self.get_single_rule(rule_id)
            
            explanation = self.explainer.explain_rule(rule)
            
            # Sử dụng model_dump() thay vì **rule.to_dict() để an toàn hơn với Pydantic
            entity = ExplainationRuleEntity(
                explain=explanation,
                **rule.to_entity().model_dump()
            )
            return entity
        except ValueError as e:
            raise NoDataError(f'Not found data for rule {rule_id}')
        
    def get_nodes(self, node_type: NodeType = NodeType.ANY, 
                  purpose: SemanticType = SemanticType.ANY):
        return get_nodes_by_type(node_type, purpose)
    
    async def get_active_rules(self, purpose: SemanticType):
        if purpose != SemanticType.ANY:
            rule_entites = self.rule_service.get_active_rules_by_purpose(purpose)
        else:
            rule_entites = self.rule_service.get_all_active_rules()
        if rule_entites is None:
            raise NoDataError(f'No rules is actived!')
        return rule_entites