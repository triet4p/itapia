from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class CurrentStatusReport(BaseModel):
    """Current market status report."""

    vwap_status: Literal["above", "below", "undefined"] = Field(
        ..., description="Comparison between VWAP-D and current price"
    )
    open_status: Literal["above", "below"] = Field(
        ..., description="Comparison between current price and open price"
    )
    rsi_status: Literal["overbought", "oversold", "neutral"] = Field(
        ..., description="RSI Status"
    )
    evidence: Dict[str, Any] = Field(
        ..., description="A dictionary describing evidence of status analysis"
    )

    class Config:
        from_attributes = True


class KeyLevelsReport(BaseModel):
    """Key levels report."""

    day_high: float
    day_low: float
    open_price: float
    vwap: Optional[float]
    or_30m_high: Optional[float]
    or_30m_low: Optional[float]

    class Config:
        from_attributes = True


class MomentumReport(BaseModel):
    """Momentum analysis report."""

    macd_crossover: Literal["bull", "bear", "neutral"] = Field(
        ..., description="Decide relationship of MACD and Signal line"
    )
    volume_status: Literal["normal", "high-spike"] = Field(
        ..., description="Decide if volume spike ratio > 2.0"
    )
    opening_range_status: Literal["bull-breakout", "bear-breakdown", "inside"] = Field(
        ..., description="Opening Range breakout"
    )
    evidence: Dict[str, Any] = Field(
        ..., description="A dictionary describing evidence of momentum analysis"
    )

    class Config:
        from_attributes = True


class IntradayAnalysisReport(BaseModel):
    """Complete intraday technical analysis report."""

    current_status_report: CurrentStatusReport = Field(..., description="Status report")
    momentum_report: MomentumReport = Field(..., description="Momentum report")
    key_levels: KeyLevelsReport = Field(..., description="Key levels")
