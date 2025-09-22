from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from .performance import PerformanceMetrics


class SemanticType(str, Enum):
    """
    Defines semantic types for values in rule trees.
    This is the heart of Strongly Typed Genetic Programming (STGP).
    """

    # Basic data types
    NUMERICAL = "NUMERICAL"  # Any number, no specific meaning
    BOOLEAN = "BOOLEAN"  # True/False signal (1.0 / 0.0)

    # Financial semantic types
    PRICE = "PRICE"  # Price-related values (e.g., close, open)
    PERCENTAGE = "PERCENTAGE"  # Percentage values (e.g., price change, return rate)
    FINANCIAL_RATIO = "FINANCIAL_RATIO"  # Financial ratios (e.g., P/E)

    # Technical indicator types
    MOMENTUM = "MOMENTUM"  # Momentum indicators (RSI, Stochastic)
    TREND = "TREND"  # Trend indicators (MACD, ADX)
    VOLATILITY = "VOLATILITY"  # Volatility indicators (ATR, Bollinger Bands)
    VOLUME = "VOLUME"  # Volume indicators (OBV)

    # Other analysis types
    SENTIMENT = "SENTIMENT"  # Sentiment score
    FORECAST_PROB = "FORECAST_PROB"  # Forecast probability

    # Decision semantic types
    DECISION_SIGNAL = "DECISION_SIGNAL"
    RISK_LEVEL = "RISK_LEVEL"
    OPPORTUNITY_RATING = "OPPORTUNITY_RATING"

    # Special types
    ANY = "ANY"  # Can be any type (used for flexible operators)
    ANY_NUMERIC = "ANY_NUMERIC"  # Can be any numeric type (used for flexible operators)

    def __init__(self, value: str):
        self.concreates: List[SemanticType] = []


SemanticType.ANY.concreates = [
    SemanticType.NUMERICAL,
    SemanticType.PRICE,
    SemanticType.PERCENTAGE,
    SemanticType.FINANCIAL_RATIO,
    SemanticType.MOMENTUM,
    SemanticType.TREND,
    SemanticType.VOLATILITY,
    SemanticType.VOLUME,
    SemanticType.SENTIMENT,
    SemanticType.FORECAST_PROB,
    SemanticType.BOOLEAN,
]

SemanticType.ANY_NUMERIC.concreates = [
    SemanticType.NUMERICAL,
    SemanticType.PRICE,
    SemanticType.PERCENTAGE,
    SemanticType.FINANCIAL_RATIO,
    SemanticType.MOMENTUM,
    SemanticType.TREND,
    SemanticType.VOLATILITY,
    SemanticType.VOLUME,
    SemanticType.SENTIMENT,
    SemanticType.FORECAST_PROB,
]


class NodeType(str, Enum):
    """Type of node in a rule tree."""

    CONSTANT = "constant"
    VARIABLE = "variable"
    OPERATOR = "operator"

    ANY = "any"


class RuleStatus(str, Enum):
    """Status of a rule."""

    READY = "READY"
    EVOLVING = "EVOLVING"
    DEPRECATED = "DEPRECATED"


class SemanticLevel(str, Enum):
    """Semantic level of a rule or value."""

    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "low"


class NodeEntity(BaseModel):
    """Node entity in a rule tree."""

    node_name: str
    children: Optional[List["NodeEntity"]] = Field(default=None)

    class Config:
        from_attributes = True


class NodeSpecEntity(BaseModel):
    """Node specification entity."""

    node_name: str
    description: str
    node_type: NodeType
    return_type: SemanticType = Field(..., description="Return type of a node")
    args_type: Optional[List[SemanticType]] = Field(
        default=None, description="Argument type, only needed for operator node"
    )

    class Config:
        from_attributes = True


class RuleEntity(BaseModel):
    """Rule entity."""

    rule_id: str
    name: str
    description: str
    purpose: SemanticType
    rule_status: RuleStatus
    created_at: datetime
    updated_at: datetime

    # Rule definition is stored as a dictionary
    root: NodeEntity

    metrics: Optional[PerformanceMetrics] = Field(default=None)

    class Config:
        from_attributes = True


class ExplainationRuleEntity(RuleEntity):
    """Rule entity with explanation."""

    explain: str
