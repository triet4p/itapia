from pydantic import BaseModel, Field

from .performance import PerformanceFilterWeights, PerformanceHardConstraints

class BehaviorModifiers(BaseModel):
    """
    Các tham số để ĐIỀU CHỈNH HÀNH VI giao dịch cuối cùng.
    """
    # Yếu tố điều chỉnh kích thước vị thế. 1.0 = mặc định, 0.5 = giảm 50%
    position_sizing_factor: float = Field(1.0, ge=0.1, le=2.0, 
                                          description="Factor to scale position size. 1.0 is default.")
    
    # Yếu tố điều chỉnh mức độ chấp nhận rủi ro (SL/TP)
    # 1.0 = mặc định, 0.8 = thắt chặt 20%, 1.2 = nới lỏng 20%
    risk_tolerance_factor: float = Field(1.0, ge=0.5, le=1.5,
                                         description="Factor to adjust risk parameters like Stop-Loss. >1.0 means higher risk tolerance.")
    
class QuantitivePreferencesConfig(BaseModel):
    weights: PerformanceFilterWeights
    constraints: PerformanceHardConstraints
    modifiers: BehaviorModifiers