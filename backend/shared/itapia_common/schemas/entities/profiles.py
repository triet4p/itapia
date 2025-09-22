# schemas/entities/profiles.py
"""Investment profile schemas for ITAPIA."""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime, timezone

# ===================================================================
# == A. Enum/Literal data types to define choices
# ===================================================================

RiskAppetite = Literal[
    "very_conservative", 
    "conservative", 
    "moderate", 
    "aggressive", 
    "very_aggressive"
]

InvestmentHorizon = Literal[
    "short_term",  # Under 1 year
    "mid_term",    # 1-5 years
    "long_term"    # Over 5 years
]

LossReaction = Literal[
    "panic_sell",      # Sell immediately
    "reduce_exposure", # Reduce exposure
    "hold_and_wait",   # Hold and wait
    "buy_the_dip"      # Buy the dip
]

InvestmentKnowledge = Literal[
    "beginner",
    "intermediate",
    "advanced",
    "expert"
]

PrimaryGoal = Literal[
    "capital_preservation", # Capital preservation
    "income_generation",    # Income generation (dividends)
    "capital_growth",       # Capital growth
    "speculation"           # Speculation
]

class RiskTolerancePart(BaseModel):
    """Risk tolerance profile part."""
    
    risk_appetite: RiskAppetite = Field(..., description="Overall risk tolerance")
    loss_reaction: LossReaction = Field(..., description="Typical reaction when the market drops sharply.")

    class Config:
        from_attributes = True
        
class InvestGoalPart(BaseModel):
    """Investment goal profile part."""
    
    primary_goal: PrimaryGoal = Field(..., description="The primary goal of this investment profile.")
    investment_horizon: InvestmentHorizon = Field(..., description="The expected investment time frame.")
    expected_annual_return_pct: int = Field(..., ge=0, le=100, description="Expected annual rate of return (%)")
    
    class Config: 
        from_attributes = True
        
class KnowledgeExpPart(BaseModel):
    """Knowledge and experience profile part."""
    
    investment_knowledge: InvestmentKnowledge = Field(..., description="Level of knowledge of financial markets.")
    years_of_experience: int = Field(..., ge=0, le=50, description="Number of years of investment experience.")

    class Config:
        from_attributes = True

class CapitalIncomePart(BaseModel):
    """Capital and income profile part."""
    
    initial_capital: float = Field(..., gt=0, description="Initial capital for this profile.")
    income_dependency: Literal["low", "medium", "high"] = Field(..., description="Degree of dependence on investment income.")

    class Config:
        from_attributes = True
        
class PersonalPreferPart(BaseModel):
    """Personal preferences profile part."""
    
    preferred_sectors: Optional[list[str]] = Field(default=None, description="Preferred sectors (eg: ['TECH', 'HEALTHCARE']).")
    excluded_sectors: Optional[list[str]] = Field(default=None, description="Sectors you want to exclude.")
    ethical_investing: bool = Field(default=False, description="Prefer ethical investing (ESG) criteria.")       
    
    class Config:
        from_attributes = True
        
class ProfileBase(BaseModel):
    """Base investment profile schema."""
    
    profile_name: str = Field(..., min_length=3, max_length=100, description="Name of profile")
    description: str = Field(..., description="Short description about this profile")
    
    risk_tolerance: RiskTolerancePart
    invest_goal: InvestGoalPart
    knowledge_exp: KnowledgeExpPart
    capital_income: CapitalIncomePart
    personal_prefer: PersonalPreferPart
    use_in_advisor: bool = Field(default=True, description="Allow Advisor to use this profile to personalize advice.")
    is_default: bool = Field(default=False, description="Set as default profile.")
    
    class Config:
        from_attributes = True
        
class ProfileCreate(ProfileBase):
    """Schema for creating a new investment profile."""
    pass

class ProfileUpdate(BaseModel):
    """
    Schema used when updating. All fields are optional.
    Users can send only the fields they want to change.
    """
    
    profile_name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    risk_tolerance: Optional[RiskTolerancePart] = None
    invest_goal: Optional[InvestGoalPart] = None
    knowledge_exp: Optional[KnowledgeExpPart] = None
    capital_income: Optional[CapitalIncomePart] = None
    personal_prefer: Optional[PersonalPreferPart] = None
    
    use_in_advisor: Optional[bool] = None
    is_default: Optional[bool] = None
    
    class Config:
        from_attributes = True

class ProfileEntity(ProfileBase):
    """Investment profile entity with database fields."""
    
    profile_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime