# itapia_common/rules/_risk_rules_builtin.py

"""
Tệp này định nghĩa và đăng ký các Rule dựng sẵn cho việc Quản lý Rủi ro.
Mỗi quy tắc đều có node gốc là OPR_TO_RISK_LEVEL.
"""

from typing import List

from itapia_common.rules import names as nms
from itapia_common.rules.rule import Rule
from itapia_common.rules.nodes.registry import create_node
from itapia_common.rules.nodes import _TreeNode

# ===================================================================
# == A. CÁC HÀM TẠO QUY TẮC QUẢN LÝ RỦI RO (RISK MANAGEMENT RULES)
# ===================================================================

def _build_risk_rule(rule_id: str, name: str, description: str, logic_tree: _TreeNode) -> Rule:
    """Hàm helper để bọc logic vào một Toán tử Kết luận Rủi ro và tạo Rule."""
    root_node = create_node(
        node_name=nms.OPR_TO_RISK_LEVEL, # <<< Chú ý: Sử dụng toán tử RISK
        children=[logic_tree]
    )
    return Rule(
        rule_id=rule_id,
        name=name,
        description=description,
        root=root_node
    )

def _create_rule_1_high_volatility_warning() -> Rule:
    """
    [1] Cảnh báo Biến động Cao: Nếu ATR (đã chuẩn hóa) cao, rủi ro cao.
    - LOGIC: Nếu ATR > 7.5% (tương đương giá trị chuẩn hóa 0.5), rủi ro được đánh giá là CAO.
    - TRIẾT LÝ: Biến động cao có nghĩa là giá có thể di chuyển ngược lại vị thế của bạn một cách nhanh chóng.
    """
    # ATR > 7.5%. source_range (0,15) -> 7.5 tương đương giá trị chuẩn hóa 0.5
    volatility_threshold = create_node(nms.CONST_NUM(0.5))
    
    cond_high_atr = create_node(nms.OPR_GT, children=[
        create_node(nms.VAR_D_ATR_14),
        volatility_threshold
    ])
    
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_high_atr,
        create_node(nms.CONST_RISK_HIGH),
        create_node(nms.CONST_RISK_LOW) # Nếu không, rủi ro biến động là thấp
    ])
    
    return _build_risk_rule("RULE_R_01_HIGH_VOLATILITY", "High Volatility Warning", "Flags high risk when ATR is significantly elevated.", logic_tree)

def _create_rule_2_weak_trend_risk() -> Rule:
    """
    [2] Rủi ro Xu hướng Yếu: Giao dịch khi xu hướng yếu có rủi ro cao.
    - LOGIC: Nếu sức mạnh xu hướng tổng thể là 'weak' hoặc 'undefined', rủi ro là TRUNG BÌNH.
    - TRIẾT LÝ: Giao dịch trong thị trường đi ngang (sideways) hoặc không rõ xu hướng thường khó đoán và dễ bị "whipsaw" (tín hiệu nhiễu).
    """
    # Sức mạnh xu hướng < 0.5 (tương đương 'moderate')
    strength_threshold = create_node(nms.CONST_NUM(0.5))
    
    cond_weak_trend = create_node(nms.OPR_LT, children=[
        create_node(nms.VAR_D_TREND_OVERALL_STRENGTH),
        strength_threshold
    ])

    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_weak_trend,
        create_node(nms.CONST_RISK_MODERATE),
        create_node(nms.CONST_RISK_LOW)
    ])
    
    return _build_risk_rule("RULE_R_02_WEAK_TREND", "Weak Trend Risk", "Flags moderate risk when the overall trend is weak or undefined.", logic_tree)

def _create_rule_3_forecasted_downside() -> Rule:
    """
    [3] Rủi ro Giảm giá theo Dự báo: Nếu mô hình dự báo rủi ro giảm giá lớn.
    - LOGIC: Nếu dự báo mức giảm tối đa (min_pct) trong 5 ngày tới < -5%, rủi ro là CAO.
    - TRIẾT LÝ: Tin vào cảnh báo của mô hình định lượng về rủi ro tiềm ẩn.
    """
    # -5% downside. source_range (-10, 0) -> -5 tương đương giá trị chuẩn hóa -0.5
    downside_threshold = create_node(nms.CONST_NUM(-0.5))

    cond_high_downside_risk = create_node(nms.OPR_LT, children=[
        create_node(nms.VAR_FC_5D_MIN_PCT),
        downside_threshold
    ])
    
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_high_downside_risk,
        create_node(nms.CONST_RISK_HIGH),
        create_node(nms.CONST_RISK_MODERATE)
    ])

    return _build_risk_rule("RULE_R_03_FC_DOWNSIDE", "Forecasted Downside Risk", "Flags high risk if the ML model forecasts a significant potential drop.", logic_tree)

def _create_rule_4_negative_news_risk() -> Rule:
    """
    [4] Rủi ro từ Tin tức Tiêu cực: Nếu có nhiều tin tức tiêu cực, rủi ro tổng thể tăng.
    - LOGIC: Nếu số lượng tin tức tiêu cực > 1, rủi ro được nâng lên mức TRUNG BÌNH.
    - TRIẾT LÝ: Dòng tin tức xấu có thể báo hiệu những thay đổi tiêu cực về cơ bản hoặc tâm lý thị trường.
    """
    cond_many_negative_news = create_node(nms.OPR_GT, children=[
        create_node(nms.VAR_NEWS_SUM_NUM_NEGATIVE),
        create_node(nms.CONST_NUM(0.9)) # > 1 tin xấu
    ])

    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_many_negative_news,
        create_node(nms.CONST_RISK_MODERATE),
        create_node(nms.CONST_RISK_LOW)
    ])

    return _build_risk_rule("RULE_R_04_NEGATIVE_NEWS", "Negative News Risk", "Flags moderate risk if there is a flow of negative news.", logic_tree)

def _create_rule_5_overextended_market() -> Rule:
    """
    [5] Rủi ro Thị trường Tăng quá nóng: Nếu RSI đã ở vùng quá mua quá lâu.
    - LOGIC: Nếu RSI (daily) > 70, rủi ro điều chỉnh là CAO.
    - TRIẾT LÝ: Mua vào khi thị trường đã tăng quá nóng là rất rủi ro.
    """
    cond_rsi_overbought = create_node(nms.OPR_GT, children=[
        create_node(nms.VAR_D_RSI_14),
        create_node(nms.CONST_RSI_OVERBOUGHT)
    ])
    
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_rsi_overbought,
        create_node(nms.CONST_RISK_HIGH),
        create_node(nms.CONST_RISK_MODERATE)
    ])

    return _build_risk_rule("RULE_R_05_OVEREXTENDED", "Overextended Market Risk", "Flags high risk of a pullback when the market is overbought (RSI > 70).", logic_tree)

# ===================================================================
# == B. DANH SÁCH TỔNG HỢP CÁC QUY TẮC DỰNG SẴN
# ===================================================================

_BUILTIN_RISK_RULES: List[Rule] | None = None

def builtin_risk_rules() -> List[Rule]:
    """
    Trả về một danh sách các quy tắc quản lý rủi ro dựng sẵn.
    Sử dụng lazy initialization để chỉ tạo danh sách một lần.
    """
    global _BUILTIN_RISK_RULES
    if _BUILTIN_RISK_RULES is not None:
        return _BUILTIN_RISK_RULES
        
    _BUILTIN_RISK_RULES = [
        _create_rule_1_high_volatility_warning(),
        _create_rule_2_weak_trend_risk(),
        _create_rule_3_forecasted_downside(),
        _create_rule_4_negative_news_risk(),
        _create_rule_5_overextended_market(),
    ]
    return _BUILTIN_RISK_RULES