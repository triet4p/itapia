from abc import ABC, abstractmethod
from typing import Literal, Any, Set, Tuple, Dict, List
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport
from itapia_common.rules.exceptions import NotFoundVarPathError
from itapia_common.schemas.entities.rules import SemanticType, NodeType

def normalize(raw_value: int|float, default_value: int|float,
              source_range: Tuple[float, float], target_range: Tuple[float, float]) -> float:
    """Normalize a value from a source range to a target range.
    
    Args:
        raw_value (int | float): The value to normalize
        default_value (int | float): Default value to return if raw_value is not numeric
        source_range (Tuple[float, float]): The source range (min, max)
        target_range (Tuple[float, float]): The target range (min, max)
        
    Returns:
        float: The normalized value in the target range
    """
    if not isinstance(raw_value, (int, float)):
        return default_value
    
    source_min, source_max = source_range
    target_min, target_max = target_range

    # Clamp the value within the source range
    clamped_value = max(source_min, min(source_max, raw_value))
    
    # Normalization formula
    source_span = source_max - source_min
    target_span = target_max - target_min
    
    if source_span == 0:
        return target_min
        
    scaled_value = (clamped_value - source_min) / source_span
    return target_min + (scaled_value * target_span)

def denormalize(encoded_value: int|float,
                source_range: Tuple[float, float], target_range: Tuple[float, float]) -> float:
    """Denormalize a value from a target range back to a source range.
    
    Args:
        encoded_value (int | float): The normalized value to denormalize
        source_range (Tuple[float, float]): The source range (min, max)
        target_range (Tuple[float, float]): The target range (min, max)
        
    Returns:
        float: The denormalized value in the source range
    """
    source_min, source_max = source_range
    target_min, target_max = target_range
    
    target_span = target_max - target_min
    source_span = source_max - source_min

    if target_span == 0:
        return source_min

    scaled_value = (encoded_value - target_min) / target_span
    return source_min + (scaled_value * source_span)


class _TreeNode(ABC):
    """Abstract base class for all tree nodes in the rule system."""
    
    def __init__(self, node_name: str, node_type: NodeType,
                 description: str, return_type: SemanticType):
        """Initialize a tree node.
        
        Args:
            node_name (str): The unique name of the node
            node_type (NodeType): The type of node (CONSTANT, VARIABLE, OPERATOR)
            description (str): A human-readable description of the node
            return_type (SemanticType): The semantic type of the value returned by this node
        """
        self.node_name = node_name
        self.node_type = node_type
        self.description = description
        self.return_type = return_type
        
    @abstractmethod
    def evaluate(self, report: QuickCheckAnalysisReport) -> float:
        """Evaluate the node and return a float value.
        
        Args:
            report (QuickCheckAnalysisReport): The analysis report to evaluate against
            
        Returns:
            float: The evaluated result of this node
        """
        pass
    
    def __eq__(self, value: object) -> bool:
        """Check equality between two tree nodes.
        
        Args:
            value (object): Another object to compare with
            
        Returns:
            bool: True if both nodes have the same name and return type
        """
        if not isinstance(value, _TreeNode):
            return False
        return self.node_name == value.node_name and self.return_type == value.return_type
    
class ConstantNode(_TreeNode):
    """A node that represents a constant value."""
    
    def __init__(self, node_name: str, description: str, return_type: SemanticType,
                 value: float, use_normalize: bool = False,
                 source_range: Tuple[float, float]|None = None,
                 target_range: Tuple[float, float]|None = None):
        """Initialize a constant node.
        
        Args:
            node_name (str): The unique name of the node
            description (str): A human-readable description of the node
            return_type (SemanticType): The semantic type of the value returned by this node
            value (float): The constant value
            use_normalize (bool): Whether to normalize the value (default: False)
            source_range (Tuple[float, float] | None): The source range for normalization
            target_range (Tuple[float, float] | None): The target range for normalization
        """
        super().__init__(node_name, node_type=NodeType.CONSTANT, description=description, return_type=return_type)
        self.value = value
        
        if use_normalize:
            if source_range is None or target_range is None:
                raise ValueError('use_normalize=True requires source range and target range')
        
        self.source_range = source_range
        self.target_range = target_range
        self.use_normalize = use_normalize
    
    def evaluate(self, report: QuickCheckAnalysisReport) -> float:
        """Evaluate the constant node and return its value.
        
        Args:
            report (QuickCheckAnalysisReport): The analysis report (unused for constants)
            
        Returns:
            float: The constant value, normalized if use_normalize is True
        """
        if not self.use_normalize:
            return self.value
        return normalize(self.value, 0, self.source_range, self.target_range)
    
class VarNode(_TreeNode):
    """Base class for "Smart Variables".
    
    A VarNode knows how to extract a raw value from a report and encode it into a number.
    """
    
    def __init__(self, node_name: str, description: str, return_type: SemanticType,
                 path: str, default_value: float = 0.0):
        """Initialize a variable node.
        
        Args:
            node_name (str): The unique name of the node
            description (str): A human-readable description of the node
            return_type (SemanticType): The semantic type of the value returned by this node
            path (str): The path to extract the value from the report
            default_value (float): The default value to return if the path is not found
        """
        # Note: node_type will be assigned in the subclass
        super().__init__(node_name, node_type=NodeType.VARIABLE, description=description, return_type=return_type)
        self.path = path
        self.default_value = default_value
        
    def _get_raw_value_from_report(self, report: QuickCheckAnalysisReport) -> Any:
        """Internal function to get raw value, supporting object attributes, dict keys, and list indices.
        
        Args:
            report (QuickCheckAnalysisReport): The analysis report to extract values from
            
        Returns:
            Any: The raw value extracted from the report
            
        Raises:
            NotFoundVarPathError: If the path cannot be resolved
        """
        try:
            keys = self.path.split('.')
            value = report
            for key in keys:
                if value is None:
                    # If an intermediate link is None, stop and return None
                    return None

                if key.isdigit() or (key.startswith('-') and key[1:].isdigit()):
                    # Handle list index case (e.g., '0', '-1')
                    index = int(key)
                    if isinstance(value, list) and -len(value) <= index < len(value):
                        value = value[index]
                    else:
                        # Invalid index or value is not a list
                        return None
                elif isinstance(value, dict):
                    # Handle dictionary key case
                    value = value.get(key)
                else:
                    # Handle object attribute case
                    value = getattr(value, key)
            
            return value
        except (AttributeError, KeyError, TypeError, IndexError):
            raise NotFoundVarPathError(self.path)

    def evaluate(self, report: QuickCheckAnalysisReport) -> float:
        """Main execution flow of a VarNode.
        
        1. Get the raw value, throw an error if the path is wrong (this is important, it's different from having a path but no value)
        2. If none, return the default value
        3. If present, encode it and return
        
        Args:
            report (QuickCheckAnalysisReport): The analysis report to evaluate against
            
        Returns:
            float: The encoded value from the report or default value
        """
        raw_value = self._get_raw_value_from_report(report)
        if raw_value is None:
            return self.default_value
        
        return self.encode(raw_value)

    @abstractmethod
    def encode(self, raw_value: Any) -> float:
        """Encode a raw value into a float.
        
        Args:
            raw_value (Any): The raw value to encode
            
        Returns:
            float: The encoded float value
        """
        pass
    
    @abstractmethod
    def decode(self, encoded_value: float) -> Any:
        """Decode a float value back to its raw form (useful for interpretation).
        
        Args:
            encoded_value (float): The encoded value to decode
            
        Returns:
            Any: The decoded raw value
        """
        pass

class NumericalVarNode(VarNode):
    """Variable node for numerical values."""
    
    def __init__(self, node_name: str, description: str, return_type: SemanticType,
                 path: str, default_value: float = 0.0,
                 source_range: Tuple[float, float] = (0, 100),
                 target_range: Tuple[float, float] = (-1, 1)):
        """Initialize a numerical variable node.
        
        Args:
            node_name (str): The unique name of the node
            description (str): A human-readable description of the node
            return_type (SemanticType): The semantic type of the value returned by this node
            path (str): The path to extract the value from the report
            default_value (float): The default value to return if the path is not found
            source_range (Tuple[float, float]): The source range for normalization (default: (0, 100))
            target_range (Tuple[float, float]): The target range for normalization (default: (-1, 1))
        """
        super().__init__(node_name, description, return_type, path, default_value)
        self.source_range = source_range
        self.target_range = target_range

    def encode(self, raw_value: float) -> float:
        """Normalize a numerical value from `source_range` to `target_range`.
        
        Example: Normalize RSI (0-100) to scale (-1, 1).
        
        Args:
            raw_value (float): The raw numerical value to normalize
            
        Returns:
            float: The normalized value in the target range
        """
        return normalize(raw_value, self.default_value, self.source_range, self.target_range)

    def decode(self, encoded_value: float) -> float:
        """Decode a normalized value back to the source range.
        
        Args:
            encoded_value (float): The normalized value to denormalize
            
        Returns:
            float: The denormalized value in the source range
        """
        return denormalize(encoded_value, self.source_range, self.target_range)

class CategoricalVarNode(VarNode):
    """Variable node for categorical (string) values."""
    
    def __init__(self, node_name: str, description: str, return_type: SemanticType,
                 path: str, default_value: float = 0.0,
                 mapping: Dict[str, float] = None,
                 use_default_label_mapping: bool = False,
                 available_values: Set[str]|None = None):
        """Initialize a categorical variable node.
        
        Args:
            node_name (str): The unique name of the node
            description (str): A human-readable description of the node
            return_type (SemanticType): The semantic type of the value returned by this node
            path (str): The path to extract the value from the report
            default_value (float): The default value to return if the path is not found
            mapping (Dict[str, float]): Mapping of string values to float values
            use_default_label_mapping (bool): Whether to create a default label mapping
            available_values (Set[str] | None): Set of possible values for default mapping
        """
        super().__init__(node_name, description, return_type, path, default_value)
        self.mapping = mapping if mapping is not None else {}
        if use_default_label_mapping:
            self.create_label_mapping(available_values)
        # Create a reverse mapping for efficient decoding
        self._reverse_mapping = {v: k for k, v in self.mapping.items()}
        
    def create_label_mapping(self, available_values: Set[str]) -> None:
        """Create a default label mapping for categorical values.
        
        Args:
            available_values (Set[str]): Set of possible string values to map
        """
        it = 0
        self.mapping = {}
        for val in available_values:
            self.mapping[val] = it
            it += 1

    def encode(self, raw_value: str) -> float:
        """Map a string value to a float based on the `mapping` dictionary.
        
        Args:
            raw_value (str): The raw string value to encode
            
        Returns:
            float: The mapped float value or default value if not found
        """
        if not isinstance(raw_value, str):
            return self.default_value
        return self.mapping.get(raw_value, self.default_value)

    def decode(self, encoded_value: float) -> str:
        """Find the original string from an encoded value.
        
        Args:
            encoded_value (float): The encoded value to decode
            
        Returns:
            str: The original string value or "unknown" if not found
        """
        # Need to handle the case where multiple keys map to the same value, here we take the first key
        return self._reverse_mapping.get(encoded_value, "unknown")

    @staticmethod
    def get_possible_values_from_schema(schema_class: Any, path: str) -> Set[str]:
        """Static function to get possible values of a Literal field from a schema.
        
        Useful for Evo-worker or UI to know the available options.
        
        Usage example: get_possible_values_from_schema(QuickCheckReport, "technical.daily.trend.ma_direction")
        
        Args:
            schema_class (Any): The schema class to extract values from
            path (str): The dot-separated path to the field
            
        Returns:
            Set[str]: Set of possible string values for the field
            
        Raises:
            NotFoundVarPathError: If the path cannot be resolved
        """
        try:
            keys = path.split('.')
            current_class = schema_class
            for key in keys:
                field_info = current_class.model_fields[key]
                # Get the class of the field's data type
                current_class = field_info.annotation
            
            # After traversal, current_class will be the Literal type
            # Use __args__ to get the tuple of possible values
            return set(current_class.__args__)
        except (AttributeError, KeyError, TypeError):
            raise NotFoundVarPathError(path)
            
class OperatorNode(_TreeNode):
    """Node that performs an operation on its child nodes."""
    
    def __init__(self, node_name: str, description: str, num_child: int|None,
                 return_type: SemanticType, args_type: List[SemanticType],
                 children: List[_TreeNode] = []):
        """Initialize an operator node.
        
        Args:
            node_name (str): The unique name of the node
            description (str): A human-readable description of the node
            num_child (int | None): The expected number of child nodes (None for variable)
            return_type (SemanticType): The semantic type of the value returned by this node
            args_type (List[SemanticType]): The semantic types of the arguments
            children (List[_TreeNode]): Initial list of child nodes
        """
        super().__init__(node_name, node_type=NodeType.OPERATOR, description=description, return_type=return_type)
        self.num_child = num_child
        self.children = children
        
        if num_child is not None and num_child != len(args_type):
            raise ValueError('Length of args_type must equal num_child')
        
        self.args_type = args_type
        
    def add_child_node(self, child_node: _TreeNode) -> None:
        """Add a child node to this operator.
        
        Args:
            child_node (_TreeNode): The child node to add
            
        Raises:
            ValueError: If the node has a fixed number of children and is already full
        """
        if self.num_child is not None:
            if len(self.children) == self.num_child:
                raise ValueError('Children of this node is full!')
        self.children.append(child_node)
        
    def update_node(self, old_idx: int, new_node: _TreeNode) -> None:
        """Update a child node at a specific index.
        
        Args:
            old_idx (int): The index of the child node to replace
            new_node (_TreeNode): The new node to insert
            
        Raises:
            IndexError: If the index is invalid
        """
        if not (0 <= old_idx < len(self.children)):
            raise IndexError("Child node index is invalid.")
        self.children[old_idx] = new_node
        
    def clear(self) -> None:
        """Clear all child nodes."""
        self.children.clear()
        
    def check_valid_children(self) -> bool:
        """Check if the children configuration is valid.
        
        Returns:
            bool: True if the children configuration is valid
        """
        if self.num_child is None:
            return True
        if len(self.children) != self.num_child:
            return False
        return True
    
    @abstractmethod
    def _evaluate_valid(self, report: QuickCheckAnalysisReport) -> float:
        """Evaluate the operator with valid children.
        
        Args:
            report (QuickCheckAnalysisReport): The analysis report to evaluate against
            
        Returns:
            float: The result of the operation
        """
        pass
    
    def evaluate(self, report: QuickCheckAnalysisReport) -> float:
        """Evaluate the operator node.
        
        Args:
            report (QuickCheckAnalysisReport): The analysis report to evaluate against
            
        Returns:
            float: The result of the operation
            
        Raises:
            ValueError: If the children configuration is invalid
        """
        if not self.check_valid_children():
            raise ValueError('Children node are not valid')
        return self._evaluate_valid(report)
    
class FunctionalOperatorNode(OperatorNode):
    """Operator node that applies a function to its child nodes."""
    
    def __init__(self, node_name: str, description: str, num_child: int|None,
                 return_type: SemanticType, args_type: List[SemanticType], 
                 opr_func: Any, children: List[_TreeNode] = []):
        """Initialize a functional operator node.
        
        Args:
            node_name (str): The unique name of the node
            description (str): A human-readable description of the node
            num_child (int | None): The expected number of child nodes (None for variable)
            return_type (SemanticType): The semantic type of the value returned by this node
            args_type (List[SemanticType]): The semantic types of the arguments
            opr_func (Any): The function to apply to child results
            children (List[_TreeNode]): Initial list of child nodes
        """
        super().__init__(node_name, description, num_child, return_type, args_type, children)
        self.opr_func = opr_func
        
    def _evaluate_valid(self, report: QuickCheckAnalysisReport) -> float:
        """Evaluate the functional operator with valid children.
        
        Args:
            report (QuickCheckAnalysisReport): The analysis report to evaluate against
            
        Returns:
            float: The result of applying the function to child results
        """
        child_results = [child.evaluate(report) for child in self.children]
        return self.opr_func(*child_results)
    
class BranchOperatorNode(OperatorNode):
    """Conditional operator node: If A then B else C."""
    
    def __init__(self, node_name: str, description: str,
                 return_type: SemanticType, args_type: List[SemanticType],
                 children: List[_TreeNode] = []):
        """Initialize a branch operator node.
        
        Args:
            node_name (str): The unique name of the node
            description (str): A human-readable description of the node
            return_type (SemanticType): The semantic type of the value returned by this node
            args_type (List[SemanticType]): The semantic types of the arguments
            children (List[_TreeNode]): Initial list of child nodes (must have exactly 3)
        """
        super().__init__(node_name, description, num_child=3, 
                         return_type=return_type, args_type=args_type, children=children)
        
    def _evaluate_valid(self, report: QuickCheckAnalysisReport) -> float:
        """Evaluate the branch operator with valid children.
        
        Args:
            report (QuickCheckAnalysisReport): The analysis report to evaluate against
            
        Returns:
            float: The result of the conditional operation
        """
        condition = self.children[0].evaluate(report)
        
        if condition > 0:  # if condition == 1.0
            return self.children[1].evaluate(report)
        else:
            return self.children[2].evaluate(report)