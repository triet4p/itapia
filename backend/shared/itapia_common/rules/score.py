# itapia_common/rules/score.py

"""
This module contains classes responsible for aggregating and interpreting
raw scores from rule sets.
"""

from typing import Dict, List, Tuple

from itapia_common.schemas.entities.rules import SemanticType

# Import threshold definitions from the file we just created
from .final_thresholds import (
    DECISION_THRESHOLDS,
    OPPORTUNITY_THRESHOLDS,
    RISK_THRESHOLDS,
    FinalThreshold,
)


class ScoreAggregator:
    """Performs logic to aggregate a list of raw scores into a single score.
    This class is unaware of purpose, it only performs mathematical operations.
    """

    def average(self, scores: List[float]) -> float:
        """Calculate the arithmetic mean of the scores.

        Args:
            scores (List[float]): List of scores to average.

        Returns:
            float: The arithmetic mean of the scores, or 0.0 if empty.
        """
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def weighted_average(self, scores: List[float], weights: List[float]) -> float:
        """Calculate the weighted average.

        Args:
            scores (List[float]): List of scores to average.
            weights (List[float]): List of weights for each score.

        Returns:
            float: The weighted average of the scores, or 0.0 if empty.

        Raises:
            ValueError: If the number of scores and weights are not equal.
        """
        if not scores:
            return 0.0
        if len(scores) != len(weights):
            raise ValueError("The number of scores and weights must be equal.")

        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        total_weight = sum(weights)

        if total_weight == 0:
            return 0.0
        return weighted_sum / total_weight

    def get_max_score(self, scores: List[float]) -> float:
        """Get the score with the largest absolute value, preserving the sign.

        Args:
            scores (List[float]): List of scores to evaluate.

        Returns:
            float: The score with the largest absolute value, or 0.0 if empty.
        """
        if not scores:
            return 0.0
        return max(scores, key=abs)

    def get_highest_score(self, scores: List[float]) -> float:
        """Get the highest score (useful for Risk and Opportunity).

        Args:
            scores (List[float]): List of scores to evaluate.

        Returns:
            float: The highest score, or 0.0 if empty.
        """
        if not scores:
            return 0.0
        return max(scores)

    def get_lowest_score(self, scores: List[float]) -> float:
        """Get the lowest score.

        Args:
            scores (List[float]): List of scores to evaluate.

        Returns:
            float: The lowest score, or 0.5 if empty.
        """
        if not scores:
            return 0.5
        return min(scores)


class ScoreFinalMapper:
    """Maps a final (aggregated) score to a human-readable conclusion label
    based on predefined thresholds.
    """

    FINAL_MAPPER_TEMPLATE = "Threshold match is {name}, which mean {description}."

    def __init__(self):
        """Initialize the mapper with threshold mappings for different purposes."""
        # Create a map from purpose to corresponding threshold set for easy lookup
        self._threshold_map: Dict[SemanticType, List[FinalThreshold]] = {
            SemanticType.DECISION_SIGNAL: DECISION_THRESHOLDS,
            SemanticType.RISK_LEVEL: RISK_THRESHOLDS,
            SemanticType.OPPORTUNITY_RATING: OPPORTUNITY_THRESHOLDS,
        }

    def map(self, score: float, purpose: SemanticType) -> Tuple[str, str]:
        """Perform the main mapping logic.

        Args:
            score (float): The final score to be interpreted.
            purpose (SemanticType): The purpose of the score, to select the correct threshold set.

        Returns:
            Tuple[str, str]: A tuple containing (identifier name, full description string).
                             Example: ('THRESHOLD_DECISION_BUY_STRONG', 'Strong indication to buy')

        Raises:
            ValueError: If no threshold set is found for the given purpose.
        """
        thresholds = self._threshold_map.get(purpose)

        if thresholds is None:
            raise ValueError(f"No threshold set found for purpose: {purpose.name}")

        # Find the best matching threshold
        # Logic: Find the nearest threshold that does not exceed the score
        best_match: FinalThreshold = thresholds[0]  # Start with the lowest value

        for threshold in thresholds:
            if score >= threshold.value:
                best_match = threshold
            else:
                # Since the list is sorted, we can stop when we encounter a larger threshold
                break

        return best_match.name, ScoreFinalMapper.FINAL_MAPPER_TEMPLATE.format(
            name=best_match.name, description=best_match.description
        )

    def match(self, score: float, purpose: SemanticType) -> FinalThreshold:
        """Find the best matching threshold for a score and purpose.

        Args:
            score (float): The final score to be interpreted.
            purpose (SemanticType): The purpose of the score, to select the correct threshold set.

        Returns:
            FinalThreshold: The best matching threshold.

        Raises:
            ValueError: If no threshold set is found for the given purpose.
        """
        thresholds = self._threshold_map.get(purpose)

        if thresholds is None:
            raise ValueError(f"No threshold set found for purpose: {purpose.name}")

        # Find the best matching threshold
        # Logic: Find the nearest threshold that does not exceed the score
        best_match: FinalThreshold = thresholds[0]  # Start with the lowest value

        for threshold in thresholds:
            if score >= threshold.value:
                best_match = threshold
            else:
                # Since the list is sorted, we can stop when we encounter a larger threshold
                break

        return best_match
