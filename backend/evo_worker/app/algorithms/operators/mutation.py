import random
import uuid
from abc import abstractmethod
from copy import deepcopy
from typing import Any, Dict, Generic, List, Optional, Type

import app.core.config as cfg
from app.state import SingletonNameable, Stateful
from itapia_common.rules.nodes import OperatorNode, _TreeNode
from itapia_common.rules.nodes.registry import create_node, get_spec_ent
from itapia_common.schemas.entities.rules import SemanticType

from ..pop import IndividualType
from ..tree import get_all_nodes, get_effective_type, grow_tree, replace_node


class MutationOperator(Stateful, SingletonNameable, Generic[IndividualType]):
    """Abstract base class for mutation operators in evolutionary algorithms."""

    def __init__(
        self, ind_cls: Type[IndividualType], new_rule_name_prefix: Optional[str] = None
    ):
        """Initialize the mutation operator.

        Args:
            ind_cls (Type[IndividualType]): The individual class type
            new_rule_name_prefix (Optional[str]): Prefix for naming new rules
        """
        self._random = random.Random(cfg.RANDOM_SEED)
        self.new_rule_name_prefix = (
            new_rule_name_prefix if new_rule_name_prefix else uuid.uuid4().hex
        )
        self.ind_cls = ind_cls

    @abstractmethod
    def __call__(self, ind: IndividualType) -> IndividualType | None:
        """Mutate an individual to create exactly one new individual.

        Args:
            ind (IndividualType): Individual to mutate

        Returns:
            IndividualType | None: Mutated individual or None if mutation failed
        """

    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {"random_state": self._random.getstate()}

    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self._random.setstate(fallback_state["random_state"])


class SubtreeMutationOperator(MutationOperator[IndividualType]):
    """Mutation operator that replaces a subtree with a randomly generated one."""

    def __init__(
        self,
        ind_cls: Type[IndividualType],
        max_subtree_depth: int,
        terminals_by_type: Dict[SemanticType, List[str]],
        operators_by_type: Dict[SemanticType, List[str]],
        new_rule_name_prefix: Optional[str] = None,
    ):
        """Initialize the subtree mutation operator.

        Args:
            ind_cls (Type[IndividualType]): The individual class type
            max_subtree_depth (int): Maximum depth for generated subtrees
            terminals_by_type (Dict[SemanticType, List[str]]): Mapping of semantic types to terminal node names
            operators_by_type (Dict[SemanticType, List[str]]): Mapping of semantic types to operator node names
            new_rule_name_prefix (Optional[str]): Prefix for naming new rules
        """
        super().__init__(ind_cls, new_rule_name_prefix)
        self.terminals_by_type = terminals_by_type
        self.operators_by_type = operators_by_type
        self.max_subtree_depth = max_subtree_depth
        # Use types that can replace ANY,
        # because we must mutate at nodes that don't return final purpose (decision signal,...)
        # but an intermediate purpose

    def __call__(self, ind: IndividualType) -> IndividualType | None:
        """Perform subtree mutation on an individual.

        Args:
            ind (IndividualType): Individual to mutate

        Returns:
            IndividualType | None: Mutated individual or None if mutation failed

        Raises:
            TypeError: If individual type doesn't match the initialized type
        """
        if not (type(ind) is self.ind_cls):
            raise TypeError("Individual must be same type as init.")

        mutated_rule = deepcopy(ind.chromosome)

        # 1. Choose a random mutation point in the tree (not the root)
        all_nodes = get_all_nodes(mutated_rule.root)
        if len(all_nodes) <= 1:
            # If tree has only 1 node, cannot mutate, return None
            return None

        mutation_point = self._random.choice(all_nodes[1:])

        # 2. Determine the required effective type at that point
        required_type = get_effective_type(mutation_point)

        new_subtree = grow_tree(
            current_depth=1,
            max_depth=self.max_subtree_depth,
            operators_by_type=self.operators_by_type,
            terminals_by_type=self.terminals_by_type,
            required_type=required_type,
            random_ins=self._random,
        )

        replace_node(mutated_rule.root, mutation_point, new_subtree)

        mutated_rule.auto_id_name(self.new_rule_name_prefix)
        return self.ind_cls.from_rule(mutated_rule)


class PointMutationOperator(MutationOperator[IndividualType]):
    """Mutation operator that changes a single node in the tree."""

    def __init__(
        self,
        ind_cls: Type[IndividualType],
        terminals_by_type: Dict[SemanticType, List[str]],
        operators_by_type: Dict[SemanticType, List[str]],
        new_rule_name_prefix: Optional[str] = None,
    ):
        """Initialize the point mutation operator.

        Args:
            ind_cls (Type[IndividualType]): The individual class type
            terminals_by_type (Dict[SemanticType, List[str]]): Mapping of semantic types to terminal node names
            operators_by_type (Dict[SemanticType, List[str]]): Mapping of semantic types to operator node names
            new_rule_name_prefix (Optional[str]): Prefix for naming new rules
        """
        super().__init__(ind_cls, new_rule_name_prefix)
        self.terminals_by_type = terminals_by_type
        self.operators_by_type = operators_by_type

    def __call__(self, ind: IndividualType) -> IndividualType | None:
        """Perform point mutation on an individual.

        Args:
            ind (IndividualType): Individual to mutate

        Returns:
            IndividualType | None: Mutated individual or None if mutation failed

        Raises:
            TypeError: If individual type doesn't match the initialized type
        """
        if not (type(ind) is self.ind_cls):
            raise TypeError("Individual must be same type as init.")

        mutated_rule = deepcopy(ind.chromosome)
        all_nodes = get_all_nodes(mutated_rule.root)

        if not all_nodes:
            return None

        mutation_point = self._random.choice(all_nodes[1:])

        if isinstance(mutation_point, OperatorNode) and mutation_point.children:
            new_node = self._mutate_operator(mutation_point)
        else:
            new_node = self._mutate_terminal(mutation_point)

        if new_node is None:
            return None

        replace_node(mutated_rule.root, mutation_point, new_node)

        mutated_rule.auto_id_name(self.new_rule_name_prefix)
        return self.ind_cls.from_rule(mutated_rule)

    def _mutate_operator(self, node: OperatorNode) -> _TreeNode | None:
        """Replace an operator with another compatible operator.

        Args:
            node (OperatorNode): The operator node to mutate

        Returns:
            _TreeNode | None: New operator node or None if no compatible replacement found
        """
        # Find other operators with the same return type and same number of parameters
        possible_replacements: List[str] = []
        for op_name in self.operators_by_type.get(node.return_type, []):
            spec = get_spec_ent(op_name)
            if len(spec.args_type) == node.num_child and op_name != node.node_name:
                possible_replacements.append(op_name)

        if possible_replacements:
            new_op_name = self._random.choice(possible_replacements)
            # Must create new node, children are passed through
            return create_node(new_op_name, children=node.children)

        return None

    def _mutate_terminal(self, node: _TreeNode) -> _TreeNode | None:
        """Replace a terminal with another terminal of the same type.

        Args:
            node (_TreeNode): The terminal node to mutate

        Returns:
            _TreeNode | None: New terminal node or None if no compatible replacement found
        """
        # Find other terminals with the same return type
        possible_replacements = [
            term_name
            for term_name in self.terminals_by_type.get(node.return_type, [])
            if term_name != node.node_name
        ]

        if possible_replacements:
            new_term_name = self._random.choice(possible_replacements)
            # Change the name and value of the node
            # This is a simplification. A complete system would need
            # a `reinitialize_node(node, new_name)` function to update all
            # properties (value, description, ...) from the new spec.
            return create_node(node_name=new_term_name)
        return None


class ShrinkMutationOperator(MutationOperator[IndividualType]):
    """Mutation operator that replaces a subtree with a terminal node."""

    def __init__(
        self,
        ind_cls: Type[IndividualType],
        terminals_by_type: Dict[SemanticType, List[str]],
        new_rule_name_prefix: Optional[str] = None,
    ):
        """Initialize the shrink mutation operator.

        Args:
            ind_cls (Type[IndividualType]): The individual class type
            terminals_by_type (Dict[SemanticType, List[str]]): Mapping of semantic types to terminal node names
            new_rule_name_prefix (Optional[str]): Prefix for naming new rules
        """
        super().__init__(ind_cls, new_rule_name_prefix)
        self.terminals_by_type = terminals_by_type

    def __call__(self, ind: IndividualType) -> IndividualType | None:
        """Perform shrink mutation on an individual.

        Args:
            ind (IndividualType): Individual to mutate

        Returns:
            IndividualType | None: Mutated individual or None if mutation failed

        Raises:
            TypeError: If individual type doesn't match the initialized type
        """
        if not (type(ind) is self.ind_cls):
            raise TypeError("Individual must be same type as init.")

        mutated_rule = deepcopy(ind.chromosome)
        all_nodes = get_all_nodes(mutated_rule.root)

        # Can only "shrink" non-leaf nodes
        shrinkable_nodes = [
            n for n in all_nodes[1:] if isinstance(n, OperatorNode) and n.children
        ]

        if not shrinkable_nodes:
            return None

        mutation_point = self._random.choice(shrinkable_nodes)
        required_type = get_effective_type(mutation_point)

        # Find a suitable terminal to replace with
        possible_terminals = self.terminals_by_type.get(required_type)
        if not possible_terminals:
            # If no replacement terminal found, do nothing
            return None

        new_terminal_name = self._random.choice(possible_terminals)

        new_terminal_node = create_node(new_terminal_name)

        # Replace the entire subtree at the mutation point with the new terminal node
        replace_node(mutated_rule.root, mutation_point, new_terminal_node)

        mutated_rule.auto_id_name(self.new_rule_name_prefix)
        return self.ind_cls.from_rule(mutated_rule)
