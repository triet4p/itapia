# itapia_common/rules/nodes/_operator_nodes_builtin.py

"""
Tệp này định nghĩa và đăng ký tất cả các OperatorNode dựng sẵn trong hệ thống.
"""

import math

from itapia_common.rules.nodes.registry import register_node_by_spec, NodeSpec
from itapia_common.rules.nodes import FunctionalOperatorNode, BranchOperatorNode
from itapia_common.schemas.enums import SemanticType
from itapia_common.rules import names as nms

# ===================================================================
# == A. Các hàm Phụ trợ (Helper Functions)
# ===================================================================

def _sigmoid(x: float) -> float:
    """Hàm Sigmoid, ánh xạ một số bất kỳ về khoảng (0, 1)."""
    if x < -10: return 0.0
    if x > 10: return 1.0
    return 1 / (1 + math.exp(-x))

def _scaled_tanh(x: float) -> float:
    """Hàm Tanh, ánh xạ một số bất kỳ về khoảng (-1, 1)."""
    return math.tanh(x)

# ===================================================================
# == B. Đăng ký các Toán tử Toán học
# ===================================================================

register_node_by_spec(nms.OPR_ADD2, NodeSpec(
    node_class=FunctionalOperatorNode, description="Adds two values",
    return_type=SemanticType.NUMERICAL, args_type=[SemanticType.NUMERICAL, SemanticType.NUMERICAL], node_type='operator',
    params={'num_child': 2, 'opr_func': lambda x, y: x + y}
))
register_node_by_spec(nms.OPR_SUB2, NodeSpec(
    node_class=FunctionalOperatorNode, description="Subtracts second value from the first (arg1 - arg2)",
    return_type=SemanticType.NUMERICAL, args_type=[SemanticType.NUMERICAL, SemanticType.NUMERICAL], node_type='operator',
    params={'num_child': 2, 'opr_func': lambda x, y: x - y}
))
register_node_by_spec(nms.OPR_MUL2, NodeSpec(
    node_class=FunctionalOperatorNode, description="Multiplies two values",
    return_type=SemanticType.NUMERICAL, args_type=[SemanticType.NUMERICAL, SemanticType.NUMERICAL], node_type='operator',
    params={'num_child': 2, 'opr_func': lambda x, y: x * y}
))
register_node_by_spec(nms.OPR_DIV2, NodeSpec(
    node_class=FunctionalOperatorNode, description="Divides first value by the second (arg1 / arg2). Returns 0 if divisor is 0.",
    return_type=SemanticType.NUMERICAL, args_type=[SemanticType.NUMERICAL, SemanticType.NUMERICAL], node_type='operator',
    params={'num_child': 2, 'opr_func': lambda x, y: x / y if y != 0 else 0.0}
))
register_node_by_spec(nms.OPR_POW2, NodeSpec(
    node_class=FunctionalOperatorNode, description="Raises the first value to the power of the second (arg1 ^ arg2)",
    return_type=SemanticType.NUMERICAL, args_type=[SemanticType.NUMERICAL, SemanticType.NUMERICAL], node_type='operator',
    params={'num_child': 2, 'opr_func': lambda x, y: math.pow(x, y)}
))
register_node_by_spec(nms.OPR_LOG2, NodeSpec(
    node_class=FunctionalOperatorNode, description="Calculates the base-2 logarithm of a value. Returns 0 for non-positive input.",
    return_type=SemanticType.NUMERICAL, args_type=[SemanticType.NUMERICAL], node_type='operator',
    params={'num_child': 1, 'opr_func': lambda x: math.log2(x) if x > 0 else 0.0}
))
register_node_by_spec(nms.OPR_ABS, NodeSpec(
    node_class=FunctionalOperatorNode, description="Calculates the absolute value of a number",
    return_type=SemanticType.NUMERICAL, args_type=[SemanticType.NUMERICAL], node_type='operator',
    params={'num_child': 1, 'opr_func': lambda x: abs(x)}
))

# ===================================================================
# == C. Đăng ký các Toán tử So sánh (Luôn trả về 1.0 hoặc 0.0)
# ===================================================================

register_node_by_spec(nms.OPR_GT, NodeSpec(
    node_class=FunctionalOperatorNode, description="Greater Than (>). Returns 1.0 if arg1 > arg2, else 0.0.",
    return_type=SemanticType.BOOLEAN, args_type=[SemanticType.ANY, SemanticType.ANY], node_type='operator',
    params={'num_child': 2, 'opr_func': lambda x, y: 1.0 if x > y else 0.0}
))
register_node_by_spec(nms.OPR_LT, NodeSpec(
    node_class=FunctionalOperatorNode, description="Less Than (<). Returns 1.0 if arg1 < arg2, else 0.0.",
    return_type=SemanticType.BOOLEAN, args_type=[SemanticType.ANY, SemanticType.ANY], node_type='operator',
    params={'num_child': 2, 'opr_func': lambda x, y: 1.0 if x < y else 0.0}
))
register_node_by_spec(nms.OPR_GTE, NodeSpec(
    node_class=FunctionalOperatorNode, description="Greater Than or Equal (>=). Returns 1.0 if arg1 >= arg2, else 0.0.",
    return_type=SemanticType.BOOLEAN, args_type=[SemanticType.ANY, SemanticType.ANY], node_type='operator',
    params={'num_child': 2, 'opr_func': lambda x, y: 1.0 if x >= y else 0.0}
))
register_node_by_spec(nms.OPR_LTE, NodeSpec(
    node_class=FunctionalOperatorNode, description="Less Than or Equal (<=). Returns 1.0 if arg1 <= arg2, else 0.0.",
    return_type=SemanticType.BOOLEAN, args_type=[SemanticType.ANY, SemanticType.ANY], node_type='operator',
    params={'num_child': 2, 'opr_func': lambda x, y: 1.0 if x <= y else 0.0}
))
register_node_by_spec(nms.OPR_EQ, NodeSpec(
    node_class=FunctionalOperatorNode, description="Equal (==). Returns 1.0 if values are close, else 0.0.",
    return_type=SemanticType.BOOLEAN, args_type=[SemanticType.ANY, SemanticType.ANY], node_type='operator',
    params={'num_child': 2, 'opr_func': lambda x, y: 1.0 if math.isclose(x, y) else 0.0}
))
register_node_by_spec(nms.OPR_NEQ, NodeSpec(
    node_class=FunctionalOperatorNode, description="Not Equal (!=). Returns 1.0 if values are not close, else 0.0.",
    return_type=SemanticType.BOOLEAN, args_type=[SemanticType.ANY, SemanticType.ANY], node_type='operator',
    params={'num_child': 2, 'opr_func': lambda x, y: 1.0 if not math.isclose(x, y) else 0.0}
))

# ===================================================================
# == D. Đăng ký các Toán tử Logic (Luôn trả về 1.0 hoặc 0.0)
# ===================================================================

register_node_by_spec(nms.OPR_AND, NodeSpec(
    node_class=FunctionalOperatorNode, description="Logical AND. Returns 1.0 if all args > 0, else 0.0.",
    return_type=SemanticType.BOOLEAN, args_type=[SemanticType.BOOLEAN, SemanticType.BOOLEAN], node_type='operator',
    params={'num_child': 2, 'opr_func': lambda *args: 1.0 if all(arg > 0 for arg in args) else 0.0}
))
register_node_by_spec(nms.OPR_OR, NodeSpec(
    node_class=FunctionalOperatorNode, description="Logical OR. Returns 1.0 if any arg > 0, else 0.0.",
    return_type=SemanticType.BOOLEAN, args_type=[SemanticType.BOOLEAN, SemanticType.BOOLEAN], node_type='operator',
    params={'num_child': 2, 'opr_func': lambda *args: 1.0 if any(arg > 0 for arg in args) else 0.0}
))
register_node_by_spec(nms.OPR_NOT, NodeSpec(
    node_class=FunctionalOperatorNode, description="Logical NOT. Returns 1.0 if arg <= 0, else 0.0.",
    return_type=SemanticType.BOOLEAN, args_type=[SemanticType.BOOLEAN], node_type='operator',
    params={'num_child': 1, 'opr_func': lambda x: 1.0 if not (x > 0) else 0.0}
))

# ===================================================================
# == E. Đăng ký các Toán tử Điều kiện
# ===================================================================

register_node_by_spec(nms.OPR_IF_THEN_ELSE, NodeSpec(
    node_class=BranchOperatorNode,
    description="IF condition > 0 THEN evaluate first child ELSE second child.",
    return_type=SemanticType.ANY, # Kiểu trả về phụ thuộc vào nhánh được chọn
    args_type=[SemanticType.BOOLEAN, SemanticType.ANY, SemanticType.ANY],
    node_type='operator',
    params={}
))

# ===================================================================
# == F. Đăng ký các Toán tử Kết luận Đặc biệt (Return Operators)
# ===================================================================

register_node_by_spec(nms.OPR_TO_DECISION_SIGNAL, NodeSpec(
    node_class=FunctionalOperatorNode,
    description="Scales any numerical input to [-1, 1] and casts it as a DECISION_SIGNAL.",
    return_type=SemanticType.DECISION_SIGNAL, args_type=[SemanticType.ANY], node_type='operator',
    params={'num_child': 1, 'opr_func': lambda x: _scaled_tanh(x)}
))
register_node_by_spec(nms.OPR_TO_RISK_LEVEL, NodeSpec(
    node_class=FunctionalOperatorNode,
    description="Scales any numerical input to [0, 1] and casts it as a RISK_LEVEL.",
    return_type=SemanticType.RISK_LEVEL, args_type=[SemanticType.ANY], node_type='operator',
    params={'num_child': 1, 'opr_func': lambda x: _sigmoid(x)}
))
register_node_by_spec(nms.OPR_TO_OPPORTUNITY_RATING, NodeSpec(
    node_class=FunctionalOperatorNode,
    description="Scales any numerical input to [0, 1] and casts it as an OPPORTUNITY_RATING.",
    return_type=SemanticType.OPPORTUNITY_RATING, args_type=[SemanticType.ANY], node_type='operator',
    params={'num_child': 1, 'opr_func': lambda x: _sigmoid(x)}
))