# algorithms/structures/tree_utils.py

import copy
import random
from typing import List, Set, Tuple, Dict

from itapia_common.rules.nodes import _TreeNode
from itapia_common.rules.nodes.registry import create_node, get_spec_ent
from itapia_common.schemas.entities.rules import SemanticType
import app.core.config as cfg


def get_all_nodes(root: _TreeNode) -> List[_TreeNode]:
    """Traverse tree in pre-order and return a flat list containing all nodes in the tree.
    
    Args:
        root (_TreeNode): Root node of the tree
        
    Returns:
        List[_TreeNode]: Flat list of all nodes in the tree
    """
    nodes = [root]
    if hasattr(root, 'children') and root.children:
        for child in root.children:
            nodes.extend(get_all_nodes(child))
    return nodes

def get_effective_type(node: _TreeNode) -> SemanticType:
    """Determine the effective (concrete) data type that a node or tree branch will return.
    
    This is a recursive function to handle polymorphic types like ANY and ANY_NUMERIC.
    
    Args:
        node (_TreeNode): Node to determine effective type for
        
    Returns:
        SemanticType: Effective semantic type of the node
    """
    # 1. Base case: If declared type is already concrete, return it
    declared_type = node.return_type
    if declared_type not in {SemanticType.ANY, SemanticType.ANY_NUMERIC}:
        return declared_type

    # 2. Recursive case: Declared type is polymorphic
    if not hasattr(node, 'children') or not node.children:
        # Polymorphic node has no children (shouldn't happen in valid tree)
        # Return declared type as a safe solution
        return declared_type
    
    index_to_check = -1
    for idx, arg_type in enumerate(node.args_type):
        if arg_type in {SemanticType.ANY, SemanticType.ANY_NUMERIC}:
            index_to_check = idx
            break

    # For polymorphic operators, effective type is determined by effective type
    # of its child branches. We can generalize by taking the effective type
    # of the first child (because children must have the same effective type)
    return get_effective_type(node.children[index_to_check])

def get_nodes_by_effective_type(root: _TreeNode) -> Dict[SemanticType, List[_TreeNode]]:
    """Traverse tree and return a dictionary grouping all nodes by their EFFECTIVE type.
    
    This function is used by Crossover to ensure semantic safety.
    
    Args:
        root (_TreeNode): Root node of the tree
        
    Returns:
        Dict[SemanticType, List[_TreeNode]]: Dictionary mapping semantic types to lists of nodes
    """
    nodes_by_type = {}
    all_nodes = get_all_nodes(root)
    for node in all_nodes:
        effective_type = get_effective_type(node)
        # Only group concrete types, ignore abstract types
        if effective_type not in {SemanticType.ANY, SemanticType.ANY_NUMERIC}:
            nodes_by_type.setdefault(effective_type, []).append(node)
    return nodes_by_type
    
def replace_node(root: _TreeNode, old_node: _TreeNode, new_node: _TreeNode) -> _TreeNode:
    """Find and replace a node (`old_node`) with a new node (`new_node`) in the tree.
    
    Returns the root of the new tree. This operation modifies the original tree.
    
    Args:
        root (_TreeNode): Root node of the tree
        old_node (_TreeNode): Node to be replaced
        new_node (_TreeNode): New node to replace with
        
    Returns:
        _TreeNode: Root of the modified tree
    """
    if root is old_node:
        return new_node
    
    if hasattr(root, 'children') and root.children:
        for i, child in enumerate(root.children):
            if child is old_node:
                # Create a new list of children with the node replaced
                root.children = root.children[:i] + [new_node] + root.children[i+1:]
                return root # Return root after modification
            else:
                # Recursively search in child trees
                replace_node(child, old_node, new_node)
    return root

def get_concreate_type(required_type: SemanticType,
                       random_ins: random.Random,
                       available_types: Set[SemanticType]) -> SemanticType:
    """Get a concrete type that is compatible with the required type.
    
    Args:
        required_type (SemanticType): Required semantic type
        random_ins (random.Random): Random number generator instance
        available_types (Set[SemanticType]): Set of available semantic types
        
    Returns:
        SemanticType: Compatible concrete semantic type
        
    Raises:
        TypeError: If no safe concrete types exist
    """
    # Use precomputed lists
    if not required_type.concreates:
        return required_type
    
    safe_concreate_types = tuple(
        t for t in required_type.concreates
        if t in available_types
    )
    
    if not safe_concreate_types:
        raise TypeError('Not exist any safe concreate types.')
    
    return random_ins.choice(safe_concreate_types)

def grow_tree(current_depth: int, 
              max_depth: int,
              operators_by_type: Dict[SemanticType, List[str]],
              terminals_by_type: Dict[SemanticType, List[str]],
              required_type: SemanticType,
              random_ins: random.Random,
              ) -> _TreeNode:
    """Core recursive function to randomly build a tree.
    
    Args:
        current_depth (int): Current depth in the tree
        max_depth (int): Maximum allowed depth
        operators_by_type (Dict[SemanticType, List[str]]): Mapping of semantic types to operator names
        terminals_by_type (Dict[SemanticType, List[str]]): Mapping of semantic types to terminal names
        required_type (SemanticType): Required semantic type for this node
        random_ins (random.Random): Random number generator instance
        
    Returns:
        _TreeNode: Newly created tree node
    """
    is_max_depth = current_depth >= max_depth
    specific_operators = operators_by_type.get(required_type, [])
    any_return_operators = operators_by_type.get(SemanticType.ANY, []) if current_depth > 1 else []
    any_numeric_return_operators = operators_by_type.get(SemanticType.ANY_NUMERIC, []) if current_depth > 1 else []

    possible_operators = specific_operators + any_return_operators + any_numeric_return_operators
    
    has_operators = len(possible_operators) > 0
    
    available_types = set(terminals_by_type.keys())
    
    # Decide whether to create a terminal
    # Must create terminal if: at max depth OR no suitable operators available
    # Otherwise, there's a probability `INIT_TERMINAL_PROB` to create terminal
    if is_max_depth or not has_operators or (current_depth > 1 and random_ins.random() < cfg.INIT_TERMINAL_PROB):
        # --- Create a Terminal Node (leaf node) ---
        concreate_type = get_concreate_type(required_type, random_ins, available_types)
        possible_terminals = terminals_by_type.get(concreate_type)
    
        if not possible_terminals:
            raise ValueError(f"Could not find a terminal for required type '{required_type}' at depth {current_depth}.")
        
        terminal_name = random_ins.choice(possible_terminals)
        return create_node(terminal_name)
    else:
        # --- Create an Operator Node (internal node) ---
        op_name = random_ins.choice(possible_operators)
        op_spec = get_spec_ent(op_name)
        
        # Handle parameters
        args_types = list(op_spec.args_type)
        resolved_types: Dict[SemanticType, SemanticType] = {}
        
        for arg_type in set(args_types):
            if arg_type.concreates:
                if op_spec.return_type == arg_type:
                    resolved_types[arg_type] = required_type
                else:
                    resolved_types[arg_type] = get_concreate_type(arg_type, random_ins, available_types)
            
        final_args_type = [resolved_types.get(t, t) for t in args_types]
        
        children = [
            grow_tree(current_depth=current_depth + 1, 
                      max_depth=max_depth,
                      operators_by_type=operators_by_type,
                      terminals_by_type=terminals_by_type,
                      required_type=child_type,
                      random_ins=random_ins)
            for child_type in final_args_type
        ]
        
        return create_node(op_name, children=children)