from pydantic import BaseModel, Field

from .performance import PerformanceFilterWeights, PerformanceHardConstraints

class BehaviorModifiers(BaseModel):
    """
    Parameters to MODIFY the final trading behavior.
    """
    
    # Position sizing factor. 1.0 = default, 0.5 = reduce by 50%
    position_sizing_factor: float = Field(1.0, ge=0.1, le=2.0, 
                                          description="Factor to scale position size. 1.0 is default.")
    
    # Risk tolerance factor (SL/TP adjustment)
    # 1.0 = default, 0.8 = tighten by 20%, 1.2 = loosen by 20%
    risk_tolerance_factor: float = Field(1.0, ge=0.5, le=1.5,
                                         description="Factor to adjust risk parameters like Stop-Loss. >1.0 means higher risk tolerance.")
    
class QuantitivePreferencesConfig(BaseModel):
    """Quantitative preferences configuration."""
    
    weights: PerformanceFilterWeights
    constraints: PerformanceHardConstraints
    modifiers: BehaviorModifiers