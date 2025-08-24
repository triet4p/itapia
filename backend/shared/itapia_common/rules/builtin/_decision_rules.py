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
from itapia_common.schemas.entities.rules import SemanticType

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
    """[1] Đi theo xu hướng: Tính điểm dựa trên sự đồng thuận của xu hướng."""
    # Logic: Điểm = (Điểm xu hướng trung hạn + Điểm xu hướng dài hạn) / 2
    # Mỗi xu hướng có điểm: uptrend=1, downtrend=-1, undefined=0
    mid_term_trend = create_node(nms.VAR_D_TREND_MIDTERM_DIR)
    long_term_trend = create_node(nms.VAR_D_TREND_LONGTERM_DIR)
    
    sum_of_trends = create_node(nms.OPR_ADD2_TO_NUM, children=[mid_term_trend, long_term_trend])
    logic_tree = create_node(nms.OPR_DIV2, children=[sum_of_trends, create_node(nms.CONST_NUM(2.0, SemanticType.NUMERICAL))])
    
    return _build_rule("RULE_D_01_TREND_FOLLOW", "Trend Following Score", "Calculates a score based on the alignment of mid and long-term trends.", logic_tree)

def _create_rule_2_rsi_momentum() -> Rule:
    """[2] Động lượng RSI: Chuyển đổi giá trị RSI đã chuẩn hóa thành một tín hiệu trực tiếp."""
    # Logic: Điểm = Giá trị RSI đã chuẩn hóa (từ -1 đến 1)
    # Ví dụ: RSI=70 -> chuẩn hóa ~0.4. RSI=30 -> chuẩn hóa ~ -0.4.
    # Quy tắc này tin rằng RSI bản thân nó đã là một tín hiệu.
    logic_tree = create_node(nms.VAR_D_RSI_14)
    
    return _build_rule("RULE_D_02_RSI_MOMENTUM", "RSI Momentum Score", "Uses the normalized RSI value directly as a momentum signal.", logic_tree)

def _create_rule_3_ml_forecast_confidence() -> Rule:
    """[3] Sự tự tin của AI: Dùng xác suất dự báo làm điểm số."""
    # Logic: Điểm = Xác suất Thắng - Xác suất Thua
    # Điều này tạo ra một điểm số từ -1 đến 1, phản ánh độ chắc chắn của mô hình.
    prob_win = create_node(nms.VAR_FC_TB_PREDICTION)
    prob_loss = create_node(nms.VAR_FC_5D_MEAN_PCT)
    
    logic_tree = create_node(nms.OPR_SUB2, children=[prob_win, prob_loss])
    
    return _build_rule("RULE_D_03_ML_CONFIDENCE", "ML Forecast Confidence", "Calculates a score based on the confidence (Prob_Win - Prob_Loss) of the ML model.", logic_tree)

def _create_rule_4_news_sentiment_balance() -> Rule:
    """[4] Cán cân Tin tức: Tính điểm dựa trên sự chênh lệch giữa tin tốt và tin xấu."""
    # Logic: Điểm = (Số tin tích cực - Số tin tiêu cực) / (Tổng số tin + 1)
    # Công thức này chuẩn hóa điểm số về khoảng [-1, 1] và xử lý trường hợp chia cho 0.
    num_pos = create_node(nms.VAR_NEWS_SUM_NUM_POSITIVE)
    num_neg = create_node(nms.VAR_NEWS_SUM_NUM_NEGATIVE)
    
    numerator = create_node(nms.OPR_SUB2_TO_NUM, children=[num_pos, num_neg])
    denominator_sum = create_node(nms.OPR_ADD2_TO_NUM, children=[num_pos, num_neg])
    denominator_sum_div = create_node(nms.OPR_ADD2, children=[denominator_sum, create_node(nms.CONST_NUM(1.0, SemanticType.NUMERICAL))])
    
    logic_tree = create_node(nms.OPR_DIV2, children=[numerator, denominator_sum_div])
    
    return _build_rule("RULE_D_04_NEWS_BALANCE", "News Sentiment Balance", "Calculates a score based on the ratio of positive to negative news.", logic_tree)

def _create_rule_5_trend_strength_confirmation() -> Rule:
    """[5] Xác nhận Sức mạnh Xu hướng: Tín hiệu mạnh hơn nếu xu hướng mạnh."""
    # Logic: Điểm = Điểm xu hướng * Điểm sức mạnh xu hướng
    # Ví dụ: Uptrend (1.0) + Strong (1.0) -> 1.0. Uptrend (1.0) + Weak (0.2) -> 0.2
    trend_direction = create_node(nms.VAR_D_TREND_MIDTERM_DIR)
    trend_strength = create_node(nms.VAR_D_TREND_OVERALL_STRENGTH)
    
    logic_tree = create_node(nms.OPR_MUL2, children=[trend_direction, trend_strength])
    
    return _build_rule("RULE_D_05_TREND_STRENGTH", "Trend Strength Confirmation", "Amplifies trend signal by its strength.", logic_tree)

def _create_rule_6_pattern_sentiment() -> Rule:
    """[6] Tín hiệu Mẫu hình: Sử dụng tín hiệu từ mẫu hình hàng đầu."""
    # Logic: Điểm = Tín hiệu của mẫu hình (bull=1, bear=-1, neutral=0)
    # Đây là một tín hiệu trực tiếp.
    logic_tree = create_node(nms.VAR_D_PATTERN_1_SENTIMENT)
    
    return _build_rule("RULE_D_06_PATTERN_SENTIMENT", "Pattern Sentiment Signal", "Uses the sentiment of the most prominent pattern directly as a signal.", logic_tree)

def _create_rule_7_mean_reversion_fading() -> Rule:
    """[7] Giao dịch Đảo chiều: Tín hiệu bán khi RSI quá mua, tín hiệu mua khi quá bán."""
    # Logic: Nếu RSI > 70, tín hiệu Bán (-1). Nếu RSI < 30, tín hiệu Mua (1).
    # Chú ý: Đây là một quy tắc đảo chiều thuần túy, không lọc theo xu hướng.
    cond_overbought = create_node(nms.OPR_GT, children=[create_node(nms.VAR_D_RSI_14), create_node(nms.CONST_RSI_OVERBOUGHT)])
    cond_oversold = create_node(nms.OPR_LT, children=[create_node(nms.VAR_D_RSI_14), create_node(nms.CONST_RSI_OVERSOLD)])
    
    inner_if = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_oversold, create_node(nms.CONST_NUM(1.0, SemanticType.NUMERICAL)), create_node(nms.CONST_NUM(0.0, SemanticType.NUMERICAL))
    ])
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_overbought, create_node(nms.CONST_NUM(-1.0, SemanticType.NUMERICAL)), inner_if
    ])
    
    return _build_rule("RULE_D_07_MEAN_REVERSION_FADE", "Mean Reversion Fading", "Generates a contrarian signal based on RSI overbought/oversold levels.", logic_tree)

def _create_rule_8_forecast_potential() -> Rule:
    """[8] Tiềm năng Dự báo: Cân bằng giữa tiềm năng tăng và giảm giá."""
    # Logic: Điểm = Dự báo tăng giá tối đa + Dự báo giảm giá tối thiểu
    # (max_pct là số dương, min_pct là số âm, nên đây là phép cộng)
    # Ví dụ: max_pct=0.8 (+10%), min_pct=-0.2 (-2%) -> Điểm = 0.6 (thiên về tăng)
    max_upside = create_node(nms.VAR_FC_5D_MAX_PCT)
    max_downside = create_node(nms.VAR_FC_5D_MIN_PCT)
    const_2 = create_node(nms.CONST_NUM(2.0, SemanticType.NUMERICAL))
    
    sub_tree = create_node(nms.OPR_SUB2_TO_NUM, children=[max_upside, max_downside])
    sub_tree2 = create_node(nms.OPR_SUB2, children=[const_2, sub_tree])
    logic_tree = create_node(nms.OPR_DIV2, children=[sub_tree2, const_2])
    return _build_rule("RULE_D_08_FC_POTENTIAL", "Forecasted Potential Score", "Balances the forecasted max upside against the max downside.", logic_tree)

def _create_rule_9_intraday_momentum() -> Rule:
    """[9] Động lượng Trong ngày: Tín hiệu dựa trên sự phá vỡ vùng giá mở cửa."""
    # Logic: Điểm = Tín hiệu từ ORB (bull-breakout=1, bear-breakdown=-1, inside=0)
    logic_tree = create_node(nms.VAR_I_ORB_STATUS)
    
    return _build_rule("RULE_D_09_INTRADAY_MOMENTUM", "Intraday Breakout Momentum", "Signal based on intraday opening range breakout status.", logic_tree)

def _create_rule_10_high_impact_news_direction() -> Rule:
    """[10] Hướng đi của Tin tức Quan trọng: Tính điểm dựa trên cảm tính của các tin có tác động mạnh."""
    # Logic: (Số tin tích cực & tác động mạnh * 1) + (Số tin tiêu cực & tác động mạnh * -1)
    # Đây là một quy tắc phức tạp hơn, chúng ta sẽ đơn giản hóa nó:
    # Logic: Nếu có tin tác động mạnh, điểm số sẽ là điểm cảm tính của tin gần nhất.
    cond_has_high_impact = create_node(nms.OPR_GTE, children=[create_node(nms.VAR_NEWS_SUM_NUM_HIGH_IMPACT), create_node(nms.CONST_NUM(0.8, SemanticType.SENTIMENT))])
    latest_news_sentiment = create_node(nms.VAR_NEWS_SUM_NUM_POSITIVE)
    
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_has_high_impact, latest_news_sentiment, create_node(nms.CONST_NUM(0.0, SemanticType.SENTIMENT))
    ])
    
    return _build_rule("RULE_D_10_HIGH_IMPACT_NEWS", "High-Impact News Direction", "Signal is driven by the sentiment of the latest news, only if high-impact news exists.", logic_tree)
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