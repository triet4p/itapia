from abc import ABC, abstractmethod
import math
from typing import Optional, Tuple, Union

import numpy as np
from itapia_common.schemas.entities.backtest import BacktestPerformanceMetrics, BacktestPerformanceWeights

AcceptedObjective = Union[float, Tuple[float, ...]]

class ObjectiveExtractor(ABC):
    
    @abstractmethod
    def extract(self, metrics: BacktestPerformanceMetrics) -> AcceptedObjective:
        pass
    
    @property
    @abstractmethod
    def default(self) -> AcceptedObjective:
        pass
    
class MultiObjectiveExtractor(ObjectiveExtractor):
    
    @abstractmethod
    def extract(self, metrics: BacktestPerformanceMetrics) -> Tuple[float, ...]:
        pass
    
    @property
    @abstractmethod
    def default(self) -> Tuple[float, ...]:
        pass
    
class SingleObjectiveExtractor(ObjectiveExtractor):
    @abstractmethod
    def extract(self, metrics: BacktestPerformanceMetrics) -> float:
        pass
    
    @property
    def default(self) -> float:
        return 0.0
    
class CSRSPObjectiveExtractor(MultiObjectiveExtractor):
    """
    A tuple with:
    
    C: CAGR
    S: Sortino Ratio
    R: Resilience
    S: Stability
    P: Profit factor
    
    """
        
    @property
    def default(self) -> Tuple[float, float, float, float, float]:
        return tuple([0.0] * 5)
    
    def extract(self, metrics: BacktestPerformanceMetrics) -> Tuple[float, float, float, float, float]:
        # --- Trường hợp cơ sở: Rule không tạo ra giao dịch nào ---
        # Trả về kết quả tệ nhất có thể cho tất cả các mục tiêu.
        
        if metrics.num_trades == 0:
            return self.default
        obj_cagr = max(-1.0, metrics.cagr)

        obj_sortino_ratio = max(0.0, metrics.sortino_ratio)
        
        obj_resilience = 1.0 - metrics.max_drawdown_pct
        
        if metrics.profit_factor >= 1:
            obj_profit_factor = min(1.0, (metrics.profit_factor - 1.0) / 2.0)
        else:
            obj_profit_factor = metrics.profit_factor - 1.0
        
        obj_stability = 1.0 / (1.0 + metrics.annual_return_stability)

        # Trả về một tuple chứa các giá trị mục tiêu theo một thứ tự cố định.
        # Thuật toán NSGA-II sẽ sử dụng tuple này để so sánh các rule.
        objectives = (
            obj_cagr,
            obj_sortino_ratio,
            obj_resilience,
            obj_stability,
            obj_profit_factor
        )
        
        # Đảm bảo tất cả các giá trị đều là số hữu hạn
        if not all(np.isfinite(obj) for obj in objectives):
            # Nếu có lỗi (ví dụ: profit_factor là inf), trả về tuple tệ nhất
            return self.default
            
        return objectives
    
class WeightedAggObjectiveExtractor(SingleObjectiveExtractor):
    def __init__(self, weights: BacktestPerformanceWeights):
        self.weights = weights
        
    def extract(self, metrics: BacktestPerformanceMetrics):
        objectives: float = 0.0
        total_weights: float = 0.0
        weights = self.weights
        
        obj_cagr = max(-1.0, metrics.cagr)
        weight_cagr = weights.cagr
        objectives += obj_cagr * weight_cagr
        total_weights += weight_cagr

        obj_sortino_ratio = max(0.0, metrics.sortino_ratio)
        weight_sortino_ratio = weights.sortino_ratio
        objectives += obj_sortino_ratio * weight_sortino_ratio
        total_weights += weight_sortino_ratio
        
        obj_resilience = 1.0 - metrics.max_drawdown_pct
        weight_resilience = weights.max_drawdown_pct
        objectives += obj_resilience * weight_resilience
        total_weights += weight_resilience
        
        if metrics.profit_factor >= 1:
            obj_profit_factor = min(1.0, (metrics.profit_factor - 1.0) / 2.0)
        else:
            obj_profit_factor = metrics.profit_factor - 1.0
        weight_profit_factor = weights.profit_factor
        objectives += obj_profit_factor * weight_profit_factor
        total_weights += weight_profit_factor
        
        obj_stability = 1.0 / (1.0 + metrics.annual_return_stability)
        weight_stability = weights.annual_return_stability
        objectives += obj_stability * weight_stability
        total_weights += weight_stability
        
        return objectives / total_weights
        