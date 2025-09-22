from abc import ABC, abstractmethod
from typing import Tuple, Union

import numpy as np
from itapia_common.schemas.entities.performance import PerformanceMetrics

AcceptedObjective = Union[float, Tuple[float, ...]]
AcceptedObjectiveName = Union[str, Tuple[str, ...]]


def clip(value: float, lb: float = -float("inf"), ub: float = float("inf")):
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

    DEFAULT: AcceptedObjective = None
    OBJ_NAMES: AcceptedObjectiveName = None

    @abstractmethod
    def extract(self, metrics: PerformanceMetrics) -> AcceptedObjective:
        """Extract objective values from backtest metrics.

        Args:
            metrics (BacktestPerformanceMetrics): Backtest performance metrics

        Returns:
            AcceptedObjective: Extracted objective values
        """


class MultiObjectiveExtractor(ObjectiveExtractor):
    """Abstract base class for extracting multiple objective values."""

    DEFAULT: Tuple[float, ...] = ()
    OBJ_NAMES: Tuple[str, ...] = ()
    NUM_OBJS: int = 0

    @abstractmethod
    def extract(self, metrics: PerformanceMetrics) -> Tuple[float, ...]:
        """Extract multiple objective values from backtest metrics.

        Args:
            metrics (BacktestPerformanceMetrics): Backtest performance metrics

        Returns:
            Tuple[float, ...]: Extracted objective values as a tuple
        """


class SingleObjectiveExtractor(ObjectiveExtractor):
    """Abstract base class for extracting a single objective value."""

    DEFAULT: float = 0.0
    OBJ_NAMES: str = "obj"

    @abstractmethod
    def extract(self, metrics: PerformanceMetrics) -> float:
        """Extract a single objective value from backtest metrics.

        Args:
            metrics (BacktestPerformanceMetrics): Backtest performance metrics

        Returns:
            float: Extracted objective value
        """


class CSRSPObjectiveExtractor(MultiObjectiveExtractor):
    """Multi-objective extractor for CAGR, Sortino Ratio, Resilience, Stability, and Profit Factor.

    A tuple with:

    C: CAGR
    S: Sortino Ratio
    R: Resilience
    S: Stability
    P: Profit factor
    """

    DEFAULT: Tuple[float, float, float, float, float] = [0.0] * 5
    NUM_OBJS: int = 5
    OBJ_NAMES: Tuple[str, str, str, str, str] = (
        "cagr",
        "sortino_ratio",
        "resilience",
        "stability",
        "profit_factor",
    )

    def extract(
        self, metrics: PerformanceMetrics
    ) -> Tuple[float, float, float, float, float]:
        """Extract CSRSP objectives from backtest metrics.

        Args:
            metrics (BacktestPerformanceMetrics): Backtest performance metrics

        Returns:
            Tuple[float, float, float, float, float]: Tuple of (CAGR, Sortino Ratio, Resilience, Stability, Profit Factor)
        """
        # Base case: Rule produces no trades
        # Return the worst possible result for all objectives
        if metrics.num_trades == 0:
            return self.DEFAULT

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
            obj_profit_factor,
        )

        # Ensure all values are finite numbers
        if not all(np.isfinite(obj) for obj in objectives):
            # If there's an error (e.g., profit_factor is inf), return the worst tuple
            return self.DEFAULT

        return objectives


class CSPSPWeightedAggObjectiveExtractor(SingleObjectiveExtractor):
    """Single objective extractor that aggregates CSPSP metrics with weights."""

    def __init__(self, weights: Tuple[float, float, float, float, float]):
        """Initialize the weighted aggregator.
        You can see `CSRSPObjectiveExtractor.OBJ_NAMES` to ensure weight order.

        Args:
            weights (Tuple[float, float, float, float, float]): Weights in order (CAGR, Sortino, Resilience, Stability, Profit Factor)
        """
        self.weights = weights

    def extract(self, metrics: PerformanceMetrics) -> float:
        """Extract and aggregate objective values from backtest metrics.

        Args:
            metrics (BacktestPerformanceMetrics): Backtest performance metrics

        Returns:
            float: Weighted aggregate of all objective values
        """
        if metrics.num_trades == 0:
            return self.DEFAULT
        objectives: float = self.DEFAULT
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
