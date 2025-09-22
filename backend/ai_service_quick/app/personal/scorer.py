from abc import ABC, abstractmethod
import math
from itapia_common.schemas.entities.performance import NormalizedPerformanceMetrics, PerformanceMetrics, MetricDirection, NORMALIZATION_CONFIG
from itapia_common.schemas.entities.personal import QuantitivePreferencesConfig
from typing import Dict, Literal


def clip(value: float, lb: float = -float('inf'), ub: float = float("inf")):
    """Clip a value to stay within specified bounds.
    
    Args:
        value (float): The value to clip
        lb (float): Lower bound (inclusive)
        ub (float): Upper bound (inclusive)
        
    Returns:
        float: The clipped value
    """
    if lb >= ub:
        return value
    if value < lb:
        return lb
    if value > ub:
        return ub
    return value


class Scorer(ABC):
    """Abstract base class for scoring performance metrics."""
    
    @abstractmethod
    def score(self, metrics: PerformanceMetrics,
              quantitive_config: QuantitivePreferencesConfig) -> float:
        """Score performance metrics based on quantitative preferences.
        
        Args:
            metrics (PerformanceMetrics): Performance metrics to score
            quantitive_config (QuantitivePreferencesConfig): Quantitative preferences configuration
            
        Returns:
            float: Score for the metrics
        """
        pass
    

class WeightedSumScorer(Scorer):
    """Scorer that uses weighted sum approach to evaluate performance metrics."""
    
    def normalize(self, metrics: PerformanceMetrics):
        """Normalize performance metrics to 0-1 range.
        
        Args:
            metrics (PerformanceMetrics): Performance metrics to normalize
            
        Returns:
            NormalizedPerformanceMetrics: Normalized performance metrics
        """
        normalized = metrics.model_dump()
        for k, value in normalized.items():
            if k in NORMALIZATION_CONFIG.keys():
                config = NORMALIZATION_CONFIG[k]
                worst = config['worst']
                best = config['best']
                direction: MetricDirection = config['direction']
                
                if direction == 'lower_is_better':
                    value, worst, best = -value, -worst, -best
                    
                if best == worst:
                    normalized[k] = 0.5
                else:
                    normalized[k] = (value - worst) / (best - worst)

                normalized[k] = clip(normalized[k], 0, 1)
        
        return NormalizedPerformanceMetrics.model_validate(normalized)
    
    def score(self, metrics: PerformanceMetrics,
              quantitive_config: QuantitivePreferencesConfig) -> float:
        """Score performance metrics using weighted sum approach.
        
        Args:
            metrics (PerformanceMetrics): Performance metrics to score
            quantitive_config (QuantitivePreferencesConfig): Quantitative preferences configuration
            
        Returns:
            float: Weighted sum score for the metrics
        """
        weights = quantitive_config.weights
        normalized = self.normalize(metrics)
        
        normalized_dict = normalized.model_dump()
        weights_dict = weights.model_dump()
        
        personal_score = 0.0
        total_weight = 0.0
        
        # Calculate weighted sum of normalized values
        for name, weight in weights_dict.items():
            if weight > 0 and name in normalized_dict:
                personal_score += normalized_dict[name] * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.0
            
        return personal_score / total_weight
        