"""Word-based impact assessment model for news analysis."""

from typing import List, Set, Tuple

from itapia_common.schemas.entities.analysis.news import (
    ImpactAssessmentReport,
    ImpactLabel,
)


class WordBasedImpactAssessmentModel:
    """Assesses the impact level of news texts based on predefined dictionaries of keywords."""

    def __init__(
        self,
        high_impact_dictionary: Set[str],
        moderate_impact_dictionary: Set[str],
        low_impact_dictionary: Set[str],
    ):
        """Initialize the impact assessment model with keyword dictionaries.

        Args:
            high_impact_dictionary (Set[str]): Set of high impact keywords
            moderate_impact_dictionary (Set[str]): Set of moderate impact keywords
            low_impact_dictionary (Set[str]): Set of low impact keywords
        """
        self.high_impact_dictionary = high_impact_dictionary
        self.moderate_impact_dictionary = moderate_impact_dictionary
        self.low_impact_dictionary = low_impact_dictionary

    def _find_matched_keywords(self, text: str) -> Tuple[ImpactLabel, List[str]]:
        """Helper function that scans text and returns both label and matched keywords.

        Args:
            text (str): Text to scan for impact keywords

        Returns:
            Tuple[ImpactLabel, List[str]]: Tuple containing impact level and list of matched keywords
        """
        # Scan for High Impact keywords
        high_matches = [
            keyword for keyword in self.high_impact_dictionary if keyword in text
        ]
        if high_matches:
            return (
                "high",
                high_matches,
            )  # Return immediately when highest level is found

        # If not, scan for Medium Impact keywords
        medium_matches = [
            keyword for keyword in self.moderate_impact_dictionary if keyword in text
        ]
        if medium_matches:
            return "moderate", medium_matches

        # If no matches found
        low_matches = [
            keyword for keyword in self.low_impact_dictionary if keyword in text
        ]
        if low_matches:
            return "low", low_matches

        return "unknown", []

    def assess(self, texts: List[str]) -> List[ImpactAssessmentReport]:
        """Assess impact for one or more texts (preprocessed/normalized).

        Args:
            texts (List[str]): List of preprocessed texts to analyze

        Returns:
            List[ImpactAssessmentReport]: List of impact assessment reports
        """
        reports = []
        for text in texts:
            # Call helper function to get both pieces of information
            label, matched_keywords = self._find_matched_keywords(text)

            reports.append(ImpactAssessmentReport(level=label, words=matched_keywords))

        return reports
