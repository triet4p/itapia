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
    """[1] Sàng lọc "Mua giá trị": Điểm số cao nếu RSI quá bán trong một xu hướng dài hạn tốt."""
    # Logic: Điểm = (Tín hiệu RSI quá bán) * (Tín hiệu xu hướng dài hạn tốt)
    # Tín hiệu RSI quá bán: 1 nếu RSI < 30, 0 nếu không.
    # Tín hiệu xu hướng dài hạn tốt: 1 nếu uptrend, 0 nếu không.
    # Chỉ khi cả hai điều kiện đều đúng thì điểm mới là 1.
    cond_rsi_oversold = create_node(nms.OPR_LT, children=[create_node(nms.VAR_D_RSI_14), create_node(nms.CONST_RSI_OVERSOLD)])
    cond_long_trend_up = create_node(nms.OPR_EQ, children=[create_node(nms.VAR_D_TREND_LONGTERM_DIR), create_node(nms.CONST_NUM(1.0))])
    
    # Dùng AND, nó sẽ trả về 1.0 nếu cả hai đúng, 0.0 nếu không.
    logic_tree = create_node(nms.OPR_AND, children=[cond_rsi_oversold, cond_long_trend_up])
    
    return _build_opportunity_rule("RULE_O_01_DEEP_VALUE", "Deep Value Screener", "Scores highly for oversold stocks within a long-term uptrend.", logic_tree)

def _create_rule_2_trend_reversal_screener() -> Rule:
    """[2] Sàng lọc Đảo chiều Xu hướng: Điểm số dương nếu có tín hiệu đảo chiều."""
    # Logic: Điểm = 0.5 nếu xu hướng trung hạn vừa chuyển sang tăng trong khi xu hướng dài hạn vẫn đang giảm.
    cond_mid_trend_up = create_node(nms.OPR_EQ, children=[create_node(nms.VAR_D_TREND_MIDTERM_DIR), create_node(nms.CONST_NUM(1.0))])
    cond_long_trend_down = create_node(nms.OPR_EQ, children=[create_node(nms.VAR_D_TREND_LONGTERM_DIR), create_node(nms.CONST_NUM(-1.0))])
    
    is_reversal_signal = create_node(nms.OPR_AND, children=[cond_mid_trend_up, cond_long_trend_down])
    
    # Nếu có tín hiệu đảo chiều, trả về điểm 0.5 (cơ hội thú vị), nếu không thì 0.
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        is_reversal_signal,
        create_node(nms.CONST_NUM(0.5)), # Điểm cho một cơ hội "thú vị"
        create_node(nms.CONST_NUM(0.0))
    ])
    
    return _build_opportunity_rule("RULE_O_02_TREND_REVERSAL", "Trend Reversal Screener", "Scores positively for early signs of a trend reversal from bearish to bullish.", logic_tree)

def _create_rule_3_forecast_upside_potential() -> Rule:
    """[3] Sàng lọc theo Tiềm năng Tăng trưởng Dự báo: Điểm số là tiềm năng tăng giá dự báo."""
    # Logic: Điểm = Giá trị đã chuẩn hóa của VAR_FC_20D_MAX_PCT.
    # Biến này đã được chuẩn hóa về [0, 1], nên ta có thể dùng trực tiếp.
    logic_tree = create_node(nms.VAR_FC_20D_MAX_PCT)

    return _build_opportunity_rule("RULE_O_03_FC_UPSIDE", "Forecasted Upside Potential", "Scores based on the normalized forecasted max upside potential.", logic_tree)

def _create_rule_4_bullish_pattern_screener() -> Rule:
    """[4] Sàng lọc Mẫu hình Tăng giá: Điểm số dựa trên sự tồn tại của mẫu hình tăng giá mạnh."""
    # Logic: Điểm = (Tín hiệu mẫu hình tăng giá) * (Điểm của mẫu hình / 100)
    # Ví dụ: Mẫu hình bull (1.0) với điểm 80 -> 1.0 * (80/100) = 0.8
    cond_is_bull_pattern = create_node(nms.OPR_EQ, children=[create_node(nms.VAR_D_PATTERN_1_SENTIMENT), create_node(nms.CONST_NUM(1.0))])
    
    # Chuẩn hóa điểm số của mẫu hình (vốn từ 0-100) về khoảng [0, 1]
    normalized_pattern_score = create_node(nms.VAR_D_PATTERN_1_SCORE)
    
    # Nếu là mẫu hình bull, trả về điểm đã chuẩn hóa, nếu không thì 0
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_is_bull_pattern,
        normalized_pattern_score,
        create_node(nms.CONST_NUM(0.0))
    ])

    return _build_opportunity_rule("RULE_O_04_BULLISH_PATTERN", "Bullish Pattern Screener", "Scores based on the existence and strength of a bullish pattern.", logic_tree)

def _create_rule_5_news_catalyst_screener() -> Rule:
    """[5] Sàng lọc theo Chất xúc tác Tin tức: Điểm số dựa trên mật độ tin tốt và có tác động."""
    # Logic: Điểm = (Điểm tin tích cực) * (Điểm tin tác động mạnh)
    # Cả hai biến này đều đã được chuẩn hóa về [0, 1].
    # Điểm sẽ chỉ cao khi cả hai yếu tố đều cao.
    positive_news_score = create_node(nms.VAR_NEWS_SUM_NUM_POSITIVE)
    high_impact_news_score = create_node(nms.VAR_NEWS_SUM_NUM_HIGH_IMPACT)
    
    logic_tree = create_node(nms.OPR_MUL2, children=[positive_news_score, high_impact_news_score])

    return _build_opportunity_rule("RULE_O_05_NEWS_CATALYST", "News Catalyst Screener", "Scores based on the density of positive and high-impact news.", logic_tree)

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