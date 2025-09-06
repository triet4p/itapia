"""Word-based keyword highlighting model for extracting sentiment evidence from news texts."""

from typing import List, Union, Set

# Import predefined Pydantic schemas
from itapia_common.schemas.entities.analysis.news import (
    KeywordHighlightingReport
)


class WordBasedKeywordHighlightingModel:
    """Extracts sentiment keywords (evidence) from text based on provided dictionaries."""
    
    def __init__(self, positive_dictionary: Set[str], negative_dictionary: Set[str]):
        """Initialize model with loaded dictionaries.
        
        Args:
            positive_dictionary (Set[str]): A set containing positive words
            negative_dictionary (Set[str]): A set containing negative words
        """
        self.positive_words = positive_dictionary
        self.negative_words = negative_dictionary

    def extract(self, texts: List[str]) -> List[KeywordHighlightingReport]:
        """Extract sentiment evidence for one or more texts (preprocessed).
        
        Args:
            texts (List[str]): A list of normalized texts to analyze
            
        Returns:
            List[KeywordHighlightingReport]: Extracted evidence reports
        """

        reports = []
        for text in texts:
            # Split text into unique words to highlight each word only once
            words_in_text = set(text.split())
            
            # Find words matching dictionaries
            found_positive = [
                word
                for word in words_in_text if word in self.positive_words
            ]
            found_negative = [
                word 
                for word in words_in_text if word in self.negative_words
            ]
            
            reports.append(KeywordHighlightingReport(
                positive_keywords=found_positive,
                negative_keywords=found_negative
            ))

        return reports