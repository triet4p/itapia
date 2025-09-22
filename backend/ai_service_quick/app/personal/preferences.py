"""Preferences manager for filtering and ranking rules based on user preferences."""

from typing import List, Tuple
from itapia_common.schemas.entities.performance import PerformanceHardConstraints, PerformanceMetrics
from itapia_common.schemas.entities.personal import QuantitivePreferencesConfig
from itapia_common.schemas.entities.rules import RuleEntity
from .scorer import Scorer


def sample_rules(scored_rules: List[Tuple[RuleEntity, float]], limit: int):
    """Sample rules evenly from a sorted list of scored rules.
    
    Args:
        scored_rules (List[Tuple[RuleEntity, float]]): List of rules with their scores, sorted by score
        limit (int): Maximum number of rules to return
        
    Returns:
        List[Tuple[RuleEntity, float]]: Sampled list of rules
    """
    n = len(scored_rules)
    if limit >= n:  # If limit is greater than number of rules, return all
        return scored_rules
    
    # Always ensure first and last indices are included
    indices = [0]
    
    # Calculate step to distribute evenly
    step = (n - 1) / (limit - 1)
    for i in range(1, limit - 1):
        idx = round(i * step)
        indices.append(idx)
    
    indices.append(n - 1)
    indices = sorted(set(indices))  # Avoid duplicates
    
    return [scored_rules[i] for i in indices]


class PreferencesManager:
    """Manager for handling user preferences in rule filtering and ranking."""
        
    def _fill_metrics_available(self, rules: List[RuleEntity]) -> List[RuleEntity]:
        """Fill missing metrics with default values.
        
        Args:
            rules (List[RuleEntity]): List of rules to process
            
        Returns:
            List[RuleEntity]: List of rules with metrics filled
        """
        filled_rules = []
        for rule_ent in rules:
            if rule_ent.metrics is None:
                # Assign default
                rule_ent.metrics = PerformanceMetrics()
            filled_rules.append(rule_ent)
        return filled_rules
                
    def _check_constraint(self, rule_ent: RuleEntity,
                          constraints: PerformanceHardConstraints) -> bool:
        """Check if a rule meets the hard constraints.
        
        Args:
            rule_ent (RuleEntity): Rule to check
            constraints (PerformanceHardConstraints): Constraints to apply
            
        Returns:
            bool: True if rule meets constraints, False otherwise
        """
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
        """Filter and rank rules based on quantitative preferences.
        
        Args:
            rules (List[RuleEntity]): List of rules to filter
            scorer (Scorer): Scorer to evaluate rules
            quantitive_config (QuantitivePreferencesConfig): Quantitative preferences configuration
            limit (int): Maximum number of rules to return
            
        Returns:
            List[RuleEntity]: Filtered and ranked list of rules
        """
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