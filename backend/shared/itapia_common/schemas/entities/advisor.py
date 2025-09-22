# itapia_common/contracts/schemas/entities/advisor.py
"""Advisor module schemas for ITAPIA."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any
from .action import Action

class TriggeredRuleInfo(BaseModel):
    """
    Summary information about a triggered rule.
    'Triggered' means the rule returned a non-zero score.
    """
    
    rule_id: str = Field(..., description="ID of the rule.")
    name: str = Field(..., description="Human-readable name of the rule.")
    score: float = Field(..., description="Normalized score returned by the rule.")
    purpose: str = Field(..., description="Purpose of the rule, e.g., 'DECISION_SIGNAL'.")
    
    class Config:
        from_attributes = True

class AggregatedScoreInfo(BaseModel):
    """
    Information about scores aggregated from rule sets.
    """
    
    raw_decision_score: float = Field(..., description="Raw decision score, -1 is immediate sell, 1 is very strong buy, range from -1 to 1")
    raw_risk_score: float = Field(..., description="Raw risk score, 0 is no risk, 1 is very high risk, range from 0 to 1.")
    raw_opportunity_score: float = Field(..., description="Raw opportunity score, 0 is no opportunity, 1 is very high opportunity, range from 0 to 1.")
    
    class Config:
        from_attributes = True

class FinalRecommendation(BaseModel):
    """
    Information about the final recommendation after all layers.
    """
    
    # Final score after going through MetaRule
    final_score: float = Field(..., description="Final score after aggregation and personalization.")
    purpose: str
    label: str
    # Label interpreted from the score
    final_recommend: str = Field(..., description="Final recommendation")
    
    triggered_rules: List[TriggeredRuleInfo] = Field(..., description="List of triggered rules that contributed to the result.")

    class Config:
        from_attributes = True


class AdvisorReportSchema(BaseModel):
    """
    Schema for the final consolidated report from the Advisor Module.
    This is the main data "contract", used both internally and returned by the API in the MVP phase.
    """
    
    # --- Main Conclusion Section (Most important for users) ---
    final_decision: FinalRecommendation = Field(..., description="Final Decision recommendation.")
    final_risk: FinalRecommendation = Field(..., description="Final Risk assessment.")
    final_opportunity: FinalRecommendation = Field(..., description="Final Opportunity assessment.")
    
    final_action: Action = Field(..., description="Final mapped action")
    
    # --- Evidence and Explanation Section (For debugging and XAI) ---
    aggregated_scores: AggregatedScoreInfo = Field(..., description="Aggregated scores before going through MetaRule.")
    
    # --- Report Metadata ---
    ticker: str = Field(..., description="Stock symbol being analyzed.")
    generated_at_utc: str = Field(..., description="Report generation time (ISO format).")
    generated_timestamp: int = Field(..., description="Generated with timestamp")

    class Config:
        from_attributes = True