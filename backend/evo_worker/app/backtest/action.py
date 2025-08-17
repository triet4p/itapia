from typing import Dict, NamedTuple, Literal
from abc import ABC
import itapia_common.rules.names as nms
from itapia_common.rules.score import ScoreFinalMapper
from itapia_common.schemas.enums import SemanticType 

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
    BASE_TP_SL_RATE: float = 2.0
    BASE_SL_PCT: float = 0.01
    MAPPER: Dict[str, Action] = {}
    def __init__(self):
        self.threshold_matcher = ScoreFinalMapper()
        
    def map_action(self, score_final: float, purpose: SemanticType) -> Action:
        if purpose != SemanticType.DECISION_SIGNAL:
            return Action(action_type='HOLD')

        threshold = self.threshold_matcher.match(purpose=purpose, score=score_final)
        return self.MAPPER.get(threshold.name, Action(action_type='HOLD'))
        
class ShortSwingActionMapper(_BaseActionMapper):
    MAPPER = {
        nms.THRESHOLD_DECISION_BUY_IMMEDIATE: Action(action_type='BUY', position_size_pct=0.9, duration_days=2, 
                                                     sl_pct=0.025, tp_pct=0.05),
        nms.THRESHOLD_DECISION_BUY_STRONG: Action(action_type='BUY', position_size_pct=0.8, duration_days=5, 
                                                  sl_pct=0.033, tp_pct=0.066),
        nms.THRESHOLD_DECISION_BUY_MODERATE: Action(action_type='BUY', position_size_pct=0.5, duration_days=10, 
                                                    sl_pct=0.04, tp_pct=0.08),
        nms.THRESHOLD_DECISION_ACCUMULATE: Action(action_type='BUY', position_size_pct=0.25, duration_days=15, 
                                                  sl_pct=0.045, tp_pct=0.09),
        
        nms.THRESHOLD_DECISION_REDUCE_POSITION: Action(action_type='SELL', position_size_pct=0.25, duration_days=15, 
                                                       sl_pct=0.045, tp_pct=0.09),
        nms.THRESHOLD_DECISION_SELL_MODERATE: Action(action_type='SELL', position_size_pct=0.45, duration_days=10, 
                                                     sl_pct=0.04, tp_pct=0.08),
        nms.THRESHOLD_DECISION_SELL_STRONG: Action(action_type='SELL', position_size_pct=0.7, duration_days=5, 
                                                   sl_pct=0.03, tp_pct=0.06),
        nms.THRESHOLD_DECISION_SELL_IMMEDIATE: Action(action_type='SELL', position_size_pct=0.9, duration_days=2, 
                                                      sl_pct=0.02, tp_pct=0.04),
    }
    
class MediumSwingActionMapper(_BaseActionMapper):
    MAPPER = {
        nms.THRESHOLD_DECISION_BUY_IMMEDIATE: Action(action_type='BUY', position_size_pct=0.9, duration_days=25, 
                                                     sl_pct=0.075, tp_pct=0.21),
        nms.THRESHOLD_DECISION_BUY_STRONG: Action(action_type='BUY', position_size_pct=0.75, duration_days=40, 
                                                  sl_pct=0.08, tp_pct=0.24),
        nms.THRESHOLD_DECISION_BUY_MODERATE: Action(action_type='BUY', position_size_pct=0.5, duration_days=60, 
                                                    sl_pct=0.088, tp_pct=0.264),
        nms.THRESHOLD_DECISION_ACCUMULATE: Action(action_type='BUY', position_size_pct=0.3, duration_days=90, 
                                                  sl_pct=0.1, tp_pct=0.3),
        
        nms.THRESHOLD_DECISION_REDUCE_POSITION: Action(action_type='SELL', position_size_pct=0.25, duration_days=85, 
                                                       sl_pct=0.1, tp_pct=0.3),
        nms.THRESHOLD_DECISION_SELL_MODERATE: Action(action_type='SELL', position_size_pct=0.45, duration_days=65, 
                                                     sl_pct=0.085, tp_pct=0.26),
        nms.THRESHOLD_DECISION_SELL_STRONG: Action(action_type='SELL', position_size_pct=0.7, duration_days=45, 
                                                   sl_pct=0.08, tp_pct=0.24),
        nms.THRESHOLD_DECISION_SELL_IMMEDIATE: Action(action_type='SELL', position_size_pct=0.9, duration_days=25, 
                                                      sl_pct=0.07, tp_pct=0.21),
    }
    
