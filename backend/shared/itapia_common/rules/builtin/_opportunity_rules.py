# itapia_common/rules/_opportunity_rules_builtin.py

"""
This module defines and registers built-in rules for opportunity finding.
Each rule has a root node of OPR_TO_OPPORTUNITY_RATING.
"""

from typing import List

from itapia_common.rules import names as nms
from itapia_common.rules.rule import Rule
from itapia_common.rules.nodes.registry import create_node
from itapia_common.rules.nodes import _TreeNode
from itapia_common.schemas.entities.rules import SemanticLevel, SemanticType

# ===================================================================
# == A. OPPORTUNITY FINDING RULE CREATION FUNCTIONS
# ===================================================================

def _build_opportunity_rule(rule_id: str, name: str, description: str, logic_tree: _TreeNode) -> Rule:
    """Helper function to wrap logic in an Opportunity Conclusion Operator and create a Rule.
    
    Args:
        rule_id: Unique identifier for the rule
        name: Human-readable name of the rule
        description: Description of what the rule does
        logic_tree: The logical expression tree for the rule
        
    Returns:
        A fully constructed Rule object
    """
    root_node = create_node(
        node_name=nms.OPR_TO_OPPORTUNITY_RATING,  # <<< Note: Using OPPORTUNITY operator
        children=[logic_tree]
    )
    return Rule(
        rule_id=rule_id,
        name=name,
        description=description,
        root=root_node
    )

def _create_rule_1_deep_value_screener() -> Rule:
    """[1] Deep Value Screener: High score if RSI is oversold in a good long-term trend.
    
    Logic: Score = (RSI oversold signal) * (Good long-term trend signal)
    RSI oversold signal: 1 if RSI < 30, 0 otherwise.
    Good long-term trend signal: 1 if uptrend, 0 otherwise.
    Score is 1 only when both conditions are true.
    """
    cond_rsi_oversold = create_node(nms.OPR_LT, children=[create_node(nms.VAR_D_RSI_14), create_node(nms.CONST_RSI_OVERSOLD)])
    cond_long_trend_up = create_node(nms.OPR_EQ, children=[create_node(nms.VAR_D_TREND_LONGTERM_DIR), create_node(nms.CONST_SEMANTIC(SemanticType.TREND, SemanticLevel.HIGH))])
    
    # Use AND, it will return 1.0 if both are true, 0.0 otherwise.
    logic_tree = create_node(nms.OPR_AND, children=[cond_rsi_oversold, cond_long_trend_up])
    
    return _build_opportunity_rule("RULE_O_01_DEEP_VALUE", "Deep Value Screener", "Scores highly for oversold stocks within a long-term uptrend.", logic_tree)

def _create_rule_2_trend_reversal_screener() -> Rule:
    """[2] Trend Reversal Screener: Positive score if there's a reversal signal.
    
    Logic: Score = 0.5 if mid-term trend has just turned up while long-term trend is still down.
    """
    cond_mid_trend_up = create_node(nms.OPR_EQ, children=[create_node(nms.VAR_D_TREND_MIDTERM_DIR), create_node(nms.CONST_SEMANTIC(SemanticType.TREND, SemanticLevel.HIGH))])
    cond_long_trend_down = create_node(nms.OPR_EQ, children=[create_node(nms.VAR_D_TREND_LONGTERM_DIR), create_node(nms.CONST_SEMANTIC(SemanticType.TREND, SemanticLevel.LOW))])
    
    is_reversal_signal = create_node(nms.OPR_AND, children=[cond_mid_trend_up, cond_long_trend_down])
    
    # If there's a reversal signal, return score 0.5 (interesting opportunity), otherwise 0.
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        is_reversal_signal,
        create_node(nms.CONST_NUM(0.5)),  # Score for an "interesting" opportunity
        create_node(nms.CONST_NUM(0.0))
    ])
    
    return _build_opportunity_rule("RULE_O_02_TREND_REVERSAL", "Trend Reversal Screener", "Scores positively for early signs of a trend reversal from bearish to bullish.", logic_tree)

def _create_rule_3_forecast_upside_potential() -> Rule:
    """[3] Forecast Upside Potential Screener: Score is the forecasted upside potential.
    
    Logic: Score = Normalized value of VAR_FC_20D_MAX_PCT.
    This variable is already normalized to [0, 1], so we can use it directly.
    """
    logic_tree = create_node(nms.VAR_FC_5D_MAX_PCT)

    return _build_opportunity_rule("RULE_O_03_FC_UPSIDE", "Forecasted Upside Potential", "Scores based on the normalized forecasted max upside potential.", logic_tree)

def _create_rule_4_bullish_pattern_screener() -> Rule:
    """[4] Bullish Pattern Screener: Score based on the existence of a strong bullish pattern.
    
    Logic: Score = (Bullish pattern signal) * (Pattern score / 100)
    Example: Bull pattern (1.0) with score 80 -> 1.0 * (80/100) = 0.8
    """
    cond_is_bull_pattern = create_node(nms.OPR_GTE, children=[create_node(nms.VAR_D_PATTERN_1_SENTIMENT), create_node(nms.CONST_SEMANTIC(SemanticType.SENTIMENT, SemanticLevel.HIGH))])
    
    # Normalize pattern score (originally 0-100) to range [0, 1]
    normalized_pattern_score = create_node(nms.VAR_D_PATTERN_1_SCORE)
    
    # If it's a bull pattern, return the normalized score, otherwise 0
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_is_bull_pattern,
        normalized_pattern_score,
        create_node(nms.CONST_NUM(0.0))
    ])

    return _build_opportunity_rule("RULE_O_04_BULLISH_PATTERN", "Bullish Pattern Screener", "Scores based on the existence and strength of a bullish pattern.", logic_tree)

def _create_rule_5_news_catalyst_screener() -> Rule:
    """[5] News Catalyst Screener: Score based on density of positive and high-impact news.
    
    Logic: Score = (Positive news score) * (High-impact news score)
    Both variables are already normalized to [0, 1].
    Score will only be high when both factors are high.
    """
    positive_news_score = create_node(nms.VAR_NEWS_SUM_NUM_POSITIVE)
    high_impact_news_score = create_node(nms.VAR_NEWS_SUM_NUM_HIGH_IMPACT)
    
    logic_tree = create_node(nms.OPR_MUL2, children=[positive_news_score, high_impact_news_score])

    return _build_opportunity_rule("RULE_O_05_NEWS_CATALYST", "News Catalyst Screener", "Scores based on the density of positive and high-impact news.", logic_tree)

# ===================================================================
# == B. BUILT-IN OPPORTUNITY RULES COLLECTION
# ===================================================================

_BUILTIN_OPPORTUNITY_RULES: List[Rule] | None = None

def builtin_opportunity_rules() -> List[Rule]:
    """Return a list of built-in opportunity finding rules.
    
    Uses lazy initialization to create the list only once.
    
    Returns:
        List of built-in opportunity rules
    """
    global _BUILTIN_OPPORTUNITY_RULES
    if _BUILTIN_OPPORTUNITY_RULES is not None:
        return _BUILTIN_OPPORTUNITY_RULES
        
    _BUILTIN_OPPORTUNITY_RULES = [
        _create_rule_1_deep_value_screener(),
        _create_rule_2_trend_reversal_screener(),
        _create_rule_3_forecast_upside_potential(),
        _create_rule_4_bullish_pattern_screener(),
        _create_rule_5_news_catalyst_screener(),
    ]
    return _BUILTIN_OPPORTUNITY_RULES