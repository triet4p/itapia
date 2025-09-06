"""Rule explainer orchestrator for translating rule trees into human-readable text."""

from typing import Dict

# Import required components
from itapia_common.rules.nodes import _TreeNode, ConstantNode, VarNode, OperatorNode
from itapia_common.rules.rule import Rule  # Access registry to get description
from itapia_common.rules import names as nms


class RuleExplainerOrchestrator:
    """Translate a rule tree (_TreeNode) into human-readable text.
    
    Converts complex rule logic into natural language explanations.
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
        """Recursive function to traverse and explain each node.
        
        Args:
            node (_TreeNode): Tree node to explain
            
        Returns:
            str: Human-readable explanation of the node
        """
        if isinstance(node, ConstantNode):
            # For Constants, we want to display their meaningful name if available,
            # or value if not.
            # node.name is the key in registry, e.g. 'CONST_RSI_OVERBOUGHT'
            return f"the threshold '{node.node_name}' (value: {node.value})"

        if isinstance(node, VarNode):
            # For VarNode, we can use the predefined description
            return node.description

        if isinstance(node, OperatorNode):
            # This is the most complex part, handling operator logic
            
            # Recursively explain child nodes first
            child_explanations = [self.explain_node(child) for child in node.children]

            op_name = node.node_name.upper()

            # Handle operators with special syntax (infix, functions)
            if op_name in self.INFIX_OPR_MAPPING.keys():
                # Infix format: (child1 op child2)
                return f"({child_explanations[0]} {self.INFIX_OPR_MAPPING[op_name]} {child_explanations[1]})"

            if op_name == nms.OPR_AND:
                return "(" + " AND ".join(child_explanations) + ")"
            
            if op_name == nms.OPR_OR:
                return "(" + " OR ".join(child_explanations) + ")"
            
            if op_name == nms.OPR_NOT:
                return f"NOT ({child_explanations[0]})"
            
            if op_name == nms.OPR_IF_THEN_ELSE:
                return f"IF {child_explanations[0]} THEN {child_explanations[1]} ELSE {child_explanations[2]}"

            # Handle conclusion operators (functions)
            if op_name.startswith('OPR_TO_'):
                # Function-like format: Function(child1)
                func_name = node.description.split(' and casts')[0]  # Get main description part
                return f"{func_name} on the result of ({child_explanations[0]})"

            # Fallback for other functions (e.g.: ABS, LOG2)
            return f"{op_name}({', '.join(child_explanations)})"

        return "Unknown Node"

    def explain_rule(self, rule: Rule) -> str:
        """High-level function to explain a complete Rule object.
        
        Args:
            rule (Rule): Rule object to explain
            
        Returns:
            str: Human-readable explanation of the rule
            
        Raises:
            TypeError: If input is not a valid Rule object with a root node
        """
        if not hasattr(rule, 'root') or not isinstance(rule.root, _TreeNode):
            raise TypeError("Input must be a valid Rule object with a root node.")
            
        logic_explanation = self.explain_node(rule.root)
        
        return f"Rule '{rule.name}': This rule calculates a final score based on the following logic: {logic_explanation}."