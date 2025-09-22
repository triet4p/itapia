import inspect
from typing import Any, Dict, List, NamedTuple, Type

from itapia_common.schemas.entities.rules import NodeSpecEntity, NodeType, SemanticType

from ._nodes import _TreeNode


class NodeSpec(NamedTuple):
    """Specification for a node type."""

    node_class: Type[_TreeNode]
    description: str
    node_type: NodeType
    params: Dict[str, Any]
    return_type: SemanticType
    args_type: List[SemanticType] | None = None


_NODE_REGISTRY: Dict[str, NodeSpec] = {}


def register_node_by_spec(node_name: str, spec: NodeSpec) -> None:
    """Register a new node specification.

    Args:
        node_name (str): The name of the node to register
        spec (NodeSpec): The node specification to register

    Raises:
        ValueError: If a node with the same name is already registered
    """
    node_name = node_name.upper()
    if node_name in _NODE_REGISTRY:
        raise ValueError(f"Node with name '{node_name}' is already registered.")
    _NODE_REGISTRY[node_name] = spec


def create_node(node_name: str, **kwargs) -> _TreeNode:
    """Main factory function (enhanced version).

    Creates a Node object based on the registered name.
    This function automatically validates parameters for the node constructor.
    """
    node_name = node_name.upper()
    spec = _NODE_REGISTRY.get(node_name)
    if spec is None:
        raise ValueError(f"No specification found for node with name '{node_name}'.")

    # --- Step 1: Collect all possible parameters ---

    # a. Parameters from spec and kwargs
    possible_params = spec.params.copy()
    possible_params.update(kwargs)

    # b. Fixed parameters from spec
    possible_params["node_name"] = node_name
    possible_params["description"] = spec.description
    possible_params["return_type"] = spec.return_type
    if spec.args_type is not None:
        possible_params["args_type"] = spec.args_type

    # --- Step 2: Get the parameters that the constructor actually needs ---

    constructor_params = inspect.signature(spec.node_class.__init__).parameters
    # constructor_params is a dict: {'self': ..., 'node_name': ..., 'description': ...}

    valid_param_names = set(constructor_params.keys())

    # --- Step 3: Filter and keep only valid parameters ---

    final_params = {
        key: value for key, value in possible_params.items() if key in valid_param_names
    }

    # --- Step 4: Create the node object ---

    try:
        return spec.node_class(**final_params)
    except TypeError as e:
        # Provide a clearer error message if there's still an issue
        raise TypeError(
            f"Error initializing node '{node_name}' with class '{spec.node_class.__name__}'. "
            f"Final parameters: {final_params}. Original error: {e}"
        ) from e


def get_nodes_by_type(
    node_type: NodeType, purpose: SemanticType
) -> List[NodeSpecEntity]:
    """Get node specifications by type and purpose.

    Args:
        node_type (NodeType): The type of nodes to retrieve
        purpose (SemanticType): The semantic type of nodes to retrieve

    Returns:
        List[NodeSpecEntity]: List of node specifications matching the criteria
    """

    return [
        NodeSpecEntity(
            node_name=name,
            description=spec.description,
            node_type=spec.node_type,
            return_type=spec.return_type,
            args_type=spec.args_type,
        )
        for name, spec in _NODE_REGISTRY.items()
        if ((spec.node_type == node_type) or node_type == NodeType.ANY)
        and ((spec.return_type == purpose) or purpose == SemanticType.ANY)
    ]


def get_terminals_by_type() -> Dict[SemanticType, List[str]]:
    """Get terminal nodes (constants and variables) grouped by semantic type.

    Returns:
        Dict[SemanticType, List[str]]: Dictionary mapping semantic types to lists of node names
    """
    results: Dict[SemanticType, List[str]] = {}
    for name, spec in _NODE_REGISTRY.items():
        return_type = spec.return_type
        node_type = spec.node_type

        if node_type == NodeType.CONSTANT or node_type == NodeType.VARIABLE:
            results[return_type] = results.get(return_type, []) + [name]

    return results


def get_operators_by_type() -> Dict[SemanticType, List[str]]:
    """Get operator nodes grouped by semantic type.

    Returns:
        Dict[SemanticType, List[str]]: Dictionary mapping semantic types to lists of node names
    """
    results: Dict[SemanticType, List[str]] = {}
    for name, spec in _NODE_REGISTRY.items():
        return_type = spec.return_type
        node_type = spec.node_type

        if node_type == NodeType.OPERATOR:
            results[return_type] = results.get(return_type, []) + [name]

    return results


def get_spec_ent(name: str) -> NodeSpecEntity:
    """Get a node specification entity by name.

    Args:
        name (str): The name of the node to retrieve

    Returns:
        NodeSpecEntity: The node specification entity

    Raises:
        ValueError: If no specification is found for the node name
    """
    spec = _NODE_REGISTRY.get(name.upper())
    if spec is None:
        raise ValueError(f"No specification found for node with name '{name}'.")
    return NodeSpecEntity(
        node_name=name,
        description=spec.description,
        node_type=spec.node_type,
        return_type=spec.return_type,
        args_type=spec.args_type,
    )
