from typing import Dict
from itapia_common.schemas.entities.performance import PerformanceFilterWeights, PerformanceHardConstraints
from itapia_common.schemas.entities.personal import QuantitivePreferencesConfig, BehaviorModifiers
from itapia_common.schemas.entities.profiles import ProfileEntity

class QuantitivePreferencesAnalyzer:
    DEFAULT_WEIGHTS: PerformanceFilterWeights = PerformanceFilterWeights(
        cagr=0.2,
        sortino_ratio=0.2,
        max_drawdown_pct=0.2,
        annual_return_stability=0.2,
        profit_factor=0.2
    )
    
    MIN_WEIGHTS: float = 0.05
    
    DEFAULT_CONSTRAINTS: PerformanceHardConstraints = PerformanceHardConstraints()
    
    DEFAULT_MODIFIERS: BehaviorModifiers = BehaviorModifiers()
    
    def get_suggested_config(self, profile: ProfileEntity) -> QuantitivePreferencesConfig:
        return QuantitivePreferencesConfig(
            weights=self._map_profile_to_weights(profile),
            constraints=self._map_profile_to_constraints(profile),
            modifiers=self._map_profile_to_modifiers(profile)
        )
    
    def _map_profile_to_weights(self, profile: ProfileEntity) -> PerformanceFilterWeights:
        weights = self.DEFAULT_WEIGHTS.model_copy(deep=True)
        
        if profile.invest_goal.primary_goal == 'capital_preservation':
            weights.max_drawdown_pct += 0.3
            weights.sortino_ratio += 0.1
            weights.cagr = max(self.MIN_WEIGHTS, weights.cagr - 0.2)
        elif profile.invest_goal.primary_goal == 'capital_growth':
            weights.cagr += 0.2
            weights.profit_factor += 0.1
            weights.max_drawdown_pct = max(self.MIN_WEIGHTS, weights.max_drawdown_pct - 0.2)
        elif profile.invest_goal.primary_goal == 'speculation':
            weights.cagr += 0.35
            weights.profit_factor += 0.2
            weights.max_drawdown_pct = max(self.MIN_WEIGHTS, weights.max_drawdown_pct - 0.3)
            weights.annual_return_stability = max(self.MIN_WEIGHTS, weights.annual_return_stability - 0.2)
            
        if profile.risk_tolerance.risk_appetite in ["very_conservative", "conservative"]:
            weights.max_drawdown_pct *= 1.5
            weights.cagr *= 0.5
            
        if profile.risk_tolerance.risk_appetite in ["aggressive", "very_aggressive"]:
            weights.max_drawdown_pct *= 0.5
            weights.cagr *= 1.5
            
        weights_dict: Dict[str, float] = {k: max(0, v) for k, v in weights.model_dump().items()}
        total_weights = sum(weights_dict.values())
        
        if total_weights == 0:
            total_weights = 1
        
        normalized_weights = {k: v / total_weights for k, v in weights_dict.items()}
        
        return PerformanceFilterWeights.model_validate(normalized_weights)
    
    def _map_profile_to_constraints(self, profile: ProfileEntity) -> PerformanceHardConstraints:
        # --- Thiết lập Max Drawdown Limit dựa trên Risk Appetite ---
        risk_map = {
            "very_conservative": (None, 0.10), # (min, max)
            "conservative": (None, 0.15),
            "moderate": (None, 0.25),
            "aggressive": (None, 0.35),
            "very_aggressive": (None, 0.50)
        }
        max_dd_constraint = risk_map.get(profile.risk_tolerance.risk_appetite, (None, None))

        # --- Thiết lập Min CAGR Limit dựa trên Kỳ vọng ---
        expected_return = profile.invest_goal.expected_annual_return_pct / 100.0
        # Yêu cầu tối thiểu phải đạt 50% kỳ vọng
        min_cagr_constraint = (expected_return * 0.5, None) 
        
        return PerformanceHardConstraints(
            max_drawdown_pct=max_dd_constraint,
            cagr=min_cagr_constraint,
            num_trades=(20, None) # Ràng buộc cứng: luôn yêu cầu ít nhất 20 giao dịch
        )
        
    def _map_profile_to_modifiers(self, profile: ProfileEntity) -> BehaviorModifiers:
        """
        Ánh xạ hồ sơ người dùng thành các tham số điều chỉnh hành vi.
        """
        # --- Điều chỉnh Kích thước Vị thế dựa trên Phản ứng với Thua lỗ ---
        sizing_map = {
            "panic_sell": 0.7,      # Rất nhạy cảm, giảm size
            "reduce_exposure": 0.85,
            "hold_and_wait": 1.0,   # Mặc định
            "buy_the_dip": 1.15     # Tự tin hơn, có thể tăng nhẹ size
        }
        sizing_factor = sizing_map.get(profile.risk_tolerance.loss_reaction, 1.0)
        
        # --- Điều chỉnh Mức độ Chấp nhận Rủi ro dựa trên "Khẩu vị" ---
        risk_map = {
            "very_conservative": 0.8, # Thắt chặt SL 20%
            "conservative": 0.9,
            "moderate": 1.0,
            "aggressive": 1.1,
            "very_aggressive": 1.25 # Nới lỏng SL 25%
        }
        risk_factor = risk_map.get(profile.risk_tolerance.risk_appetite, 1.0)
        
        return BehaviorModifiers(
            position_sizing_factor=sizing_factor,
            risk_tolerance_factor=risk_factor
        )