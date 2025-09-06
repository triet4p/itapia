from pydantic import BaseModel, Field
from typing import List, Literal

class SentimentAnalysisReport(BaseModel):
    label: Literal['negative', 'neutral', 'positive'] = Field(..., description='Label of sentiment')
    score: int|float = Field(..., description='Score of sentiment')
    
    class Config:
        from_attributes = True
        
class NERElement(BaseModel):
    entity_group: str = Field(..., description='Name of entity group')
    word: str = Field(..., description='word recognized')
    class Config:
        from_attributes = True
    
class NERReport(BaseModel):
    entities: List[NERElement] = Field(..., description='List of entity')
    class Config:
        from_attributes = True
        
ImpactLabel = Literal['low', 'moderate', 'high', 'unknown']
        
class ImpactAssessmentReport(BaseModel):
    level: ImpactLabel = Field(..., description='Level of impact')
    words: List[str] = Field(..., default_factory=list, description='List of evidence impact words')
    
    class Config:
        from_attributes = True
        
class KeywordHighlightingReport(BaseModel):
    positive_keywords: List[str] = Field(..., description='List of positive keyword highlighted')
    negative_keywords: List[str] = Field(..., description='List of negative keyword highlighted')
    
    class Config:
        from_attributes = True
        
class SummaryReport(BaseModel):
    num_positive_sentiment: int
    num_negative_sentiment: int
    num_high_impact: int
    num_moderate_impact: int
    num_low_impact: int
    avg_of_positive_keyword_found: float
    avg_of_negative_keyword_found: float
    avg_of_ner_found: float
        
class SingleNewsAnalysisReport(BaseModel):
    text: str = Field(..., description='Text to analysis')
    sentiment_analysis: SentimentAnalysisReport = Field(..., description='Sentiment Analysis Report')
    ner: NERReport = Field(..., description='NER Report')
    impact_assessment: ImpactAssessmentReport = Field(..., description='Impact Assessment Report')
    keyword_highlighting_evidence: KeywordHighlightingReport = Field(..., description='Keyword Highlighting Evidence')
    
    class Config:
        from_attributes = True
        
class NewsAnalysisReport(BaseModel):
    ticker: str
    reports: List[SingleNewsAnalysisReport]
    summary: SummaryReport