from typing import Dict, NamedTuple, Literal, Optional, Tuple
from abc import ABC, abstractmethod
import itapia_common.rules.names as nms
from itapia_common.rules.score import ScoreFinalMapper
from itapia_common.schemas.entities.rules import SemanticType 

ACTION_TYPE = Literal['BUY', 'SELL', 'HOLD']

class Action(NamedTuple):
    action_type: ACTION_TYPE
    # Tỉ lệ phần trăm vốn dùng cho action này
    position_size_pct: float = 1.0
    # Thời gian hold nếu ko có tín hiệu thoát khác
    duration_days: int = 365
    
    sl_pct: float = 1.0
    tp_pct: float = 1.0
    
    def __repr__(self):
        return f'Action(action_type={self.action_type}, position_size_pct={self.position_size_pct}, duration_days={self.duration_days}, sl_pct={self.sl_pct}, tp_pct={self.tp_pct})'

class _BaseActionMapper(ABC):
    @abstractmethod
    def map_action(self, score_final: float) -> Action:
        pass
        
class LinearDecisionActionMapper(_BaseActionMapper):
    
    DEFAULT_POSITION_SIZE_PCT_RANGE: Tuple[float, float] = (0.1, 0.9)
    DEFAULT_DURATION_DAYS_RANGE: Tuple[int, int] = (1, 90)
    DEFAULT_SL_PCT_RANGE: Tuple[float, float] = (0.02, 0.1)
    DEFAULT_TP_PCT_RANGE: Tuple[float, float] = (0.04, 0.3)
    MIN_BUY_THRESHOLD: float = 0.1
    MAX_SELL_THRESHOLD: float = -0.1 
    
    def __init__(self, position_size_pct_range: Optional[Tuple[float, float]] = None,
                 duration_days_range: Optional[Tuple[int, int]] = None,
                 sl_pct_range: Optional[Tuple[float, float]] = None,
                 tp_pct_range: Optional[Tuple[float, float]] = None,
                 min_buy_threshold: Optional[float] = None,
                 max_sell_threshold: Optional[float] = None):
        self.position_size_pct_range = position_size_pct_range if position_size_pct_range else self.DEFAULT_POSITION_SIZE_PCT_RANGE
        self.duration_days_range = duration_days_range if duration_days_range else self.DEFAULT_DURATION_DAYS_RANGE
        self.sl_pct_range = sl_pct_range if sl_pct_range else self.DEFAULT_SL_PCT_RANGE
        self.tp_pct_range = tp_pct_range if tp_pct_range else self.DEFAULT_TP_PCT_RANGE
        self.min_buy_threshold = min_buy_threshold if min_buy_threshold else self.MIN_BUY_THRESHOLD
        self.max_sell_threshold = max_sell_threshold if max_sell_threshold else self.MAX_SELL_THRESHOLD
        
    def map_action(self, score_final: float):
        action_type: ACTION_TYPE 
        if score_final > self.min_buy_threshold:
            action_type = 'BUY'
        elif score_final < self.max_sell_threshold:
            action_type = 'SELL'
        else:
            action_type = 'HOLD'
            
        if action_type == 'HOLD':
            return Action('HOLD')
            
        confidence = abs(score_final)
            
        position_size_pct = (self.position_size_pct_range[0]
                             + (self.position_size_pct_range[1] - 
                                self.position_size_pct_range[0]) * confidence)

        duration_days = (self.duration_days_range[1]
                         - (self.duration_days_range[1] 
                            - self.duration_days_range[0]) * confidence)
        
        sl_pct = (self.sl_pct_range[0] 
                  + (self.sl_pct_range[1] 
                     - self.sl_pct_range[0]) * confidence)
        
        tp_pct = (self.tp_pct_range[0] 
                  + (self.tp_pct_range[1] 
                     - self.tp_pct_range[0]) * confidence)
        
        return Action(action_type=action_type,
                      position_size_pct=position_size_pct,
                      duration_days=duration_days,
                      sl_pct=sl_pct,
                      tp_pct=tp_pct)
        
MEDIUM_SWING_IDEAL_MAPPER = LinearDecisionActionMapper(
    position_size_pct_range=[0.2, 0.9],
    duration_days_range=[25, 90],
    sl_pct_range=[0.07, 0.1],
    tp_pct_range=[0.21, 0.3],
    min_buy_threshold=0.05,
    max_sell_threshold=-0.02
)

MEDIUM_SWING_PESSIMISTIC_MAPPER = LinearDecisionActionMapper(
    position_size_pct_range=[0.2, 0.9],
    duration_days_range=[25, 90],
    sl_pct_range=[0.07, 0.1],
    tp_pct_range=[0.08, 0.12],
    min_buy_threshold=0.03,
    max_sell_threshold=-0.03
)

# Sau này các mapper cho risk, opportunity được triển khai riêng