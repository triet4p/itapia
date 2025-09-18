"""Aggregation orchestrator for combining and interpreting rule scores."""

from typing import List, Dict, Tuple

from itapia_common.rules.score import ScoreAggregator, ScoreFinalMapper
from itapia_common.schemas.entities.rules import SemanticType
from itapia_common.schemas.entities.advisor import AggregatedScoreInfo


class AggregationOrchestrator:
    """Responsible for aggregation operations and interpretation of score values."""
    
    def __init__(self):
        """Initialize the aggregation orchestrator with required components."""
        self.aggregator = ScoreAggregator()
        self.mapper = ScoreFinalMapper()

    def aggregate_raw_scores(
        self, 
        decision_scores: List[float], 
        risk_scores: List[float], 
        opportunity_scores: List[float]
    ) -> AggregatedScoreInfo:
        """Aggregate raw scores from rule sets.
        
        Args:
            decision_scores (List[float]): List of decision signal scores
            risk_scores (List[float]): List of risk assessment scores
            opportunity_scores (List[float]): List of opportunity rating scores
            
        Returns:
            AggregatedScoreInfo: Container with aggregated scores for each category
        """
        agg_decision = self.aggregator.average(decision_scores)
        agg_risk = self.aggregator.get_highest_score(risk_scores)
        agg_opportunity = self.aggregator.get_lowest_score(opportunity_scores)
        
        return AggregatedScoreInfo(
            raw_decision_score=agg_decision,
            raw_risk_score=agg_risk,
            raw_opportunity_score=agg_opportunity
        )

    def map_final_scores(self, final_scores: Dict[str, float]) -> Dict[str, Tuple[str, str]]:
        """Map final scores to meaningful labels.
        
        Args:
            final_scores (Dict[str, float]): Dictionary of final scores by semantic type
            
        Returns:
            Dict[str, Tuple[str, str]]: Mapping of semantic types to (label, recommendation) tuples
        """
        dec_desc = self.mapper.map(final_scores[SemanticType.DECISION_SIGNAL], SemanticType.DECISION_SIGNAL)
        risk_desc = self.mapper.map(final_scores[SemanticType.RISK_LEVEL], SemanticType.RISK_LEVEL)
        opp_desc = self.mapper.map(final_scores[SemanticType.OPPORTUNITY_RATING], SemanticType.OPPORTUNITY_RATING)

        return {
            SemanticType.DECISION_SIGNAL: dec_desc,
            SemanticType.RISK_LEVEL: risk_desc,
            SemanticType.OPPORTUNITY_RATING: opp_desc
        }