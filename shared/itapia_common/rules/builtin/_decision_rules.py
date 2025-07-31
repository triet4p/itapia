# itapia_common/rules/_rules_builtin.py

"""
Tệp này định nghĩa và đăng ký các Rule dựng sẵn trong hệ thống.
Mỗi quy tắc đều có node gốc là một Toán tử Kết luận Đặc biệt.
"""

from typing import List

from itapia_common.rules import names as nms
from itapia_common.rules.rule import Rule
from itapia_common.rules.nodes.registry import create_node
from itapia_common.rules.nodes import _TreeNode

# ===================================================================
# == A. CÁC HÀM TẠO QUY TẮC RA QUYẾT ĐỊNH (DECISION MAKING RULES)
# ===================================================================

def _build_rule(rule_id: str, name: str, description: str, logic_tree: _TreeNode) -> Rule:
    """Hàm helper để bọc logic vào một Toán tử Kết luận và tạo Rule."""
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
    """[1] Đi theo xu hướng: Nếu cả trung và dài hạn đều đồng thuận, tín hiệu mạnh."""
    cond_buy = create_node(nms.OPR_AND, children=[
        create_node(nms.OPR_EQ, children=[create_node(nms.VAR_D_TREND_MIDTERM_DIR), create_node(nms.CONST_NUM(1.0))]),
        create_node(nms.OPR_EQ, children=[create_node(nms.VAR_D_TREND_LONGTERM_DIR), create_node(nms.CONST_NUM(1.0))])
    ])
    cond_sell = create_node(nms.OPR_AND, children=[
        create_node(nms.OPR_EQ, children=[create_node(nms.VAR_D_TREND_MIDTERM_DIR), create_node(nms.CONST_NUM(-1.0))]),
        create_node(nms.OPR_EQ, children=[create_node(nms.VAR_D_TREND_LONGTERM_DIR), create_node(nms.CONST_NUM(-1.0))])
    ])
    
    inner_if = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_sell, create_node(nms.CONST_DECISION_SELL_STRONG), create_node(nms.CONST_DECISION_HOLD_NEUTRAL)
    ])
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_buy, create_node(nms.CONST_DECISION_BUY_STRONG), inner_if
    ])
    
    return _build_rule("RULE_D_01_TREND_FOLLOW", "Trend Following", "Signal based on mid and long-term trend alignment.", logic_tree)

def _create_rule_2_rsi_dip_buying() -> Rule:
    """[2] Mua khi giá điều chỉnh: Mua khi RSI quá bán trong một xu hướng không phải giảm."""
    cond_rsi_oversold = create_node(nms.OPR_LT, children=[create_node(nms.VAR_D_RSI_14), create_node(nms.CONST_RSI_OVERSOLD)])
    cond_trend_not_down = create_node(nms.OPR_GTE, children=[create_node(nms.VAR_D_TREND_MIDTERM_DIR), create_node(nms.CONST_NUM(0.0))])
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        create_node(nms.OPR_AND, children=[cond_rsi_oversold, cond_trend_not_down]),
        create_node(nms.CONST_DECISION_BUY_MODERATE),
        create_node(nms.CONST_DECISION_HOLD_NEUTRAL)
    ])
    return _build_rule("RULE_D_02_RSI_DIP_BUY", "RSI Dip Buying", "Buy on RSI oversold, but only if the trend is not negative.", logic_tree)

def _create_rule_3_ml_forecast_trust() -> Rule:
    """[3] Tin vào AI: Dịch trực tiếp dự báo thắng/thua của mô hình Triple Barrier."""
    cond_win = create_node(nms.OPR_EQ, children=[create_node(nms.VAR_FC_TB_PREDICTION), create_node(nms.CONST_NUM(1.0))])
    cond_loss = create_node(nms.OPR_EQ, children=[create_node(nms.VAR_FC_TB_PREDICTION), create_node(nms.CONST_NUM(-1.0))])
    inner_if = create_node(nms.OPR_IF_THEN_ELSE, children=[cond_loss, create_node(nms.CONST_DECISION_SELL_STRONG), create_node(nms.CONST_DECISION_HOLD_NEUTRAL)])
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[cond_win, create_node(nms.CONST_DECISION_BUY_STRONG), inner_if])
    return _build_rule("RULE_D_03_ML_FORECAST", "ML Forecast Driven", "Translates the Triple Barrier model's output into a signal.", logic_tree)

def _create_rule_4_news_sentiment_lead() -> Rule:
    """[4] Theo tin tức: Tín hiệu mua nếu tin tích cực vượt trội và có tác động mạnh."""
    cond_pos_gt_neg = create_node(nms.OPR_GT, children=[create_node(nms.VAR_NEWS_SUM_NUM_POSITIVE), create_node(nms.VAR_NEWS_SUM_NUM_NEGATIVE)])
    cond_has_high_impact = create_node(nms.OPR_GTE, children=[create_node(nms.VAR_NEWS_SUM_NUM_HIGH_IMPACT), create_node(nms.CONST_NUM(1.0))])
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        create_node(nms.OPR_AND, children=[cond_pos_gt_neg, cond_has_high_impact]),
        create_node(nms.CONST_DECISION_BUY_MODERATE),
        create_node(nms.CONST_DECISION_HOLD_NEUTRAL)
    ])
    return _build_rule("RULE_D_04_NEWS_LEAD", "News Sentiment Lead", "Signal based on positive news flow with high impact.", logic_tree)

def _create_rule_5_volatility_avoidance() -> Rule:
    """[5] Né biến động: Giữ vị thế thận trọng nếu dự báo biến động ngắn hạn cao."""
    cond_high_vol = create_node(nms.OPR_GT, children=[create_node(nms.VAR_FC_5D_STD_PCT), create_node(nms.CONST_NUM(0.6))])
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_high_vol, create_node(nms.CONST_DECISION_HOLD_NEGATIVE), create_node(nms.CONST_DECISION_HOLD_NEUTRAL)
    ])
    return _build_rule("RULE_D_05_VOL_AVOID", "Volatility Avoidance", "Cautious hold signal if high short-term volatility is forecasted.", logic_tree)

def _create_rule_6_pattern_confirmation() -> Rule:
    """[6] Xác nhận mẫu hình: Tín hiệu Mua/Bán nếu có mẫu hình đảo chiều mạnh."""
    cond_bull_pattern = create_node(nms.OPR_EQ, children=[create_node(nms.VAR_D_PATTERN_1_SENTIMENT), create_node(nms.CONST_NUM(1.0))])
    cond_bear_pattern = create_node(nms.OPR_EQ, children=[create_node(nms.VAR_D_PATTERN_1_SENTIMENT), create_node(nms.CONST_NUM(-1.0))])
    inner_if = create_node(nms.OPR_IF_THEN_ELSE, children=[cond_bear_pattern, create_node(nms.CONST_DECISION_SELL_MODERATE), create_node(nms.CONST_DECISION_HOLD_NEUTRAL)])
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[cond_bull_pattern, create_node(nms.CONST_DECISION_BUY_MODERATE), inner_if])
    return _build_rule("RULE_D_06_PATTERN_CONFIRM", "Pattern Confirmation", "Signal based on the sentiment of the most prominent pattern.", logic_tree)

def _create_rule_7_mean_reversion_rsi() -> Rule:
    """[7] Giao dịch đảo chiều: Bán khi RSI quá mua trong một xu hướng không phải tăng."""
    cond_rsi_overbought = create_node(nms.OPR_GT, children=[create_node(nms.VAR_D_RSI_14), create_node(nms.CONST_RSI_OVERBOUGHT)])
    cond_trend_not_up = create_node(nms.OPR_LTE, children=[create_node(nms.VAR_D_TREND_MIDTERM_DIR), create_node(nms.CONST_NUM(0.0))])
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        create_node(nms.OPR_AND, children=[cond_rsi_overbought, cond_trend_not_up]),
        create_node(nms.CONST_DECISION_SELL_MODERATE),
        create_node(nms.CONST_DECISION_HOLD_NEUTRAL)
    ])
    return _build_rule("RULE_D_07_MEAN_REVERSION", "Mean Reversion RSI", "Sell on RSI overbought, but only if the trend is not positive.", logic_tree)

def _create_rule_8_forecast_momentum() -> Rule:
    """[8] Động lượng Dự báo: Mua mạnh nếu dự báo giá trung bình 20 ngày tăng > 5%."""
    # 5% trong 20 ngày. Normalized source_range (-10, 10) -> (5 - (-10))/20 * (1 - (-1)) + (-1) = 0.5
    threshold = create_node(nms.CONST_NUM(0.5))
    cond_strong_fc_momentum = create_node(nms.OPR_GT, children=[create_node(nms.VAR_FC_20D_MEAN_PCT), threshold])
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_strong_fc_momentum, create_node(nms.CONST_DECISION_BUY_STRONG), create_node(nms.CONST_DECISION_HOLD_NEUTRAL)
    ])
    return _build_rule("RULE_D_08_FC_MOMENTUM", "Forecast Momentum", "Strong buy if a significant positive price change is forecasted long-term.", logic_tree)

def _create_rule_9_intraday_breakout() -> Rule:
    """[9] Giao dịch phá vỡ trong ngày: Mua nếu có tín hiệu phá vỡ khỏi vùng giá mở cửa."""
    cond_bull_breakout = create_node(nms.OPR_EQ, children=[create_node(nms.VAR_I_ORB_STATUS), create_node(nms.CONST_NUM(1.0))])
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_bull_breakout, create_node(nms.CONST_DECISION_ACCUMULATE), create_node(nms.CONST_DECISION_HOLD_NEUTRAL)
    ])
    return _build_rule("RULE_D_09_INTRADAY_BREAKOUT", "Intraday Breakout", "Signal to accumulate on intraday bullish breakouts.", logic_tree)

def _create_rule_10_negative_news_override() -> Rule:
    """[10] Tin xấu ghi đè: Bán ngay lập tức nếu có tin rất tiêu cực và tác động mạnh, bất kể tín hiệu kỹ thuật."""
    cond_very_negative = create_node(nms.OPR_GT, children=[create_node(nms.VAR_NEWS_SUM_NUM_NEGATIVE), create_node(nms.CONST_NUM(0.5))]) # > 2 tin xấu
    cond_has_high_impact = create_node(nms.OPR_GTE, children=[create_node(nms.VAR_NEWS_SUM_NUM_HIGH_IMPACT), create_node(nms.CONST_NUM(0.9))])
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        create_node(nms.OPR_AND, children=[cond_very_negative, cond_has_high_impact]),
        create_node(nms.CONST_DECISION_SELL_IMMEDIATE),
        create_node(nms.CONST_DECISION_HOLD_NEUTRAL) # Quy tắc này chỉ bán, không mua.
    ])
    return _build_rule("RULE_D_10_NEWS_OVERRIDE", "Negative News Override", "High-priority sell signal on significant negative news.", logic_tree)

# ===================================================================
# == B. DANH SÁCH TỔNG HỢP CÁC QUY TẮC DỰNG SẴN
# ===================================================================
_BUILTIN_DECISION_RULES: List[Rule] | None = None

def builtin_decision_rules() -> List[Rule]:
    global _BUILTIN_DECISION_RULES
    
    if _BUILTIN_DECISION_RULES is not None:
        return _BUILTIN_DECISION_RULES
    _BUILTIN_DECISION_RULES = [
        _create_rule_1_trend_following(),
        _create_rule_2_rsi_dip_buying(),
        _create_rule_3_ml_forecast_trust(),
        _create_rule_4_news_sentiment_lead(),
        _create_rule_5_volatility_avoidance(),
        _create_rule_6_pattern_confirmation(),
        _create_rule_7_mean_reversion_rsi(),
        _create_rule_8_forecast_momentum(),
        _create_rule_9_intraday_breakout(),
        _create_rule_10_negative_news_override()
    ]
    
    return _BUILTIN_DECISION_RULES