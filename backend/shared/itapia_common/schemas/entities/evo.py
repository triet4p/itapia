from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from .rules import RuleEntity


class EvoRunStatus(str, Enum):
    """Status of an evolutionary run."""

    COMPLETED = "COMPLETED"
    RUNNING = "RUNNING"


class EvoRuleEntity(RuleEntity):
    """Rule entity produced by an evolutionary run."""

    evo_run_id: str = Field(..., description="Evo Run which produced this rule")


class EvoRunEntity(BaseModel):
    """Evolutionary run entity."""

    run_id: str = Field(..., description="Running ID of this Evolutionary Run.")
    status: EvoRunStatus = Field(..., description="Status of this run")
    algorithm: str = Field(..., description="Algorithm this run used.")
    config: Dict[str, Any] = Field(..., description="Metadata of this run")
    fallback_state: bytes = Field(
        ..., description="A pickle dump to save any fallback state of this run"
    )
    rules: List[EvoRuleEntity] = Field(
        ..., description="Evo Rule Entities of this run."
    )
