from pydantic import BaseModel, Field
from typing import List, Literal

class SentimentAnalysisReport(BaseModel):
    label: Literal['negative', 'neutral', 'positive'] = Field(..., description='Label of sentiment')
    score: int|float = Field(..., description='Score of sentiment')
    
    class Config:
        from_attributes = True
    
class NERReport(BaseModel):
    text: str = Field(..., description='Key entity text')
    ner_type: str = Field(..., description='Type of key entity')
    
    class Config:
        from_attributes = True
    
class ImpactAssessmentReport(BaseModel):
    level: Literal['low', 'moderate', 'high'] = Field(..., description='Level of impact')
    score: int|float = Field(..., description='Score of impact')
    
    class Config:
        from_attributes = True
    
class WordHighlightElement(BaseModel):
    word: str = Field(..., description='Word highlighted')
    weight: str = Field(..., description='Weight of contribution to sentence')
    
    class Config:
        from_attributes = True
        
class KeywordHighlightingReport(BaseModel):
    positive_keywords: List[WordHighlightElement] = Field(..., description='List of positive keyword highlighted')
    negative_keywords: List[WordHighlightElement] = Field(..., description='List of negative keyword highlighted')
    
    class Config:
        from_attributes = True
        
class SingleNewsAnalysisReport(BaseModel):
    text: str = Field(..., description='Text to analysis')
    sentiment_analysis: SentimentAnalysisReport = Field(..., description='Sentiment Analysis Report')
    ner: NERReport|None = Field(..., description='NER Report')
    impact_assessment: ImpactAssessmentReport|None = Field(..., description='Impact Assessment Report')
    keyword_highlighting_evidence: KeywordHighlightingReport|None = Field(..., description='Keyword Highlighting Evidence')
    
    class Config:
        from_attributes = True
        
class NewsAnalysisReport(BaseModel):
    ticker: str
    reports: List[SingleNewsAnalysisReport]