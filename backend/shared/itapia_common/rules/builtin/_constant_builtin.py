# itapia_common/rules/nodes/_constant_nodes_builtin.py

"""
Tệp này định nghĩa và đăng ký tất cả các ConstantNode dựng sẵn trong hệ thống.
Bao gồm các hằng số chung và các hằng số đặc biệt cho lĩnh vực tài chính.
"""

# Sử dụng import tương đối để giao tiếp với các module anh em
from typing import Set
import numpy as np
from itapia_common.rules.nodes.registry import register_node_by_spec, NodeSpec
from itapia_common.rules.nodes import ConstantNode
from itapia_common.schemas.enums import SemanticType
from itapia_common.rules import names as nms

# == A. Hằng số Số học Chung (Ephemeral Random Constants - ERCs)
# == Mục đích: Cung cấp "vật liệu xây dựng" thô cho Evo-worker.
# == Kiểu: NUMERICAL, không có ngữ nghĩa cụ thể.
# ===================================================================

# Tạo một loạt các hằng số số học từ -1.0 đến 1.0
const_values: Set[float] = set()
# Thêm các giá trị chi tiết trong khoảng [-1, 1]
for value in np.round(np.arange(-1.0, 1.1, 0.1), 2):
    const_values.add(float(value))
# Thêm các giá trị nguyên lớn hơn
for value in np.round(np.arange(-10.0, 11.0, 1.0), 2):
    const_values.add(float(value))

for value in sorted(list(const_values)):
    node_name = nms.CONST_NUM(value)
    description = f"Generic numerical constant with value {value}"
    
    register_node_by_spec(
        node_name=node_name,
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
    node_name=nms.CONST_RSI_OVERBOUGHT,
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
    node_name=nms.CONST_RSI_OVERSOLD,
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
    node_name=nms.CONST_STOCH_OVERBOUGHT,
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
    node_name=nms.CONST_STOCH_OVERSOLD,
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
    node_name=nms.CONST_ADX_STRONG_TREND,
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