# itapia_common/rules/_risk_rules_builtin.py

"""
This module defines and registers built-in rules for risk management.
Each rule has a root node of OPR_TO_RISK_LEVEL.
"""

from typing import List

from itapia_common.rules import names as nms
from itapia_common.rules.nodes import _TreeNode
from itapia_common.rules.nodes.registry import create_node
from itapia_common.rules.rule import Rule
from itapia_common.schemas.entities.rules import SemanticLevel, SemanticType

# ===================================================================
# == A. RISK MANAGEMENT RULE CREATION FUNCTIONS
# ===================================================================


def _build_risk_rule(
    rule_id: str, name: str, description: str, logic_tree: _TreeNode
) -> Rule:
    """Helper function to wrap logic in a Risk Conclusion Operator and create a Rule.

    Args:
        rule_id: Unique identifier for the rule
        name: Human-readable name of the rule
        description: Description of what the rule does
        logic_tree: The logical expression tree for the rule

    Returns:
        A fully constructed Rule object
    """
    root_node = create_node(
        node_name=nms.OPR_TO_RISK_LEVEL,  # <<< Note: Using RISK operator
        children=[logic_tree],
    )
    return Rule(rule_id=rule_id, name=name, description=description, root=root_node)


def _create_rule_1_volatility_risk() -> Rule:
    """[1] Volatility Risk: The risk score is the normalized volatility level.

    Logic: Risk score = Normalized value of VAR_D_ATR_14.
    This variable is already normalized to [0, 1], with higher values indicating greater volatility.
    """
    logic_tree = create_node(nms.VAR_D_ATR_14)

    return _build_risk_rule(
        "RULE_R_01_VOLATILITY_RISK",
        "Volatility Risk Score",
        "Scores risk based on the normalized ATR value.",
        logic_tree,
    )


def _create_rule_2_weak_trend_risk() -> Rule:
    """[2] Weak Trend Risk: Higher risk when the trend is unclear.

    Logic: Risk score = 1.0 - Trend strength.
    If trend is strong (strength=1.0), risk is 0. If trend is weak (strength=0.2), risk is 0.8.
    """
    trend_strength = create_node(nms.VAR_D_TREND_OVERALL_STRENGTH)

    logic_tree = create_node(
        nms.OPR_SUB2,
        children=[
            create_node(nms.CONST_NUM(1.0)),
            create_node(nms.OPR_TO_NUMERICAL, children=[trend_strength]),
        ],
    )

    return _build_risk_rule(
        "RULE_R_02_WEAK_TREND_RISK",
        "Weak Trend Risk",
        "Scores higher risk when the trend strength is weaker.",
        logic_tree,
    )


def _create_rule_3_forecasted_downside_risk() -> Rule:
    """[3] Forecasted Downside Risk: Risk score is the forecasted downside potential.

    Logic: Risk score = abs(Normalized value of VAR_FC_5D_MIN_PCT).
    The VAR_FC_5D_MIN_PCT variable has values from -1 to 0. Taking the absolute value converts it to [0, 1].
    Greater downside potential (e.g., -10% -> normalized -1.0) results in higher risk score (1.0).
    """
    max_downside = create_node(nms.VAR_FC_5D_MIN_PCT)

    logic_tree = create_node(nms.OPR_ABS, children=[max_downside])

    return _build_risk_rule(
        "RULE_R_03_FC_DOWNSIDE_RISK",
        "Forecasted Downside Risk",
        "Scores risk based on the absolute normalized forecasted max downside.",
        logic_tree,
    )


def _create_rule_4_negative_news_risk() -> Rule:
    """[4] Negative News Risk: Risk score is the level of negative news.

    Logic: Risk score = Normalized value of VAR_NEWS_SUM_NUM_NEGATIVE.
    This variable is already normalized to [0, 1], with higher values indicating more negative news.
    """
    logic_tree = create_node(nms.VAR_NEWS_SUM_NUM_NEGATIVE)

    return _build_risk_rule(
        "RULE_R_04_NEGATIVE_NEWS_RISK",
        "Negative News Risk",
        "Scores risk based on the normalized count of negative news.",
        logic_tree,
    )


def _create_rule_5_overextended_risk() -> Rule:
    """[5] Overextended Market Risk: High risk score if RSI is in overbought territory.

    Logic: If RSI > 50, risk score begins to increase linearly.
           If RSI < 50, risk score is 0.
    Formula: max(0, (normalized_RSI - 0)) -> because RSI=50 is normalized to 0.
    """
    # RSI > 50 (normalized value is 0)
    cond_is_bullish_territory = create_node(
        nms.OPR_GT,
        children=[
            create_node(nms.VAR_D_RSI_14),
            create_node(
                nms.CONST_SEMANTIC(SemanticType.MOMENTUM, SemanticLevel.MODERATE)
            ),
        ],
    )

    # If true, risk score is the normalized RSI value.
    # If false, risk score is 0.
    logic_tree = create_node(
        nms.OPR_IF_THEN_ELSE,
        children=[
            cond_is_bullish_territory,
            create_node(nms.VAR_D_RSI_14),
            create_node(
                nms.CONST_SEMANTIC(SemanticType.MOMENTUM, SemanticLevel.MODERATE)
            ),
        ],
    )

    return _build_risk_rule(
        "RULE_R_05_OVEREXTENDED_RISK",
        "Overextended Market Risk",
        "Scores higher risk as RSI moves deeper into overbought territory (>50).",
        logic_tree,
    )


# ===================================================================
# == B. BUILT-IN RISK RULES COLLECTION
# ===================================================================

_BUILTIN_RISK_RULES: List[Rule] | None = None


def builtin_risk_rules() -> List[Rule]:
    """Return a list of built-in risk management rules.

    Uses lazy initialization to create the list only once.

    Returns:
        List of built-in risk rules
    """
    global _BUILTIN_RISK_RULES
    if _BUILTIN_RISK_RULES is not None:
        return _BUILTIN_RISK_RULES

    _BUILTIN_RISK_RULES = [
        _create_rule_1_volatility_risk(),
        _create_rule_2_weak_trend_risk(),
        _create_rule_3_forecasted_downside_risk(),
        _create_rule_4_negative_news_risk(),
        _create_rule_5_overextended_risk(),
    ]
    return _BUILTIN_RISK_RULES
