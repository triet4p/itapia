"""Sentiment analysis model for news texts using transformer models."""

from typing import List
from transformers import pipeline

from itapia_common.schemas.entities.analysis.news import SentimentAnalysisReport


class SentimentAnalysisModel:
    """Performs sentiment analysis on news texts using transformer models."""
    
    def __init__(self, model_name: str):
        """Initialize the sentiment analysis model.
        
        Args:
            model_name (str): Name of the transformer model to use for sentiment analysis
        """
        self.pipe = pipeline("sentiment-analysis", model=model_name, device='cpu')
        
    def analysis_sentiment(self, texts: List[str]) -> List[SentimentAnalysisReport]:
        """Analyze sentiment of texts.
        
        Args:
            texts (List[str]): List of texts to analyze
            
        Returns:
            List[SentimentAnalysisReport]: List of sentiment analysis reports
        """
        analysis_dicts = self.pipe(texts, truncation=True, padding=True)
        return [
            SentimentAnalysisReport(
                label=analysis_dict['label'].lower(),
                score=round(analysis_dict['score'], 3)
            )
            for analysis_dict in analysis_dicts
        ]