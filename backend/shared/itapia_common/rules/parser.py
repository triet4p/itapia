# itapia_common/rules/serializer.py

from typing import Any, Dict

from itapia_common.schemas.entities.rules import NodeEntity

# Import node classes for type checking
from .nodes import OperatorNode, _TreeNode
from .nodes.registry import create_node


def serialize_tree(node: _TreeNode) -> NodeEntity:
    """Serialize a Node tree (starting from the root node) into a nested dictionary structure.
    This function works recursively.

    Args:
        node (_TreeNode): The root node of the tree or branch to convert.

    Returns:
        Dict[str, Any]: A dictionary representing the tree.

    Raises:
        TypeError: If the input is not an instance of _TreeNode.
    """
    if not isinstance(node, _TreeNode):
        raise TypeError("Input must be an instance of _TreeNode.")

    # Create basic dictionary
    # Note: node.node_name has been .upper() in the constructor
    node_name = node.node_name
    node_children = None

    # If it's an Operator, recursively serialize its children
    if isinstance(node, OperatorNode):
        if node.children:  # Only add 'children' key if present
            node_children = [serialize_tree(child) for child in node.children]

    # Other node types (Constant, Var) don't have 'children' or special parameters
    # so no additional processing is needed. Their names (node_name) are sufficient for reconstruction.

    return NodeEntity(node_name=node_name, children=node_children)


def parse_tree(data: NodeEntity) -> _TreeNode:
    """Parse a dictionary structure and reconstruct a complete Node tree.
    This function works recursively and uses the Node Factory.

    Args:
        data (Dict[str, Any]): Dictionary representing a node (and its children).

    Returns:
        _TreeNode: The root node of the reconstructed tree or branch.

    Raises:
        TypeError: If children data is not a list.
        ValueError: If there's an error creating the node.
    """
    node_name = data.node_name

    # Prepare parameters to be passed to the factory
    # These are dynamic parameters, not predefined in the Spec
    factory_kwargs: Dict[str, Any] = {}

    # 1. Recursively parse child nodes first (if any)
    if data.children is not None:
        children_data = data.children
        if not isinstance(children_data, list):
            raise TypeError("'children' must be a list.")

        # Recreate each child node and add to kwargs
        factory_kwargs["children"] = [
            parse_tree(child_data) for child_data in children_data
        ]

    # Add other special parameters here if needed...

    # 3. Call Node Factory to create the current node
    # The node_name of a node in the tree will be auto-generated or can be taken from dict if desired
    # Here, we simplify by using the node_name directly
    try:
        # The factory will use node_name to look up the Spec and use kwargs to pass dynamic parameters
        node_instance = create_node(node_name=node_name, **factory_kwargs)
    except Exception as e:
        # Wrap the original error to provide additional context when debugging
        raise ValueError(
            f"Error creating node with name '{node_name}'. Original error: {e}"
        ) from e

    return node_instance
