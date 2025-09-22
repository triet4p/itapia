# itapia_common/rules/nodes/_variable_nodes_builtin.py

"""
This module defines and registers all built-in VarNode instances in the system.
These variables extract data directly from QuickCheckReport.
"""

from itapia_common.rules import names as nms
from itapia_common.rules.nodes import CategoricalVarNode, NumericalVarNode
from itapia_common.rules.nodes.registry import NodeSpec, register_node_by_spec
from itapia_common.schemas.entities.rules import NodeType, SemanticType

# ===================================================================
# == A. VARIABLES FROM DAILY TECHNICAL ANALYSIS REPORT
# ===================================================================

# --- A.1. From Key Indicators ---

register_node_by_spec(
    nms.VAR_D_RSI_14,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Daily RSI (14-period), normalized to [-1, 1]",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.MOMENTUM,
        params={
            "path": "technical_report.daily_report.key_indicators.rsi_14",
            "source_range": (0, 100),
            "target_range": (-1, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_D_ADX_14,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Daily ADX (14-period), normalized to [-1, 1]",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.TREND,
        params={
            "path": "technical_report.daily_report.key_indicators.adx_14",
            "source_range": (0, 100),
            "target_range": (-1, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_D_ATR_14,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Daily ATR (14-period) as a percentage of close price, normalized to [0, 1]",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.VOLATILITY,
        # Assume 10% ATR is very high
        params={
            "path": "technical_report.daily_report.key_indicators.atr_14",
            "source_range": (0, 15),
            "target_range": (0, 1),
        },
    ),
)
# --- A.2. From Trend Report ---

register_node_by_spec(
    nms.VAR_D_TREND_MIDTERM_DIR,
    NodeSpec(
        node_class=CategoricalVarNode,
        description="Mid-term trend direction (MA based)",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.TREND,
        params={
            "path": "technical_report.daily_report.trend_report.midterm_report.ma_direction",
            "mapping": {"uptrend": 1.0, "downtrend": -1.0, "undefined": 0.0},
        },
    ),
)
register_node_by_spec(
    nms.VAR_D_TREND_LONGTERM_DIR,
    NodeSpec(
        node_class=CategoricalVarNode,
        description="Long-term trend direction (MA based)",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.TREND,
        params={
            "path": "technical_report.daily_report.trend_report.longterm_report.ma_direction",
            "mapping": {"uptrend": 1.0, "downtrend": -1.0, "undefined": 0.0},
        },
    ),
)
register_node_by_spec(
    nms.VAR_D_TREND_OVERALL_STRENGTH,
    NodeSpec(
        node_class=CategoricalVarNode,
        description="Overall trend strength",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.TREND,
        params={
            "path": "technical_report.daily_report.trend_report.overall_strength.strength",
            "mapping": {"strong": 1.0, "moderate": 0.5, "weak": 0.2, "undefined": 0.0},
        },
    ),
)

# --- A.3. From Support/Resistance Report ---
# Assumption: Take the price level of the most important threshold (first in the list)
register_node_by_spec(
    nms.VAR_D_SUPPORT_1_PRICE,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Price level of the nearest support",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.PRICE,
        params={
            "path": "technical_report.daily_report.sr_report.supports.0.level",
            "source_range": (0, 200),
            "target_range": (0, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_D_RESISTANCE_1_PRICE,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Price level of the nearest resistance",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.PRICE,
        params={
            "path": "technical_report.daily_report.sr_report.resistances.0.level",
            "source_range": (0, 200),
            "target_range": (0, 1),
        },
    ),
)

# --- A.4. From Pattern Report ---
# Assumption: Take information of the most prominent pattern (first in the list)
register_node_by_spec(
    nms.VAR_D_PATTERN_1_SCORE,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Score of the most prominent recognized pattern",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.NUMERICAL,
        params={
            "path": "technical_report.daily_report.pattern_report.top_patterns.0.score",
            "source_range": (0, 100),
            "target_range": (0, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_D_PATTERN_1_SENTIMENT,
    NodeSpec(
        node_class=CategoricalVarNode,
        description="Sentiment of the most prominent pattern (bull/bear)",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.BOOLEAN,
        params={
            "path": "technical_report.daily_report.pattern_report.top_patterns.0.sentiment",
            "mapping": {"bull": 1.0, "bear": -1.0, "neutral": 0.0},
        },
    ),
)


# ===================================================================
# == B. VARIABLES FROM INTRADAY TECHNICAL ANALYSIS REPORT
# ===================================================================

register_node_by_spec(
    nms.VAR_I_RSI_STATUS,
    NodeSpec(
        node_class=CategoricalVarNode,
        description="Intraday RSI status (overbought/oversold)",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.MOMENTUM,
        params={
            "path": "technical_report.intraday_report.current_status_report.rsi_status",
            "mapping": {"overbought": 1.0, "oversold": -1.0, "neutral": 0.0},
        },
    ),
)
register_node_by_spec(
    nms.VAR_I_MACD_CROSSOVER,
    NodeSpec(
        node_class=CategoricalVarNode,
        description="Intraday MACD crossover status (bull/bear)",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.MOMENTUM,
        params={
            "path": "technical_report.intraday_report.momentum_report.macd_crossover",
            "mapping": {"bull": 1.0, "bear": -1.0, "neutral": 0.0},
        },
    ),
)
register_node_by_spec(
    nms.VAR_I_ORB_STATUS,
    NodeSpec(
        node_class=CategoricalVarNode,
        description="Intraday Opening Range Breakout status",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.MOMENTUM,
        params={
            "path": "technical_report.intraday_report.momentum_report.opening_range_status",
            "mapping": {"bull-breakout": 1.0, "bear-breakdown": -1.0, "inside": 0.0},
        },
    ),
)

# ===================================================================
# == C. VARIABLES FROM FORECASTING REPORT - UPDATED
# ===================================================================

# --- C.1. From Triple Barrier Classification task (forecasts[0]) ---
register_node_by_spec(
    nms.VAR_FC_TB_PREDICTION,
    NodeSpec(
        CategoricalVarNode,
        "Forecasted trade outcome (-1: loss, 0: timeout, 1: win)",
        return_type=SemanticType.NUMERICAL,
        node_type=NodeType.VARIABLE,
        # Values are already -1, 0, 1 so no mapping needed
        params={
            "path": "forecasting_report.forecasts.0.prediction.0",
            "mapping": {-1: -1.0, 0: 0.0, 1: 1.0},
        },
    ),
)

# --- C.2. From 5-Day Distribution Regression task (forecasts[1]) ---
register_node_by_spec(
    nms.VAR_FC_5D_MEAN_PCT,
    NodeSpec(
        NumericalVarNode,
        "Forecasted mean price change in 5 days (%)",
        return_type=SemanticType.PERCENTAGE,
        node_type=NodeType.VARIABLE,
        # Assume 5% change in 5 days is large
        params={
            "path": "forecasting_report.forecasts.1.prediction.0",
            "source_range": (-2, 2),
            "target_range": (-1, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_FC_5D_STD_PCT,
    NodeSpec(
        NumericalVarNode,
        "Forecasted price volatility (std) in 5 days (%)",
        return_type=SemanticType.VOLATILITY,
        node_type=NodeType.VARIABLE,
        # Assume 5% standard deviation is very high
        params={
            "path": "forecasting_report.forecasts.1.prediction.1",
            "source_range": (0, 2.5),
            "target_range": (0, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_FC_5D_MAX_PCT,
    NodeSpec(
        NumericalVarNode,
        "Forecasted max potential upside in 5 days (%)",
        return_type=SemanticType.PERCENTAGE,
        node_type=NodeType.VARIABLE,
        params={
            "path": "forecasting_report.forecasts.1.prediction.3",
            "source_range": (-2.5, 2.5),
            "target_range": (-1, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_FC_5D_MIN_PCT,
    NodeSpec(
        NumericalVarNode,
        "Forecasted max potential downside in 5 days (%)",
        return_type=SemanticType.PERCENTAGE,
        node_type=NodeType.VARIABLE,
        params={
            "path": "forecasting_report.forecasts.1.prediction.2",
            "source_range": (-2.5, 2.5),
            "target_range": (-1, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_FC_5D_Q25_PCT,
    NodeSpec(
        NumericalVarNode,
        "Forecasted q25 price change in 5 days (%)",
        return_type=SemanticType.PERCENTAGE,
        node_type=NodeType.VARIABLE,
        # Assume 5% change in 5 days is large
        params={
            "path": "forecasting_report.forecasts.1.prediction.4",
            "source_range": (-2.5, 2.5),
            "target_range": (-1, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_FC_5D_Q75_PCT,
    NodeSpec(
        NumericalVarNode,
        "Forecasted q75 price change in 5 days (%)",
        return_type=SemanticType.PERCENTAGE,
        node_type=NodeType.VARIABLE,
        # Assume 5% change in 5 days is large
        params={
            "path": "forecasting_report.forecasts.1.prediction.5",
            "source_range": (-2.5, 2.5),
            "target_range": (-1, 1),
        },
    ),
)

# --- C.3. From 20-Day Distribution Regression task (forecasts[2]) ---
register_node_by_spec(
    nms.VAR_FC_20D_MEAN_PCT,
    NodeSpec(
        NumericalVarNode,
        "Forecasted mean price change in 20 days (%)",
        return_type=SemanticType.PERCENTAGE,
        node_type=NodeType.VARIABLE,
        # Assume 10% change in 20 days is large
        params={
            "path": "forecasting_report.forecasts.2.prediction.0",
            "source_range": (-2.5, 2.5),
            "target_range": (-1, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_FC_20D_STD_PCT,
    NodeSpec(
        NumericalVarNode,
        "Forecasted price volatility (std) in 20 days (%)",
        return_type=SemanticType.VOLATILITY,
        node_type=NodeType.VARIABLE,
        # Assume 10% standard deviation is very high
        params={
            "path": "forecasting_report.forecasts.2.prediction.1",
            "source_range": (0, 3.5),
            "target_range": (0, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_FC_20D_MAX_PCT,
    NodeSpec(
        NumericalVarNode,
        "Forecasted max potential upside in 20 days (%)",
        return_type=SemanticType.PERCENTAGE,
        node_type=NodeType.VARIABLE,
        params={
            "path": "forecasting_report.forecasts.2.prediction.3",
            "source_range": (-3, 3),
            "target_range": (-1, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_FC_20D_MIN_PCT,
    NodeSpec(
        NumericalVarNode,
        "Forecasted max potential downside in 20 days (%)",
        return_type=SemanticType.PERCENTAGE,
        node_type=NodeType.VARIABLE,
        params={
            "path": "forecasting_report.forecasts.2.prediction.2",
            "source_range": (-3, 3),
            "target_range": (-1, 1),
        },
    ),
)

# ===================================================================
# == D. VARIABLES FROM NEWS ANALYSIS REPORT
# == Using fields already aggregated in SummaryReport
# ===================================================================

# --- D.1. Count-based Variables ---

register_node_by_spec(
    nms.VAR_NEWS_SUM_NUM_POSITIVE,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Summary: Total number of news with positive sentiment",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.SENTIMENT,
        # Assume: 5 positive news is a very strong signal
        params={
            "path": "news_report.summary.num_positive_sentiment",
            "source_range": (0, 5),
            "target_range": (0, 1),
        },
    ),
)

register_node_by_spec(
    nms.VAR_NEWS_SUM_NUM_NEGATIVE,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Summary: Total number of news with negative sentiment",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.SENTIMENT,
        # Assume: 5 negative news is a very strong signal (normalized value is 1.0, but meaning is negative)
        params={
            "path": "news_report.summary.num_negative_sentiment",
            "source_range": (0, 5),
            "target_range": (0, 1),
        },
    ),
)

register_node_by_spec(
    nms.VAR_NEWS_SUM_NUM_HIGH_IMPACT,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Summary: Total number of news assessed as high impact",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.SENTIMENT,
        params={
            "path": "news_report.summary.num_high_impact",
            "source_range": (0, 3),
            "target_range": (0, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_NEWS_SUM_NUM_MODERATE_IMPACT,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Summary: Total number of news assessed as high impact",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.SENTIMENT,
        params={
            "path": "news_report.summary.num_moderate_impact",
            "source_range": (0, 3),
            "target_range": (0, 1),
        },
    ),
)
register_node_by_spec(
    nms.VAR_NEWS_SUM_NUM_LOW_IMPACT,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Summary: Total number of news assessed as high impact",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.SENTIMENT,
        params={
            "path": "news_report.summary.num_low_impact",
            "source_range": (0, 3),
            "target_range": (0, 1),
        },
    ),
)
# --- D.2. Ratio/Average-based Variables ---

register_node_by_spec(
    nms.VAR_NEWS_SUM_AVG_POSITIVE_KEYWORDS,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Summary: Average number of positive keywords found per news item",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.SENTIMENT,
        # Assume: Average 3 positive keywords/news is a strong signal
        params={
            "path": "news_report.summary.avg_of_positive_keyword_found",
            "source_range": (0, 2),
            "target_range": (0, 1),
        },
    ),
)

register_node_by_spec(
    nms.VAR_NEWS_SUM_AVG_NEGATIVE_KEYWORDS,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Summary: Average number of negative keywords found per news item",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.SENTIMENT,
        params={
            "path": "news_report.summary.avg_of_negative_keyword_found",
            "source_range": (0, 2),
            "target_range": (0, 1),
        },
    ),
)

register_node_by_spec(
    nms.VAR_NEWS_SUM_AVG_NER,
    NodeSpec(
        node_class=NumericalVarNode,
        description="Summary: Average number of named entities found per news item",
        node_type=NodeType.VARIABLE,
        return_type=SemanticType.SENTIMENT,
        # Assume: Average 5 entities/news indicates very specific and trustworthy news
        params={
            "path": "news_report.summary.avg_of_ner_found",
            "source_range": (0, 4),
            "target_range": (0, 1),
        },
    ),
)
