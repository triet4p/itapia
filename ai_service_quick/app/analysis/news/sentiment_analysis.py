from typing import List
from transformers import pipeline

from itapia_common.schemas.entities.analysis.news import SentimentAnalysisReport

class SentimentAnalysisModel:
    def __init__(self, model_name: str):
        self.pipe = pipeline("sentiment-analysis", model=model_name, device='cpu')
        
    def analysis_sentiment(self, texts: List[str]) -> List[SentimentAnalysisReport]:
        analysis_dicts = self.pipe(texts, truncation=True, padding=True)
        return [
            SentimentAnalysisReport(
                label=analysis_dict['label'].lower(),
                score=round(analysis_dict['score'], 3)
            )
            for analysis_dict in analysis_dicts
        ]