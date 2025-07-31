# itapia_common/rules/_opportunity_rules_builtin.py

"""
Tệp này định nghĩa và đăng ký các Rule dựng sẵn cho việc Tìm kiếm Cơ hội.
Mỗi quy tắc đều có node gốc là OPR_TO_OPPORTUNITY_RATING.
"""

from typing import List

from itapia_common.rules import names as nms
from itapia_common.rules.rule import Rule
from itapia_common.rules.nodes.registry import create_node
from itapia_common.rules.nodes import _TreeNode

# ===================================================================
# == A. CÁC HÀM TẠO QUY TẮC TÌM KIẾM CƠ HỘI (OPPORTUNITY FINDING RULES)
# ===================================================================

def _build_opportunity_rule(rule_id: str, name: str, description: str, logic_tree: _TreeNode) -> Rule:
    """Hàm helper để bọc logic vào một Toán tử Kết luận Cơ hội và tạo Rule."""
    root_node = create_node(
        node_name=nms.OPR_TO_OPPORTUNITY_RATING, # <<< Chú ý: Sử dụng toán tử OPPORTUNITY
        children=[logic_tree]
    )
    return Rule(
        rule_id=rule_id,
        name=name,
        description=description,
        root=root_node
    )

def _create_rule_1_deep_value_screener() -> Rule:
    """
    [1] Sàng lọc "Mua giá trị": Tìm cổ phiếu bị bán quá đà trong một xu hướng dài hạn vẫn tốt.
    - LOGIC: Nếu RSI (daily) < 30 (quá bán) VÀ xu hướng dài hạn là UPTREND.
    - TRIẾT LÝ: Tìm kiếm cơ hội mua "kim cương trong bùn", cổ phiếu tốt đang bị điều chỉnh tạm thời.
    """
    cond_rsi_oversold = create_node(nms.OPR_LT, children=[
        create_node(nms.VAR_D_RSI_14),
        create_node(nms.CONST_RSI_OVERSOLD)
    ])
    cond_long_trend_up = create_node(nms.OPR_EQ, children=[
        create_node(nms.VAR_D_TREND_LONGTERM_DIR),
        create_node(nms.CONST_NUM(1.0))
    ])
    
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        create_node(nms.OPR_AND, children=[cond_rsi_oversold, cond_long_trend_up]),
        create_node(nms.CONST_OPP_RATING_STRONG), # Đây là một cơ hội mạnh
        create_node(nms.CONST_OPP_RATING_AVOID)   # Nếu không, quy tắc này không tìm thấy gì
    ])
    
    return _build_opportunity_rule("RULE_O_01_DEEP_VALUE", "Deep Value Screener", "Finds oversold stocks within a long-term uptrend.", logic_tree)

def _create_rule_2_trend_reversal_screener() -> Rule:
    """
    [2] Sàng lọc Đảo chiều Xu hướng: Tìm tín hiệu sớm của một sự đảo chiều từ giảm sang tăng.
    - LOGIC: Nếu xu hướng trung hạn vừa chuyển sang UPTREND VÀ xu hướng dài hạn đang là DOWNTREND.
    - TRIẾT LÝ: Bắt con sóng sớm khi có dấu hiệu xu hướng đang thay đổi.
    """
    cond_mid_trend_up = create_node(nms.OPR_EQ, children=[
        create_node(nms.VAR_D_TREND_MIDTERM_DIR),
        create_node(nms.CONST_NUM(1.0))
    ])
    cond_long_trend_down = create_node(nms.OPR_EQ, children=[
        create_node(nms.VAR_D_TREND_LONGTERM_DIR),
        create_node(nms.CONST_NUM(-1.0))
    ])
    
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        create_node(nms.OPR_AND, children=[cond_mid_trend_up, cond_long_trend_down]),
        create_node(nms.CONST_OPP_RATING_INTERESTING), # Cơ hội thú vị, cần theo dõi thêm
        create_node(nms.CONST_OPP_RATING_AVOID)
    ])
    
    return _build_opportunity_rule("RULE_O_02_TREND_REVERSAL", "Trend Reversal Screener", "Finds early signs of a trend reversal from bearish to bullish.", logic_tree)

def _create_rule_3_forecast_upside_potential() -> Rule:
    """
    [3] Sàng lọc theo Tiềm năng Tăng trưởng Dự báo: Tìm cổ phiếu được AI dự báo có tiềm năng tăng giá cao.
    - LOGIC: Nếu dự báo mức tăng tối đa (max_pct) trong 20 ngày tới > 10%.
    - TRIẾT LÝ: Tận dụng khả năng dự báo của mô hình để tìm các cơ hội tăng trưởng.
    """
    # 10% upside potential. source_range (0, 15) -> 10 tương đương giá trị chuẩn hóa 0.66
    upside_threshold = create_node(nms.CONST_NUM(0.7))
    
    cond_high_upside = create_node(nms.OPR_GT, children=[
        create_node(nms.VAR_FC_20D_MAX_PCT),
        upside_threshold
    ])
    
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_high_upside,
        create_node(nms.CONST_OPP_RATING_STRONG),
        create_node(nms.CONST_OPP_RATING_NEUTRAL)
    ])

    return _build_opportunity_rule("RULE_O_03_FC_UPSIDE", "Forecasted Upside Potential", "Finds stocks with high potential upside forecasted by the ML model.", logic_tree)

def _create_rule_4_bullish_pattern_screener() -> Rule:
    """
    [4] Sàng lọc Mẫu hình Tăng giá: Tìm các cổ phiếu vừa xác nhận một mẫu hình tăng giá mạnh.
    - LOGIC: Nếu mẫu hình hàng đầu được nhận diện là 'bull' VÀ có điểm số cao.
    - TRIẾT LÝ: Các mẫu hình giá kinh điển là những tín hiệu mạnh mẽ về tâm lý thị trường.
    """
    # Điểm số mẫu hình > 60 là một tín hiệu đáng tin cậy
    score_threshold = create_node(nms.CONST_NUM(0.6))
    
    cond_is_bull_pattern = create_node(nms.OPR_EQ, children=[
        create_node(nms.VAR_D_PATTERN_1_SENTIMENT),
        create_node(nms.CONST_NUM(1.0))
    ])
    cond_high_score = create_node(nms.OPR_GT, children=[
        create_node(nms.VAR_D_PATTERN_1_SCORE),
        score_threshold
    ])
    
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        create_node(nms.OPR_AND, children=[cond_is_bull_pattern, cond_high_score]),
        create_node(nms.CONST_OPP_RATING_STRONG),
        create_node(nms.CONST_OPP_RATING_AVOID)
    ])

    return _build_opportunity_rule("RULE_O_04_BULLISH_PATTERN", "Bullish Pattern Screener", "Finds stocks that have recently confirmed a strong bullish chart/candlestick pattern.", logic_tree)

def _create_rule_5_news_catalyst_screener() -> Rule:
    """
    [5] Sàng lọc theo Chất xúc tác Tin tức: Tìm các cổ phiếu đang có dòng tin tức tích cực đột biến.
    - LOGIC: Nếu số lượng tin tức tích cực > 3 VÀ có ít nhất 2 tin tức tác động mạnh.
    - TRIẾT LÝ: Một dòng tin tức đột biến có thể là chất xúc tác cho một đợt tăng giá mạnh.
    """
    cond_many_positive_news = create_node(nms.OPR_GT, children=[
        create_node(nms.VAR_NEWS_SUM_NUM_POSITIVE),
        create_node(nms.CONST_NUM(0.9))
    ])
    cond_many_high_impact = create_node(nms.OPR_GTE, children=[
        create_node(nms.VAR_NEWS_SUM_NUM_HIGH_IMPACT),
        create_node(nms.CONST_NUM(0.6))
    ])
    
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        create_node(nms.OPR_AND, children=[cond_many_positive_news, cond_many_high_impact]),
        create_node(nms.CONST_OPP_RATING_INTERESTING),
        create_node(nms.CONST_OPP_RATING_NEUTRAL)
    ])

    return _build_opportunity_rule("RULE_O_05_NEWS_CATALYST", "News Catalyst Screener", "Finds stocks with a surge of positive and high-impact news.", logic_tree)


# ===================================================================
# == B. DANH SÁCH TỔNG HỢP CÁC QUY TẮC DỰNG SẴN
# ===================================================================

_BUILTIN_OPPORTUNITY_RULES: List[Rule] | None = None

def builtin_opportunity_rules() -> List[Rule]:
    """
    Trả về một danh sách các quy tắc tìm kiếm cơ hội dựng sẵn.
    Sử dụng lazy initialization để chỉ tạo danh sách một lần.
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