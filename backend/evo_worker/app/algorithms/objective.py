from abc import ABC, abstractmethod
import math
from typing import Optional, Tuple, Union

import numpy as np
from itapia_common.schemas.entities.backtest import BacktestPerformanceMetrics

AcceptedObjective = Union[float, Tuple[float, ...]]

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

class ObjectiveExtractor(ABC):
    """Abstract base class for extracting objective values from backtest metrics."""
    
    @abstractmethod
    def extract(self, metrics: BacktestPerformanceMetrics) -> AcceptedObjective:
        """Extract objective values from backtest metrics.
        
        Args:
            metrics (BacktestPerformanceMetrics): Backtest performance metrics
            
        Returns:
            AcceptedObjective: Extracted objective values
        """
        pass
    
    @property
    @abstractmethod
    def default(self) -> AcceptedObjective:
        """Get the default objective values.
        
        Returns:
            AcceptedObjective: Default objective values
        """
        pass
    
class MultiObjectiveExtractor(ObjectiveExtractor):
    """Abstract base class for extracting multiple objective values."""
    
    @abstractmethod
    def extract(self, metrics: BacktestPerformanceMetrics) -> Tuple[float, ...]:
        """Extract multiple objective values from backtest metrics.
        
        Args:
            metrics (BacktestPerformanceMetrics): Backtest performance metrics
            
        Returns:
            Tuple[float, ...]: Extracted objective values as a tuple
        """
        pass
    
    @property
    @abstractmethod
    def default(self) -> Tuple[float, ...]:
        """Get the default objective values.
        
        Returns:
            Tuple[float, ...]: Default objective values as a tuple
        """
        pass
    
class SingleObjectiveExtractor(ObjectiveExtractor):
    """Abstract base class for extracting a single objective value."""
    
    @abstractmethod
    def extract(self, metrics: BacktestPerformanceMetrics) -> float:
        """Extract a single objective value from backtest metrics.
        
        Args:
            metrics (BacktestPerformanceMetrics): Backtest performance metrics
            
        Returns:
            float: Extracted objective value
        """
        pass
    
    @property
    def default(self) -> float:
        """Get the default objective value.
        
        Returns:
            float: Default objective value (0.0)
        """
        return 0.0
    
class CSRSPObjectiveExtractor(MultiObjectiveExtractor):
    """Multi-objective extractor for CAGR, Sortino Ratio, Resilience, Stability, and Profit Factor.
    
    A tuple with:
    
    C: CAGR
    S: Sortino Ratio
    R: Resilience
    S: Stability
    P: Profit factor
    """
        
    @property
    def default(self) -> Tuple[float, float, float, float, float]:
        """Get the default objective values.
        
        Returns:
            Tuple[float, float, float, float, float]: Default objective values (all 0.0)
        """
        return tuple([0.0] * 5)
    
    def extract(self, metrics: BacktestPerformanceMetrics) -> Tuple[float, float, float, float, float]:
        """Extract CSRSP objectives from backtest metrics.
        
        Args:
            metrics (BacktestPerformanceMetrics): Backtest performance metrics
            
        Returns:
            Tuple[float, float, float, float, float]: Tuple of (CAGR, Sortino Ratio, Resilience, Stability, Profit Factor)
        """
        # Base case: Rule produces no trades
        # Return the worst possible result for all objectives
        if metrics.num_trades == 0:
            return self.default
            
        obj_cagr = clip(metrics.cagr, lb=-1.0)
        obj_sortino_ratio = clip(metrics.sortino_ratio, lb=0.0, ub=15.0)
        obj_resilience = 1.0 - metrics.max_drawdown_pct
        
        if metrics.profit_factor >= 1:
            obj_profit_factor = clip((metrics.profit_factor - 1.0) / 2.0, ub=1.5)
        else:
            obj_profit_factor = metrics.profit_factor - 1.0
        
        obj_stability = 1.0 / (1.0 + metrics.annual_return_stability)

        # Return a tuple containing objective values in a fixed order
        # The NSGA-II algorithm will use this tuple to compare rules
        objectives = (
            obj_cagr,
            obj_sortino_ratio,
            obj_resilience,
            obj_stability,
            obj_profit_factor
        )
        
        # Ensure all values are finite numbers
        if not all(np.isfinite(obj) for obj in objectives):
            # If there's an error (e.g., profit_factor is inf), return the worst tuple
            return self.default
            
        return objectives
    
class CSPSPWeightedAggObjectiveExtractor(SingleObjectiveExtractor):
    """Single objective extractor that aggregates CSPSP metrics with weights."""
    
    def __init__(self, weights: Tuple[float, float, float, float, float]):
        """Initialize the weighted aggregator.
        
        Args:
            weights (Tuple[float, float, float, float, float]): Weights in order (CAGR, Sortino, Resilience, Stability, Profit Factor)
        """
        self.weights = weights
        
    def extract(self, metrics: BacktestPerformanceMetrics) -> float:
        """Extract and aggregate objective values from backtest metrics.
        
        Args:
            metrics (BacktestPerformanceMetrics): Backtest performance metrics
            
        Returns:
            float: Weighted aggregate of all objective values
        """
        objectives: float = 0.0
        total_weights: float = 0.0
        weights = self.weights
        total_weights = sum(weights)
        
        obj_cagr = clip(metrics.cagr, lb=-1.0)
        objectives += obj_cagr * weights[0]

        obj_sortino_ratio = clip(metrics.sortino_ratio, lb=0.0, ub=15.0)
        objectives += obj_sortino_ratio * weights[1]
        
        obj_resilience = 1.0 - metrics.max_drawdown_pct
        objectives += obj_resilience * weights[2]
        
        obj_stability = 1.0 / (1.0 + metrics.annual_return_stability)
        objectives += obj_stability * weights[3]
        
        if metrics.profit_factor >= 1:
            obj_profit_factor = clip((metrics.profit_factor - 1.0) / 2.0, ub=1.5)
        else:
            obj_profit_factor = metrics.profit_factor - 1.0
        objectives += obj_profit_factor * weights[4]
        
        return objectives / total_weights
        