# itapia_common/rules/explainer.py

from typing import Dict

# Import các thành phần cần thiết
from itapia_common.rules.nodes import _TreeNode, ConstantNode, VarNode, OperatorNode
from itapia_common.rules.rule import Rule # Truy cập registry để lấy description
from itapia_common.rules import names as nms

class RuleExplainerOrchestrator:
    """
    Dịch một cây quy tắc (_TreeNode) thành một chuỗi văn bản
    có thể đọc được bởi con người.
    """
    INFIX_OPR_MAPPING = {
        nms.OPR_ADD2: '+',
        nms.OPR_SUB2: '-',
        nms.OPR_MUL2: '*',
        nms.OPR_DIV2: '/',
        nms.OPR_GT: 'is greater than',
        nms.OPR_LT: 'is less than',
        nms.OPR_GTE: 'is greater than or equal to',
        nms.OPR_LTE: 'is less than or equal to',
        nms.OPR_EQ: 'is equal to',
        nms.OPR_NEQ: 'is not equal to'
    }
    
    def explain_node(self, node: _TreeNode) -> str:
        """
        Hàm đệ quy chính để duyệt và giải thích từng node.
        """
        if isinstance(node, ConstantNode):
            # Với Constant, ta muốn hiển thị tên có ý nghĩa của nó nếu có,
            # hoặc giá trị nếu không.
            # node.name chính là key trong registry, ví dụ 'CONST_RSI_OVERBOUGHT'
            return f"the threshold '{node.node_name}' (value: {node.value})"

        if isinstance(node, VarNode):
            # Với VarNode, ta có thể dùng description đã định nghĩa sẵn
            return node.description

        if isinstance(node, OperatorNode):
            # Đây là phần phức tạp nhất, xử lý logic của toán tử
            
            # Đệ quy giải thích các node con trước
            child_explanations = [self.explain_node(child) for child in node.children]

            op_name = node.node_name.upper()

            # Xử lý các toán tử có cú pháp đặc biệt (infix, functions)
            if op_name in self.INFIX_OPR_MAPPING.keys():
                # Định dạng infix: (child1 op child2)
                return f"({child_explanations[0]} {self.INFIX_OPR_MAPPING[op_name]} {child_explanations[1]})"

            if op_name == nms.OPR_AND:
                return "(" + " AND ".join(child_explanations) + ")"
            
            if op_name == nms.OPR_OR:
                return "(" + " OR ".join(child_explanations) + ")"
            
            if op_name == nms.OPR_NOT:
                return f"NOT ({child_explanations[0]})"
            
            if op_name == nms.OPR_IF_THEN_ELSE:
                return f"IF {child_explanations[0]} THEN {child_explanations[1]} ELSE {child_explanations[2]}"

            # Xử lý các toán tử kết luận (là các hàm)
            if op_name.startswith('OPR_TO_'):
                # Định dạng function-like: Function(child1)
                func_name = node.description.split(' and casts')[0] # Lấy phần mô tả chính
                return f"{func_name} on the result of ({child_explanations[0]})"

            # Fallback cho các hàm khác (ví dụ: ABS, LOG2)
            return f"{op_name}({', '.join(child_explanations)})"

        return "Unknown Node"

    def explain_rule(self, rule: Rule) -> str:
        """
        Hàm cấp cao để giải thích một đối tượng Rule hoàn chỉnh.
        """
        if not hasattr(rule, 'root') or not isinstance(rule.root, _TreeNode):
            raise TypeError("Input must be a valid Rule object with a root node.")
            
        logic_explanation = self.explain_node(rule.root)
        
        return f"Rule '{rule.name}': This rule calculates a final score based on the following logic: {logic_explanation}."