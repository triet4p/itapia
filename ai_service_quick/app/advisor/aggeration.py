# ai_service_quick/app/advisor/aggregation_orc.py
from typing import List, Dict, Tuple

from itapia_common.rules.score import ScoreAggregator, ScoreFinalMapper
from itapia_common.schemas.enums import SemanticType
from itapia_common.schemas.entities.advisor import AggregatedScoreInfo

class AggregationOrchestrator:
    """
    Chịu trách nhiệm về các phép toán tổng hợp và diễn giải điểm số.
    """
    def __init__(self):
        self.aggregator = ScoreAggregator()
        self.mapper = ScoreFinalMapper()

    def aggregate_raw_scores(
        self, 
        decision_scores: List[float], 
        risk_scores: List[float], 
        opportunity_scores: List[float]
    ) -> AggregatedScoreInfo:
        """Tổng hợp các điểm số thô từ các bộ quy tắc."""
        agg_decision = self.aggregator.average(decision_scores)
        agg_risk = self.aggregator.get_highest_score(risk_scores)
        agg_opportunity = self.aggregator.get_lowest_score(opportunity_scores)
        
        return AggregatedScoreInfo(
            raw_decision_score=agg_decision,
            raw_risk_score=agg_risk,
            raw_opportunity_score=agg_opportunity
        )

    def synthesize_final_decision(
        self, 
        aggregated_scores: AggregatedScoreInfo, 
        weights: Dict[SemanticType, float]
    ) -> Dict[SemanticType, float]:
        """Thực thi logic tổng hợp cuối cùng có trọng số (Meta-Rule)."""
        final_decision = (aggregated_scores.raw_decision_score * weights.get(SemanticType.DECISION_SIGNAL, 1.0)) - \
                         (aggregated_scores.raw_risk_score * weights.get(SemanticType.RISK_LEVEL, 1.0)) + \
                         (aggregated_scores.raw_opportunity_score * weights.get(SemanticType.OPPORTUNITY_RATING, 1.0))
        
        # Trong MVP, rủi ro và cơ hội cuối cùng chính là điểm số thô đã tổng hợp
        final_risk = aggregated_scores.raw_risk_score
        final_opportunity = aggregated_scores.raw_opportunity_score
        
        return {
            SemanticType.DECISION_SIGNAL: max(-1.0, min(1.0, final_decision)),
            SemanticType.RISK_LEVEL: final_risk,
            SemanticType.OPPORTUNITY_RATING: final_opportunity
        }

    def map_final_scores(self, final_scores: Dict[str, float]):
        """ánh xạ các điểm số cuối cùng sang các nhãn có ý nghĩa."""
        dec_desc = self.mapper.map(final_scores[SemanticType.DECISION_SIGNAL], SemanticType.DECISION_SIGNAL)
        risk_desc = self.mapper.map(final_scores[SemanticType.RISK_LEVEL], SemanticType.RISK_LEVEL)
        opp_desc = self.mapper.map(final_scores[SemanticType.OPPORTUNITY_RATING], SemanticType.OPPORTUNITY_RATING)

        return {
            SemanticType.DECISION_SIGNAL: dec_desc,
            SemanticType.RISK_LEVEL: risk_desc,
            SemanticType.OPPORTUNITY_RATING: opp_desc
        }