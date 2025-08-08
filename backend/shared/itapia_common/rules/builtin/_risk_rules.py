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

def _create_rule_1_volatility_risk() -> Rule:
    """[1] Rủi ro Biến động: Điểm rủi ro chính là mức độ biến động đã chuẩn hóa."""
    # Logic: Điểm rủi ro = Giá trị đã chuẩn hóa của VAR_D_ATR_14.
    # Biến này đã được chuẩn hóa về [0, 1], với giá trị cao hơn cho thấy biến động lớn hơn.
    logic_tree = create_node(nms.VAR_D_ATR_14)
    
    return _build_risk_rule("RULE_R_01_VOLATILITY_RISK", "Volatility Risk Score", "Scores risk based on the normalized ATR value.", logic_tree)

def _create_rule_2_weak_trend_risk() -> Rule:
    """[2] Rủi ro Xu hướng Yếu: Rủi ro cao hơn khi xu hướng không rõ ràng."""
    # Logic: Điểm rủi ro = 1.0 - Sức mạnh xu hướng.
    # Nếu xu hướng mạnh (strength=1.0), rủi ro là 0. Nếu xu hướng yếu (strength=0.2), rủi ro là 0.8.
    trend_strength = create_node(nms.VAR_D_TREND_OVERALL_STRENGTH)
    
    logic_tree = create_node(nms.OPR_SUB2, children=[
        create_node(nms.CONST_NUM(1.0)),
        trend_strength
    ])
    
    return _build_risk_rule("RULE_R_02_WEAK_TREND_RISK", "Weak Trend Risk", "Scores higher risk when the trend strength is weaker.", logic_tree)

def _create_rule_3_forecasted_downside_risk() -> Rule:
    """[3] Rủi ro Giảm giá theo Dự báo: Điểm rủi ro là tiềm năng giảm giá dự báo."""
    # Logic: Điểm rủi ro = abs(Giá trị đã chuẩn hóa của VAR_FC_5D_MIN_PCT).
    # Biến VAR_FC_5D_MIN_PCT có giá trị từ -1 đến 0. Lấy giá trị tuyệt đối sẽ chuyển nó về [0, 1].
    # Tiềm năng giảm giá càng lớn (ví dụ: -10% -> chuẩn hóa -1.0), điểm rủi ro càng cao (1.0).
    max_downside = create_node(nms.VAR_FC_5D_MIN_PCT)
    
    logic_tree = create_node(nms.OPR_ABS, children=[max_downside])

    return _build_risk_rule("RULE_R_03_FC_DOWNSIDE_RISK", "Forecasted Downside Risk", "Scores risk based on the absolute normalized forecasted max downside.", logic_tree)

def _create_rule_4_negative_news_risk() -> Rule:
    """[4] Rủi ro từ Tin tức Tiêu cực: Điểm rủi ro là mức độ tin tức tiêu cực."""
    # Logic: Điểm rủi ro = Giá trị đã chuẩn hóa của VAR_NEWS_SUM_NUM_NEGATIVE.
    # Biến này đã được chuẩn hóa về [0, 1], với giá trị cao hơn cho thấy nhiều tin xấu hơn.
    logic_tree = create_node(nms.VAR_NEWS_SUM_NUM_NEGATIVE)

    return _build_risk_rule("RULE_R_04_NEGATIVE_NEWS_RISK", "Negative News Risk", "Scores risk based on the normalized count of negative news.", logic_tree)

def _create_rule_5_overextended_risk() -> Rule:
    """
    [5] Rủi ro Thị trường Tăng quá nóng: Điểm rủi ro cao nếu RSI ở vùng quá mua.
    - LOGIC: Nếu RSI > 50, điểm rủi ro bắt đầu tăng tuyến tính.
             Nếu RSI < 50, điểm rủi ro là 0.
    - Công thức: max(0, (RSI_chuẩn_hóa - 0)) -> vì RSI=50 được chuẩn hóa về 0.
    """
    # RSI > 50 (giá trị chuẩn hóa là 0)
    cond_is_bullish_territory = create_node(nms.OPR_GT, children=[
        create_node(nms.VAR_D_RSI_14),
        create_node(nms.CONST_NUM(0.0)) 
    ])
    
    # Nếu đúng, điểm rủi ro chính là giá trị RSI đã chuẩn hóa.
    # Nếu sai, điểm rủi ro là 0.
    logic_tree = create_node(nms.OPR_IF_THEN_ELSE, children=[
        cond_is_bullish_territory,
        create_node(nms.VAR_D_RSI_14),
        create_node(nms.CONST_NUM(0.0))
    ])

    return _build_risk_rule("RULE_R_05_OVEREXTENDED_RISK", "Overextended Market Risk", "Scores higher risk as RSI moves deeper into overbought territory (>50).", logic_tree)
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
        _create_rule_1_volatility_risk(),
        _create_rule_2_weak_trend_risk(),
        _create_rule_3_forecasted_downside_risk(),
        _create_rule_4_negative_news_risk(),
        _create_rule_5_overextended_risk(),
    ]
    return _BUILTIN_RISK_RULES