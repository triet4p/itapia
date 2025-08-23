from typing import List, NamedTuple
from . import names as nms
from itapia_common.schemas.entities.rules import SemanticType


class FinalThreshold(NamedTuple):
    name: str
    value: float
    description: str
    purpose: SemanticType
    
# ===================================================================
# == A. Ngưỡng cho Tín hiệu Quyết định (Decision Signals)
# ===================================================================
DECISION_THRESHOLDS: List[FinalThreshold] = sorted([
    FinalThreshold(nms.THRESHOLD_DECISION_SELL_IMMEDIATE, -0.95, "Sell immediately with high confidence", SemanticType.DECISION_SIGNAL),
    FinalThreshold(nms.THRESHOLD_DECISION_SELL_STRONG, -0.8, "Strong indication to sell", SemanticType.DECISION_SIGNAL),
    FinalThreshold(nms.THRESHOLD_DECISION_SELL_MODERATE, -0.5, "Moderate indication to sell", SemanticType.DECISION_SIGNAL),
    FinalThreshold(nms.THRESHOLD_DECISION_REDUCE_POSITION, -0.3, "Consider reducing position/Take partial profit", SemanticType.DECISION_SIGNAL),
    FinalThreshold(nms.THRESHOLD_DECISION_HOLD_NEGATIVE, -0.1, "Hold but with caution, negative outlook", SemanticType.DECISION_SIGNAL),
    FinalThreshold(nms.THRESHOLD_DECISION_HOLD_NEUTRAL, 0.0, "Hold, no clear direction", SemanticType.DECISION_SIGNAL),
    FinalThreshold(nms.THRESHOLD_DECISION_HOLD_POSITIVE, 0.1, "Hold with positive outlook", SemanticType.DECISION_SIGNAL),
    FinalThreshold(nms.THRESHOLD_DECISION_ACCUMULATE, 0.3, "Accumulate/Buy on dips", SemanticType.DECISION_SIGNAL),
    FinalThreshold(nms.THRESHOLD_DECISION_BUY_MODERATE, 0.5, "Moderate indication to buy, consider confirming", SemanticType.DECISION_SIGNAL),
    FinalThreshold(nms.THRESHOLD_DECISION_BUY_STRONG, 0.8, "Strong indication to buy", SemanticType.DECISION_SIGNAL),
    FinalThreshold(nms.THRESHOLD_DECISION_BUY_IMMEDIATE, 0.95, "Buy immediately with high confidence", SemanticType.DECISION_SIGNAL),
], key=lambda x: x.value)

# ===================================================================
# == B. Ngưỡng cho Mức độ Rủi ro (Risk Levels)
# ===================================================================
RISK_THRESHOLDS: List[FinalThreshold] = sorted([
    FinalThreshold(nms.THRESHOLD_RISK_VERY_LOW, 0.1, "Very Low, suitable for capital preservation", SemanticType.RISK_LEVEL),
    FinalThreshold(nms.THRESHOLD_RISK_LOW, 0.3, "Low, conservative approach", SemanticType.RISK_LEVEL),
    FinalThreshold(nms.THRESHOLD_RISK_MODERATE, 0.5, "Moderate, balanced risk/reward", SemanticType.RISK_LEVEL),
    FinalThreshold(nms.THRESHOLD_RISK_HIGH, 0.8, "High, requires close monitoring", SemanticType.RISK_LEVEL),
    FinalThreshold(nms.THRESHOLD_RISK_VERY_HIGH, 0.95, "Very High, speculative", SemanticType.RISK_LEVEL),
], key=lambda x: x.value)

# ===================================================================
# == C. Ngưỡng cho Đánh giá Cơ hội (Opportunity Ratings)
# ===================================================================
OPPORTUNITY_THRESHOLDS: List[FinalThreshold] = sorted([
    FinalThreshold(nms.THRESHOLD_OPP_RATING_AVOID, 0.0, "Low potential, probably avoid", SemanticType.OPPORTUNITY_RATING),
    FinalThreshold(nms.THRESHOLD_OPP_RATING_NEUTRAL, 0.2, "Neutral, no special signal", SemanticType.OPPORTUNITY_RATING),
    FinalThreshold(nms.THRESHOLD_OPP_RATING_INTERESTING, 0.5, "Interesting, add to watchlist", SemanticType.OPPORTUNITY_RATING),
    FinalThreshold(nms.THRESHOLD_OPP_RATING_STRONG, 0.8, "A strong opportunity, worth investigating", SemanticType.OPPORTUNITY_RATING),
    FinalThreshold(nms.THRESHOLD_OPP_RATING_TOP_TIER, 0.95, "A top-tier opportunity, high conviction", SemanticType.OPPORTUNITY_RATING),
], key=lambda x: x.value)