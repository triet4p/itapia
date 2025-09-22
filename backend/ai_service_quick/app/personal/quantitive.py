"""Quantitative preferences analyzer for mapping user profiles to quantitative configurations."""

from typing import Dict
from itapia_common.schemas.entities.performance import PerformanceFilterWeights, PerformanceHardConstraints
from itapia_common.schemas.entities.personal import QuantitivePreferencesConfig, BehaviorModifiers
from itapia_common.schemas.entities.profiles import ProfileEntity


class QuantitivePreferencesAnalyzer:
    """Analyzer for converting user profiles into quantitative preferences configurations."""
    
    # --- BASELINE CONSTANTS ---
    # Start with a "perfect" average profile
    BASE_WEIGHTS: PerformanceFilterWeights = PerformanceFilterWeights(
        cagr=0.25,
        sortino_ratio=0.25,
        max_drawdown_pct=0.25,
        annual_return_stability=0.15,
        profit_factor=0.10
    )
    
    def get_suggested_config(self, profile: ProfileEntity) -> QuantitivePreferencesConfig:
        """Main coordination function: build quantitative configuration from profile.
        
        Args:
            profile (ProfileEntity): User investment profile
            
        Returns:
            QuantitivePreferencesConfig: Suggested quantitative preferences configuration
        """
        return QuantitivePreferencesConfig(
            weights=self._map_profile_to_weights(profile),
            constraints=self._map_profile_to_constraints(profile),
            modifiers=self._map_profile_to_modifiers(profile)
        )
    
    def _map_profile_to_weights(self, profile: ProfileEntity) -> PerformanceFilterWeights:
        """Map entire profile to weights, considering interactions between factors.
        
        Args:
            profile (ProfileEntity): User investment profile
            
        Returns:
            PerformanceFilterWeights: Weights for performance metrics
        """
        # Start from balanced baseline weights
        weights = self.BASE_WEIGHTS.model_copy(deep=True)

        # === 1. Adjust based on PRIMARY GOAL ===
        # This is the most influential factor on weights
        if profile.invest_goal.primary_goal == 'capital_preservation':
            weights.max_drawdown_pct += 0.30  # Safety is paramount
            weights.annual_return_stability += 0.15
            weights.sortino_ratio += 0.10
            weights.cagr -= 0.35
            weights.profit_factor -= 0.20
        elif profile.invest_goal.primary_goal == 'capital_growth':
            weights.cagr += 0.20
            weights.profit_factor += 0.10
            weights.max_drawdown_pct -= 0.20
        elif profile.invest_goal.primary_goal == 'speculation':
            weights.cagr += 0.35
            weights.profit_factor += 0.15
            weights.max_drawdown_pct -= 0.30
            weights.annual_return_stability -= 0.20

        # === 2. Adjust based on RISK APPETITE ===
        # This factor will "amplify" or "attenuate" weights related to risk/return
        risk_map = {
            "very_conservative": {'risk_mult': 1.5, 'return_mult': 0.5},
            "conservative":      {'risk_mult': 1.2, 'return_mult': 0.8},
            "moderate":          {'risk_mult': 1.0, 'return_mult': 1.0},
            "aggressive":        {'risk_mult': 0.7, 'return_mult': 1.3},
            "very_aggressive":   {'risk_mult': 0.4, 'return_mult': 1.8}
        }
        
        multipliers = risk_map.get(profile.risk_tolerance.risk_appetite)
        if multipliers:
            weights.cagr *= multipliers['return_mult']
            weights.profit_factor *= multipliers['return_mult']
            weights.max_drawdown_pct *= multipliers['risk_mult']
            weights.sortino_ratio *= multipliers['risk_mult']
            weights.annual_return_stability *= multipliers['risk_mult']

        # === 3. (Optional) Small adjustments based on EXPERIENCE ===
        if profile.knowledge_exp.investment_knowledge in ['beginner', 'intermediate']:
             # Beginners typically prefer stable, easy-to-follow strategies
            weights.annual_return_stability += 0.05
            weights.max_drawdown_pct += 0.05
            weights.cagr -= 0.10

        # === 4. Normalize final weights ===
        weights_dict: Dict[str, float] = {k: max(0, v) for k, v in weights.model_dump().items()}
        total_weights = sum(weights_dict.values())
        if total_weights == 0: total_weights = 1
        
        normalized_weights = {k: v / total_weights for k, v in weights_dict.items()}
        
        return PerformanceFilterWeights.model_validate(normalized_weights)
    
    def _map_profile_to_constraints(self, profile: ProfileEntity) -> PerformanceHardConstraints:
        """Map entire profile to hard constraints.
        
        Args:
            profile (ProfileEntity): User investment profile
            
        Returns:
            PerformanceHardConstraints: Hard constraints for performance metrics
        """
        # Start with default constraints (e.g., always need at least 20 trades)
        constraints = PerformanceHardConstraints(num_trades=(10, None))

        # --- Set Max Drawdown based on Risk Appetite AND Loss Reaction ---
        # Start with a baseline level
        risk_appetite_map = {
            "very_conservative": 0.10, "conservative": 0.15, "moderate": 0.25,
            "aggressive": 0.35, "very_aggressive": 0.50
        }
        max_dd = risk_appetite_map.get(profile.risk_tolerance.risk_appetite, 0.30)
        
        # Adjust based on loss reaction behavior
        if profile.risk_tolerance.loss_reaction == "panic_sell":
            max_dd *= 0.8 # If prone to panic, tighten drawdown by 20%
        elif profile.risk_tolerance.loss_reaction == "buy_the_dip":
            max_dd *= 1.1 # If confident, can loosen slightly

        constraints.max_drawdown_pct = (None, round(max_dd, 2))

        # --- Set Min CAGR based on Expected Return AND Investment Horizon ---
        expected_return = profile.invest_goal.expected_annual_return_pct / 100.0
        
        # Adjust minimum requirement based on investment horizon
        horizon_map = {"short_term": 0.07, "mid_term": 0.05, "long_term": 0.04}
        min_requirement_factor = horizon_map.get(profile.invest_goal.investment_horizon, 0.05)
        
        min_cagr = expected_return * min_requirement_factor
        constraints.cagr = (round(min_cagr, 2), None)
        
        return constraints
        
    def _map_profile_to_modifiers(self, profile: ProfileEntity) -> BehaviorModifiers:
        """Map entire profile to behavior adjustment parameters.
        
        Args:
            profile (ProfileEntity): User investment profile
            
        Returns:
            BehaviorModifiers: Behavior modifiers for trading decisions
        """
        # Start with default values
        sizing_factor = 1.0
        risk_factor = 1.0

        # --- Adjust Sizing Factor based on Loss Reaction AND Income Dependency ---
        sizing_map = {"panic_sell": 0.7, "reduce_exposure": 0.85, "hold_and_wait": 1.0, "buy_the_dip": 1.15}
        sizing_factor *= sizing_map.get(profile.risk_tolerance.loss_reaction, 1.0)
        
        if profile.capital_income.income_dependency == "high":
            # If highly dependent on income, should reduce risk -> reduce position size
            sizing_factor *= 0.8

        # --- Adjust Risk Factor based on Risk Appetite AND Experience ---
        risk_appetite_map = {
            "very_conservative": 0.8, "conservative": 0.9, "moderate": 1.0,
            "aggressive": 1.1, "very_aggressive": 1.25
        }
        risk_factor *= risk_appetite_map.get(profile.risk_tolerance.risk_appetite, 1.0)

        if profile.knowledge_exp.investment_knowledge == "beginner":
            # Beginners should be encouraged to tighten risk somewhat
            risk_factor *= 0.95
        
        return BehaviorModifiers(
            position_sizing_factor=round(sizing_factor, 2),
            risk_tolerance_factor=round(risk_factor, 2)
        )