# itapia_common/rules/nodes/_constant_nodes_builtin.py

"""
Tệp này định nghĩa và đăng ký tất cả các ConstantNode dựng sẵn trong hệ thống.
Bao gồm các hằng số chung và các hằng số đặc biệt cho lĩnh vực tài chính.
"""

# Sử dụng import tương đối để giao tiếp với các module anh em
import numpy as np
from .registry import register_node_by_spec, NodeSpec
from ._nodes import ConstantNode
from .semantic_typing import SemanticType
from . import names as nms

# == A. Hằng số Số học Chung (Ephemeral Random Constants - ERCs)
# == Mục đích: Cung cấp "vật liệu xây dựng" thô cho Evo-worker.
# == Kiểu: NUMERICAL, không có ngữ nghĩa cụ thể.
# ===================================================================

# Tạo một loạt các hằng số số học từ -1.0 đến 1.0
for value in np.round(np.arange(-1.0, 1.1, 0.1), 2):
    sign_char = "P" if value >= 0 else "N"
    name_str = str(abs(value)).replace('.', '_')
    node_id = nms.CONST_NUM_TEMPLATE.format(sign_char=sign_char, name=name_str)
    description = f"Generic numerical constant with value {value}"
    
    register_node_by_spec(
        node_id=node_id,
        spec=NodeSpec(
            node_class=ConstantNode,
            description=description,
            return_type=SemanticType.NUMERICAL,
            params={'value': float(value), 'use_normalize': False},
            node_type='constant'
        )
    )


# ===================================================================
# == B. Đăng ký các Hằng số Đặc biệt (Domain-Specific Constants)
# == Các hằng số này là các ngưỡng kỹ thuật, cần được chuẩn hóa.
# ===================================================================

# --- Ngưỡng cho các chỉ báo Động lượng (Momentum) ---

register_node_by_spec(
    node_id=nms.CONST_RSI_OVERBOUGHT,
    spec=NodeSpec(
        node_class=ConstantNode,
        description='RSI Overbought Threshold (70)',
        return_type=SemanticType.MOMENTUM,
        params={
            'value': 70.0,
            'use_normalize': True,
            'source_range': (0, 100),
            'target_range': (-1, 1),
        },
        node_type='constant'
    )
)

register_node_by_spec(
    node_id=nms.CONST_RSI_OVERSOLD,
    spec=NodeSpec(
        node_class=ConstantNode,
        description='RSI Oversold Threshold (30)',
        return_type=SemanticType.MOMENTUM,
        params={
            'value': 30.0,
            'use_normalize': True,
            'source_range': (0, 100),
            'target_range': (-1, 1)
        },
        node_type='constant'
    )
)

register_node_by_spec(
    node_id=nms.CONST_STOCH_OVERBOUGHT,
    spec=NodeSpec(
        node_class=ConstantNode,
        description='Stochastic Overbought Threshold (80)',
        return_type=SemanticType.MOMENTUM,
        params={
            'value': 80.0,
            'use_normalize': True,
            'source_range': (0, 100),
            'target_range': (-1, 1)
        },
        node_type='constant'
    )
)

register_node_by_spec(
    node_id=nms.CONST_STOCH_OVERSOLD,
    spec=NodeSpec(
        node_class=ConstantNode,
        description='Stochastic Oversold Threshold (20)',
        return_type=SemanticType.MOMENTUM,
        params={
            'value': 20.0,
            'use_normalize': True,
            'source_range': (0, 100),
            'target_range': (-1, 1)
        },
        node_type='constant'
    )
)


# --- Ngưỡng cho các chỉ báo Xu hướng (Trend) ---

register_node_by_spec(
    node_id=nms.CONST_ADX_STRONG_TREND,
    spec=NodeSpec(
        node_class=ConstantNode,
        description='ADX Strong Trend Threshold (25)',
        return_type=SemanticType.TREND,
        params={
            'value': 25.0,
            'use_normalize': True,
            'source_range': (0, 100), # ADX cũng trong khoảng 0-100
            'target_range': (-1, 1)
        },
        node_type='constant'
    )
)

# ===================================================================
# == C. Hằng số Quyết định (Kết quả của Decision Maker)
# ===================================================================
DECISION_SIGNALS = {
    # Mua
    nms.CONST_DECISION_BUY_IMMEDIATE:   (0.95, "Signal: Buy immediately with high confidence"),
    nms.CONST_DECISION_BUY_STRONG:      (0.8, "Signal: Strong indication to buy"),
    nms.CONST_DECISION_BUY_MODERATE:    (0.5, "Signal: Moderate indication to buy, consider confirming"),
    nms.CONST_DECISION_ACCUMULATE:      (0.3, "Signal: Accumulate/Buy on dips"),
    # Giữ
    nms.CONST_DECISION_HOLD_NEUTRAL:    (0.0, "Signal: Hold, no clear direction"),
    nms.CONST_DECISION_HOLD_POSITIVE:   (0.1, "Signal: Hold with positive outlook"),
    nms.CONST_DECISION_HOLD_NEGATIVE:   (-0.1,"Signal: Hold but with caution, negative outlook"),
    # Bán
    nms.CONST_DECISION_REDUCE_POSITION: (-0.3,"Signal: Consider reducing position/Take partial profit"),
    nms.CONST_DECISION_SELL_MODERATE:   (-0.5,"Signal: Moderate indication to sell"),
    nms.CONST_DECISION_SELL_STRONG:     (-0.8,"Signal: Strong indication to sell"),
    nms.CONST_DECISION_SELL_IMMEDIATE:  (-0.95,"Signal: Sell immediately with high confidence"),
}
for name, (value, desc) in DECISION_SIGNALS.items():
    register_node_by_spec(name, NodeSpec(ConstantNode, desc, return_type=SemanticType.DECISION_SIGNAL, 
                                         params={'value': value, 'use_normalize': False},
                                         node_type='constant'))

# ===================================================================
# == D. Hằng số Quản lý Rủi ro (Kết quả của Risk Manager)
# ===================================================================
RISK_LEVELS = {
    nms.CONST_RISK_VERY_LOW:    (0.1, "Risk Level: Very Low, suitable for capital preservation"),
    nms.CONST_RISK_LOW:         (0.3, "Risk Level: Low, conservative approach"),
    nms.CONST_RISK_MODERATE:    (0.5, "Risk Level: Moderate, balanced risk/reward"),
    nms.CONST_RISK_HIGH:        (0.8, "Risk Level: High, requires close monitoring"),
    nms.CONST_RISK_VERY_HIGH:   (0.95, "Risk Level: Very High, speculative"),
}
for name, (value, desc) in RISK_LEVELS.items():
    register_node_by_spec(name, NodeSpec(ConstantNode, desc, return_type=SemanticType.RISK_LEVEL, 
                                         params={'value': value, 'use_normalize': False},
                                         node_type='constant'))

# ===================================================================
# == E. Hằng số Đánh giá Cơ hội (Kết quả của Opportunity Finder)
# ===================================================================
OPPORTUNITY_RATINGS = {
    nms.CONST_OPP_RATING_TOP_TIER:    (0.95, "Opportunity Rating: A top-tier opportunity, high conviction"),
    nms.CONST_OPP_RATING_STRONG:    (0.8, "Opportunity Rating: A strong opportunity, worth investigating"),
    nms.CONST_OPP_RATING_INTERESTING: (0.5, "Opportunity Rating: Interesting, add to watchlist"),
    nms.CONST_OPP_RATING_NEUTRAL:   (0.2, "Opportunity Rating: Neutral, no special signal"),
    nms.CONST_OPP_RATING_AVOID:     (0.0, "Opportunity Rating: Low potential, probably avoid"),
}
for name, (value, desc) in OPPORTUNITY_RATINGS.items():
    register_node_by_spec(name, NodeSpec(ConstantNode, desc, return_type=SemanticType.OPPORTUNITY_RATING,
                                         params={'value': value, 'use_normalize': False},
                                         node_type='constant'))