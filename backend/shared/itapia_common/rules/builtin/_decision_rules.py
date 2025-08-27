# itapia_common/rules/_rules_builtin.py

"""
This module defines and registers built-in rules in the system.
Each rule has a root node that is a special Conclusion Operator.
"""

from typing import List

from itapia_common.rules import names as nms
from itapia_common.rules.rule import Rule
from itapia_common.rules.nodes.registry import create_node
from itapia_common.rules.nodes import _TreeNode
from itapia_common.schemas.entities.rules import SemanticLevel, SemanticType

# ===================================================================
# == A. DECISION MAKING RULE CREATION FUNCTIONS
# ===================================================================

def _build_rule(rule_id: str, name: str, description: str, logic_tree: _TreeNode) -> Rule:
    """Helper function to wrap logic in a Conclusion Operator and create a Rule."""
    root_node = create_node(
        node_name=nms.OPR_TO_DECISION_SIGNAL,
        children=[logic_tree]
    )
    return Rule(
        rule_id=rule_id,
        name=name,
        description=description,
        root=root_node
    )

def _create_rule_1_trend_following() -> Rule:
    """[1] Trend Following: Calculate score based on trend consensus."""
    # Logic: Score = (Mid-term trend score + Long-term trend score) / 2
    # Each trend has a score: uptrend=1, downtrend=-1, undefined=0
    mid_term_trend = create_node(nms.VAR_D_TREND_MIDTERM_DIR)
    long_term_trend = create_node(nms.VAR_D_TREND_LONGTERM_DIR)
    
    sum_of_trends = create_node(nms.OPR_ADD2, children=[mid_term_trend, long_term_trend])
    sum_of_trends_num = create_node(nms.OPR_TO_NUMERICAL, children=[sum_of_trends])
    
    logic_tree = create_node(nms.OPR_DIV2, children=[sum_of_trends_num, create_node(nms.CONST_NUM(2.0))])
    
    return _build_rule("RULE_D_01_TREND_FOLLOW", "Trend Following Score", "Calculates a score based on the alignment of mid and long-term trends.", logic_tree)

def _create_rule_2_rsi_momentum() -> Rule:
    """[2] RSI Momentum: Convert normalized RSI value to a direct signal."""
    # Logic: Score = Normalized RSI value (from -1 to 1)
    # Example: RSI=70 -> normalized ~0.4. RSI=30 -> normalized ~ -0.4.
    # This rule assumes RSI itself is already a signal.
    logic_tree = create_node(nms.VAR_D_RSI_14)
    
    return _build_rule("RULE_D_02_RSI_MOMENTUM", "RSI Momentum Score", "Uses the normalized RSI value directly as a momentum signal.", logic_tree)

def _create_rule_3_ml_forecast_confidence() -> Rule:
    """[3] AI Confidence: Use forecast probability as score."""
    # Logic: Score = Win Probability - Loss Probability
    # This creates a score from -1 to 1, reflecting model certainty.
    prob_win = create_node(nms.VAR_FC_TB_PREDICTION)
    prob_loss = create_node(nms.VAR_FC_5D_MEAN_PCT)
    
    logic_tree = create_node(nms.OPR_SUB2, children=[prob_win, prob_loss])
    
    return _build_rule("RULE_D_03_ML_CONFIDENCE", "ML Forecast Confidence", "Calculates a score based on the confidence (Prob_Win - Prob_Loss) of the ML model.", logic_tree)

def _create_rule_4_news_sentiment_balance() -> Rule:
    """[4] News Sentiment Balance: Calculate score based on difference between positive and negative news."""
    # Logic: Score = (Number of positive news - Number of negative news) / (Total news + 1)
    # This formula normalizes the score to [-1, 1] and handles division by zero.
    num_pos = create_node(nms.VAR_NEWS_SUM_NUM_POSITIVE)
    num_neg = create_node(nms.VAR_NEWS_SUM_NUM_NEGATIVE)
    
    numerator = create_node(nms.OPR_SUB2, children=[num_pos, num_neg])
    numerator_num = create_node(nms.OPR_TO_NUMERICAL, children=[numerator])
    denominator_sum = create_node(nms.OPR_ADD2, children=[num_pos, num_neg])
    denominator_sum_num = create_node(nms.OPR_TO_NUMERICAL, children=[denominator_sum])
    denominator_sum_div = create_node(nms.OPR_ADD2, children=[denominator_sum_num, create_node(nms.CONST_NUM(1.0))])
    
    logic_tree = create_node(nms.OPR_DIV2, children=[numerator_num, denominator_sum_div])
    
    return _build_rule("RULE_D_04_NEWS_BALANCE", "News Sentiment Balance", "Calculates a score based on the ratio of positive to negative news.", logic_tree)

def _create_rule_5_trend_strength_confirmation() -> Rule:
    """[5] Trend Strength Confirmation: Stronger signal when trend is strong."""
    # Logic: Score = Trend direction * Trend strength
    # Example: Uptrend (1.0) + Strong (1.0) -> 1.0. Uptrend (1.0) + Weak (0.2) -> 0.2
    trend_direction = create_node(nms.VAR_D_TREND_MIDTERM_DIR)
    trend_strength = create_node(nms.VAR_D_TREND_OVERALL_STRENGTH)
    
    logic_tree = create_node(nms.OPR_MUL2, children=[trend_direction, trend_strength])
    
    return _build_rule("RULE_D_05_TREND_STRENGTH", "Trend Strength Confirmation", "Amplifies trend signal by its strength.", logic_tree)

def _create_rule_6_pattern_sentiment() -> Rule:
    """[6] Pattern Signal: Use signal from the most prominent pattern."""
    # Logic: Score = Pattern signal (bull=1, bear=-1, neutral=0)
    # This is a direct signal.
    logic_tree = create_node(nms.VAR_D_PATTERN_1_SENTIMENT)
    
    return _build_rule("RULE_D_06_PATTERN_SENTIMENT", "Pattern Sentiment Signal", "Uses the sentiment of the most prominent pattern directly as a signal.", logic_tree)

def _create_rule_7_mean_reversion_fading() -> Rule:
    """[7] Mean Reversion Trading: Sell signal when RSI is overbought, buy signal when oversold."""
    # Logic: If RSI > 70, sell signal (-1). If RSI < 30, buy signal (1).
    # Note: This is a pure contrarian rule, not filtered by trend.
    cond_overbought = create_node(nms.OPR_GT, children=[create_node(nms.VAR_D_RSI_14), create_node(nms.CONST_RSI_OVERBOUGHT)])
    cond_oversold = create_node(nms.OPR_LT, children=[create_node(nms.VAR_D_RSI_14), create_node(nms.CONST_RSI_OVERSOLD)])
    
    inner_if = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_oversold, create_node(nms.CONST_NUM(1.0)), create_node(nms.CONST_NUM(0.0))
    ])
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_overbought, create_node(nms.CONST_NUM(-1.0)), inner_if
    ])
    
    return _build_rule("RULE_D_07_MEAN_REVERSION_FADE", "Mean Reversion Fading", "Generates a contrarian signal based on RSI overbought/oversold levels.", logic_tree)

def _create_rule_8_forecast_potential() -> Rule:
    """[8] Forecast Potential: Balance between upside and downside potential."""
    # Logic: Score = Max upside forecast + Min downside forecast
    # (max_pct is positive, min_pct is negative, so this is addition)
    # Example: max_pct=0.8 (+10%), min_pct=-0.2 (-2%) -> Score = 0.6 (biased toward upside)
    max_upside = create_node(nms.VAR_FC_5D_MAX_PCT)
    max_downside = create_node(nms.VAR_FC_5D_MIN_PCT)
    const_2 = create_node(nms.CONST_NUM(2.0))
    
    sub_tree = create_node(nms.OPR_SUB2, children=[max_upside, max_downside])
    sub_tree_num = create_node(nms.OPR_TO_NUMERICAL, children=[sub_tree])
    sub_tree2 = create_node(nms.OPR_SUB2, children=[const_2, sub_tree_num])
    logic_tree = create_node(nms.OPR_DIV2, children=[sub_tree2, const_2])
    return _build_rule("RULE_D_08_FC_POTENTIAL", "Forecasted Potential Score", "Balances the forecasted max upside against the max downside.", logic_tree)

def _create_rule_9_intraday_momentum() -> Rule:
    """[9] Intraday Momentum: Signal based on opening range breakout."""
    # Logic: Score = ORB signal (bull-breakout=1, bear-breakdown=-1, inside=0)
    logic_tree = create_node(nms.VAR_I_ORB_STATUS)
    
    return _build_rule("RULE_D_09_INTRADAY_MOMENTUM", "Intraday Breakout Momentum", "Signal based on intraday opening range breakout status.", logic_tree)

def _create_rule_10_high_impact_news_direction() -> Rule:
    """[10] High-Impact News Direction: Calculate score based on sentiment of high-impact news."""
    # Logic: (Number of positive & high-impact news * 1) + (Number of negative & high-impact news * -1)
    # This is a more complex rule, we'll simplify it:
    # Logic: If high-impact news exists, the score will be the sentiment of the latest news.
    cond_has_high_impact = create_node(nms.OPR_GTE, children=[create_node(nms.VAR_NEWS_SUM_NUM_HIGH_IMPACT), create_node(nms.CONST_SEMANTIC(SemanticType.SENTIMENT, SemanticLevel.HIGH))])
    latest_news_sentiment = create_node(nms.VAR_NEWS_SUM_NUM_POSITIVE)
    latest_news_sentiment_num = create_node(nms.OPR_TO_NUMERICAL, children=[latest_news_sentiment])
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_has_high_impact, latest_news_sentiment_num, create_node(nms.CONST_NUM(0.0))
    ])
    
    return _build_rule("RULE_D_10_HIGH_IMPACT_NEWS", "High-Impact News Direction", "Signal is driven by the sentiment of the latest news, only if high-impact news exists.", logic_tree)

# ===================================================================
# == B. BUILT-IN DECISION RULES REGISTRY
# ===================================================================
_BUILTIN_DECISION_RULES: List[Rule] | None = None

def builtin_decision_rules() -> List[Rule]:
    global _BUILTIN_DECISION_RULES
    
    if _BUILTIN_DECISION_RULES is not None:
        return _BUILTIN_DECISION_RULES
    
    # Initialize the list of built-in decision rules
    _BUILTIN_DECISION_RULES = [
        _create_rule_1_trend_following(),
        _create_rule_2_rsi_momentum(),
        _create_rule_3_ml_forecast_confidence(),
        _create_rule_4_news_sentiment_balance(),
        _create_rule_5_trend_strength_confirmation(),
        _create_rule_6_pattern_sentiment(),
        _create_rule_7_mean_reversion_fading(),
        _create_rule_8_forecast_potential(),
        _create_rule_9_intraday_momentum(),
        _create_rule_10_high_impact_news_direction()
    ]
    
    return _BUILTIN_DECISION_RULES