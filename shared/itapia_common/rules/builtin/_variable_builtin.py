# itapia_common/rules/nodes/_variable_nodes_builtin.py

"""
Tệp này định nghĩa và đăng ký tất cả các VarNode dựng sẵn trong hệ thống.
Các biến này trích xuất dữ liệu trực tiếp từ QuickCheckReport.
"""

from itapia_common.rules.nodes.registry import register_node_by_spec, NodeSpec
from itapia_common.rules.nodes import NumericalVarNode, CategoricalVarNode
from itapia_common.schemas.enums import SemanticType
from itapia_common.rules import names as nms

# ===================================================================
# == A. BIẾN TỪ BÁO CÁO PHÂN TÍCH KỸ THUẬT - KHUNG NGÀY (DAILY)
# ===================================================================

# --- A.1. Từ các chỉ báo chính (Key Indicators) ---

register_node_by_spec(nms.VAR_D_RSI_14, NodeSpec(
    node_class=NumericalVarNode,
    description='Daily RSI (14-period), normalized to [-1, 1]',
    node_type='variable',
    return_type=SemanticType.MOMENTUM,
    params={'path': 'technical_report.daily_report.key_indicators.rsi_14', 'source_range': (0, 100), 'target_range': (-1, 1)}
))
register_node_by_spec(nms.VAR_D_ADX_14, NodeSpec(
    node_class=NumericalVarNode,
    description='Daily ADX (14-period), normalized to [-1, 1]',
    node_type='variable',
    return_type=SemanticType.TREND,
    params={'path': 'technical_report.daily_report.key_indicators.adx_14', 'source_range': (0, 100), 'target_range': (-1, 1)}
))
register_node_by_spec(nms.VAR_D_ATR_14, NodeSpec(
    node_class=NumericalVarNode,
    description='Daily ATR (14-period) as a percentage of close price, normalized to [0, 1]',
    node_type='variable',
    return_type=SemanticType.VOLATILITY,
    # Giả định ATR 10% là rất cao
    params={'path': 'technical_report.daily_report.key_indicators.atr_14', 'source_range': (0, 15), 'target_range': (0, 1)}
))
# --- A.2. Từ báo cáo xu hướng (Trend Report) ---

register_node_by_spec(nms.VAR_D_TREND_MIDTERM_DIR, NodeSpec(
    node_class=CategoricalVarNode,
    description='Mid-term trend direction (MA based)',
    node_type='variable',
    return_type=SemanticType.TREND,
    params={
        'path': 'technical_report.daily_report.trend_report.midterm_report.ma_direction',
        'mapping': {'uptrend': 1.0, 'downtrend': -1.0, 'undefined': 0.0}
    }
))
register_node_by_spec(nms.VAR_D_TREND_LONGTERM_DIR, NodeSpec(
    node_class=CategoricalVarNode,
    description='Long-term trend direction (MA based)',
    node_type='variable',
    return_type=SemanticType.TREND,
    params={
        'path': 'technical_report.daily_report.trend_report.longterm_report.ma_direction',
        'mapping': {'uptrend': 1.0, 'downtrend': -1.0, 'undefined': 0.0}
    }
))
register_node_by_spec(nms.VAR_D_TREND_OVERALL_STRENGTH, NodeSpec(
    node_class=CategoricalVarNode,
    description='Overall trend strength',
    node_type='variable',
    return_type=SemanticType.TREND,
    params={
        'path': 'technical_report.daily_report.trend_report.overall_strength.strength',
        'mapping': {'strong': 1.0, 'moderate': 0.5, 'weak': 0.2, 'undefined': 0.0}
    }
))

# --- A.3. Từ báo cáo Hỗ trợ/Kháng cự (S/R Report) ---
# Giả định: Lấy mức giá của ngưỡng quan trọng nhất (đầu tiên trong danh sách)
register_node_by_spec(nms.VAR_D_SUPPORT_1_PRICE, NodeSpec(
    node_class=NumericalVarNode,
    description='Price level of the nearest support',
    node_type='variable',
    return_type=SemanticType.PRICE,
    params={'path': 'technical_report.daily_report.sr_report.supports.0.level', 'source_range': (0, 200), 'target_range': (0, 1)}
))
register_node_by_spec(nms.VAR_D_RESISTANCE_1_PRICE, NodeSpec(
    node_class=NumericalVarNode,
    description='Price level of the nearest resistance',
    node_type='variable',
    return_type=SemanticType.PRICE,
    params={'path': 'technical_report.daily_report.sr_report.resistances.0.level', 'source_range': (0, 200), 'target_range': (0, 1)}
))

# --- A.4. Từ báo cáo Mẫu hình (Pattern Report) ---
# Giả định: Lấy thông tin của mẫu hình quan trọng nhất (đầu tiên trong danh sách)
register_node_by_spec(nms.VAR_D_PATTERN_1_SCORE, NodeSpec(
    node_class=NumericalVarNode,
    description='Score of the most prominent recognized pattern',
    node_type='variable',
    return_type=SemanticType.NUMERICAL,
    params={'path': 'technical_report.daily_report.pattern_report.top_patterns.0.score', 'source_range': (0, 100), 'target_range': (0, 1)}
))
register_node_by_spec(nms.VAR_D_PATTERN_1_SENTIMENT, NodeSpec(
    node_class=CategoricalVarNode,
    description='Sentiment of the most prominent pattern (bull/bear)',
    node_type='variable',
    return_type=SemanticType.BOOLEAN,
    params={
        'path': 'technical_report.daily_report.pattern_report.top_patterns.0.sentiment',
        'mapping': {'bull': 1.0, 'bear': -1.0, 'neutral': 0.0}
    }
))


# ===================================================================
# == B. BIẾN TỪ BÁO CÁO PHÂN TÍCH KỸ THUẬT - TRONG NGÀY (INTRADAY)
# ===================================================================

register_node_by_spec(nms.VAR_I_RSI_STATUS, NodeSpec(
    node_class=CategoricalVarNode,
    description='Intraday RSI status (overbought/oversold)',
    node_type='variable',
    return_type=SemanticType.MOMENTUM,
    params={
        'path': 'technical_report.intraday_report.current_status_report.rsi_status',
        'mapping': {'overbought': 1.0, 'oversold': -1.0, 'neutral': 0.0}
    }
))
register_node_by_spec(nms.VAR_I_MACD_CROSSOVER, NodeSpec(
    node_class=CategoricalVarNode,
    description='Intraday MACD crossover status (bull/bear)',
    node_type='variable',
    return_type=SemanticType.MOMENTUM,
    params={
        'path': 'technical_report.intraday_report.momentum_report.macd_crossover',
        'mapping': {'bull': 1.0, 'bear': -1.0, 'neutral': 0.0}
    }
))
register_node_by_spec(nms.VAR_I_ORB_STATUS, NodeSpec(
    node_class=CategoricalVarNode,
    description='Intraday Opening Range Breakout status',
    node_type='variable',
    return_type=SemanticType.MOMENTUM,
    params={
        'path': 'technical_report.intraday_report.momentum_report.opening_range_status',
        'mapping': {'bull-breakout': 1.0, 'bear-breakdown': -1.0, 'inside': 0.0}
    }
))

# ===================================================================
# == C. BIẾN TỪ BÁO CÁO DỰ BÁO (FORECASTING) - ĐÃ CẬP NHẬT
# ===================================================================

# --- C.1. Từ task Triple Barrier Classification (forecasts[0]) ---
register_node_by_spec(nms.VAR_FC_TB_PREDICTION, NodeSpec(
    CategoricalVarNode, 'Forecasted trade outcome (-1: loss, 0: timeout, 1: win)',
    return_type=SemanticType.NUMERICAL, node_type='variable',
    # Giá trị đã là -1, 0, 1 nên không cần mapping
    params={'path': 'forecasting_report.forecasts.0.prediction.0', 'mapping': {-1: -1.0, 0: 0.0, 1: 1.0}}
))

# --- C.2. Từ task 5-Day Distribution Regression (forecasts[1]) ---
register_node_by_spec(nms.VAR_FC_5D_MEAN_PCT, NodeSpec(
    NumericalVarNode, 'Forecasted mean price change in 5 days (%)',
    return_type=SemanticType.PERCENTAGE, node_type='variable',
    # Giả định thay đổi 5% trong 5 ngày là lớn
    params={'path': 'forecasting_report.forecasts.1.prediction.0', 'source_range': (-5, 5), 'target_range': (-1, 1)}
))
register_node_by_spec(nms.VAR_FC_5D_STD_PCT, NodeSpec(
    NumericalVarNode, 'Forecasted price volatility (std) in 5 days (%)', 
    return_type=SemanticType.VOLATILITY, node_type='variable',
    # Giả định độ lệch chuẩn 5% là rất cao
    params={'path': 'forecasting_report.forecasts.1.prediction.1', 'source_range': (0, 5), 'target_range': (0, 1)}
))
register_node_by_spec(nms.VAR_FC_5D_MAX_PCT, NodeSpec(
    NumericalVarNode, 'Forecasted max potential upside in 5 days (%)', 
    return_type=SemanticType.PERCENTAGE, node_type='variable',
    params={'path': 'forecasting_report.forecasts.1.prediction.3', 'source_range': (0, 10), 'target_range': (0, 1)}
))
register_node_by_spec(nms.VAR_FC_5D_MIN_PCT, NodeSpec(
    NumericalVarNode, 'Forecasted max potential downside in 5 days (%)', 
    return_type=SemanticType.PERCENTAGE, node_type='variable',
    params={'path': 'forecasting_report.forecasts.1.prediction.2', 'source_range': (-10, 0), 'target_range': (-1, 0)}
))
register_node_by_spec(nms.VAR_FC_5D_Q25_PCT, NodeSpec(
    NumericalVarNode, 'Forecasted q25 price change in 5 days (%)', 
    return_type=SemanticType.PERCENTAGE, node_type='variable',
    # Giả định thay đổi 5% trong 5 ngày là lớn
    params={'path': 'forecasting_report.forecasts.1.prediction.4', 'source_range': (-5, 5), 'target_range': (-1, 1)}
))
register_node_by_spec(nms.VAR_FC_5D_Q75_PCT, NodeSpec(
    NumericalVarNode, 'Forecasted q75 price change in 5 days (%)', 
    return_type=SemanticType.PERCENTAGE, node_type='variable',
    # Giả định thay đổi 5% trong 5 ngày là lớn
    params={'path': 'forecasting_report.forecasts.1.prediction.5', 'source_range': (-5, 5), 'target_range': (-1, 1)}
))

# --- C.3. Từ task 20-Day Distribution Regression (forecasts[2]) ---
register_node_by_spec(nms.VAR_FC_20D_MEAN_PCT, NodeSpec(
    NumericalVarNode, 'Forecasted mean price change in 20 days (%)',
    return_type=SemanticType.PERCENTAGE, node_type='variable',
    # Giả định thay đổi 10% trong 20 ngày là lớn
    params={'path': 'forecasting_report.forecasts.2.prediction.0', 'source_range': (-10, 10), 'target_range': (-1, 1)}
))
register_node_by_spec(nms.VAR_FC_20D_STD_PCT, NodeSpec(
    NumericalVarNode, 'Forecasted price volatility (std) in 20 days (%)', 
    return_type=SemanticType.VOLATILITY, node_type='variable',
    # Giả định độ lệch chuẩn 10% là rất cao
    params={'path': 'forecasting_report.forecasts.2.prediction.1', 'source_range': (0, 10), 'target_range': (0, 1)}
))
register_node_by_spec(nms.VAR_FC_20D_MAX_PCT, NodeSpec(
    NumericalVarNode, 'Forecasted max potential upside in 20 days (%)', 
    return_type=SemanticType.PERCENTAGE, node_type='variable',
    params={'path': 'forecasting_report.forecasts.2.prediction.3', 'source_range': (0, 15), 'target_range': (0, 1)}
))
register_node_by_spec(nms.VAR_FC_20D_MIN_PCT, NodeSpec(
    NumericalVarNode, 'Forecasted max potential downside in 20 days (%)', 
    return_type=SemanticType.PERCENTAGE, node_type='variable',
    params={'path': 'forecasting_report.forecasts.2.prediction.2', 'source_range': (-15, 0), 'target_range': (-1, 0)}
))

# ===================================================================
# == D. BIẾN TỪ BÁO CÁO PHÂN TÍCH TIN TỨC (NEWS)
# == Sử dụng các trường đã được tổng hợp trong SummaryReport
# ===================================================================

# --- D.1. Biến về số lượng (Count-based) ---

register_node_by_spec(nms.VAR_NEWS_SUM_NUM_POSITIVE, NodeSpec(
    node_class=NumericalVarNode,
    description='Summary: Total number of news with positive sentiment',
    node_type='variable',
    return_type=SemanticType.SENTIMENT,
    # Giả định: 5 tin tích cực là một tín hiệu rất mạnh
    params={'path': 'news_report.summary.num_positive_sentiment', 'source_range': (0, 5), 'target_range': (0, 1)}
))

register_node_by_spec(nms.VAR_NEWS_SUM_NUM_NEGATIVE, NodeSpec(
    node_class=NumericalVarNode,
    description='Summary: Total number of news with negative sentiment',
    node_type='variable',
    return_type=SemanticType.SENTIMENT,
    # Giả định: 5 tin tiêu cực là tín hiệu rất mạnh (giá trị chuẩn hóa là 1.0, nhưng ý nghĩa là tiêu cực)
    params={'path': 'news_report.summary.num_negative_sentiment', 'source_range': (0, 5), 'target_range': (0, 1)}
))

register_node_by_spec(nms.VAR_NEWS_SUM_NUM_HIGH_IMPACT, NodeSpec(
    node_class=NumericalVarNode,
    description='Summary: Total number of news assessed as high impact',
    node_type='variable',
    return_type=SemanticType.SENTIMENT,
    params={'path': 'news_report.summary.num_high_impact', 'source_range': (0, 3), 'target_range': (0, 1)}
))
register_node_by_spec(nms.VAR_NEWS_SUM_NUM_MODERATE_IMPACT, NodeSpec(
    node_class=NumericalVarNode,
    description='Summary: Total number of news assessed as high impact',
    node_type='variable',
    return_type=SemanticType.SENTIMENT,
    params={'path': 'news_report.summary.num_moderate_impact', 'source_range': (0, 3), 'target_range': (0, 1)}
))
register_node_by_spec(nms.VAR_NEWS_SUM_NUM_LOW_IMPACT, NodeSpec(
    node_class=NumericalVarNode,
    description='Summary: Total number of news assessed as high impact',
    node_type='variable',
    return_type=SemanticType.SENTIMENT,
    params={'path': 'news_report.summary.num_low_impact', 'source_range': (0, 3), 'target_range': (0, 1)}
))
# --- D.2. Biến về tỷ lệ/trung bình (Ratio/Average-based) ---

register_node_by_spec(nms.VAR_NEWS_SUM_AVG_POSITIVE_KEYWORDS, NodeSpec(
    node_class=NumericalVarNode,
    description='Summary: Average number of positive keywords found per news item',
    node_type='variable',
    return_type=SemanticType.SENTIMENT,
    # Giả định: Trung bình 3 từ khóa tích cực/tin là một tín hiệu mạnh
    params={'path': 'news_report.summary.avg_of_positive_keyword_found', 'source_range': (0, 3), 'target_range': (0, 1)}
))

register_node_by_spec(nms.VAR_NEWS_SUM_AVG_NEGATIVE_KEYWORDS, NodeSpec(
    node_class=NumericalVarNode,
    description='Summary: Average number of negative keywords found per news item',
    node_type='variable',
    return_type=SemanticType.SENTIMENT,
    params={'path': 'news_report.summary.avg_of_negative_keyword_found', 'source_range': (0, 3), 'target_range': (0, 1)}
))

register_node_by_spec(nms.VAR_NEWS_SUM_AVG_NER, NodeSpec(
    node_class=NumericalVarNode,
    description='Summary: Average number of named entities found per news item',
    node_type='variable',
    return_type=SemanticType.SENTIMENT,
    # Giả định: Trung bình 5 thực thể/tin cho thấy tin tức rất cụ thể và đáng tin
    params={'path': 'news_report.summary.avg_of_ner_found', 'source_range': (0, 5), 'target_range': (0, 1)}
))