from typing import List, Tuple
from itapia_common.dblib.services import RuleService
from itapia_common.schemas.entities.performance import PerformanceHardConstraints, PerformanceMetrics
from itapia_common.schemas.entities.personal import QuantitivePreferencesConfig
from itapia_common.schemas.entities.rules import RuleEntity, RuleStatus
from .scorer import Scorer

def sample_rules(scored_rules: List[Tuple[RuleEntity, float]], limit: int):
    n = len(scored_rules)
    if limit >= n:  # Nếu limit lớn hơn số rule thì lấy hết
        return scored_rules
    
    # Luôn đảm bảo lấy index 0 và index cuối
    indices = [0]
    
    # Tính step để chia đều
    step = (n - 1) / (limit - 1)
    for i in range(1, limit - 1):
        idx = round(i * step)
        indices.append(idx)
    
    indices.append(n - 1)
    indices = sorted(set(indices))  # tránh trùng lặp
    
    return [scored_rules[i] for i in indices]

class PreferencesManager:
        
    def _fill_metrics_available(self, rules: List[RuleEntity]) -> List[RuleEntity]:
        filled_rules = []
        for rule_ent in rules:
            if rule_ent.metrics is None:
                # Assign default
                rule_ent.metrics = PerformanceMetrics()
            filled_rules.append(rule_ent)
        return filled_rules
                
    def _check_constraint(self, rule_ent: RuleEntity,
                          constraints: PerformanceHardConstraints) -> bool:
        metrics_dict = rule_ent.metrics.model_dump()
        constraints_dict = constraints.model_dump()
        
        for k, metric in metrics_dict.items():
            if k not in constraints_dict:
                continue
            lb, ub = constraints_dict[k]
            
            if lb is not None and metric < lb:
                return False
            
            if ub is not None and metric > ub:
                return False
            
        return True
                
    def filter_rules(self, rules: List[RuleEntity], scorer: Scorer, 
                     quantitive_config: QuantitivePreferencesConfig,
                     limit: int = 10) -> List[RuleEntity]:
        if not rules:
            return []
        
        filled_rules = self._fill_metrics_available(rules)
        
        hard_constraints = quantitive_config.constraints
        eligible_rules: List[RuleEntity] = []
        for rule_ent in filled_rules:
            if self._check_constraint(rule_ent, hard_constraints):
                eligible_rules.append(rule_ent)
                
        if not eligible_rules:
            return []
        
        scored_rules: List[Tuple[RuleEntity, float]] = []
        for rule_ent in eligible_rules:
            personal_score = scorer.score(rule_ent.metrics, quantitive_config)
            scored_rules.append((rule_ent, personal_score))
            
        scored_rules.sort(key=lambda x: x[1], reverse=True)
        
        return [rule for rule, score in sample_rules(scored_rules, limit)]