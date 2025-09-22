"""Crossover operators for evolutionary algorithms."""

import copy
import random
import uuid
from abc import abstractmethod
from typing import Any, Dict, Generic, List, Optional, Tuple, Type

import app.core.config as cfg
from app.state import SingletonNameable, Stateful
from itapia_common.rules.nodes import _TreeNode

from ..pop import IndividualType
from ..tree import get_effective_type, get_nodes_by_effective_type, replace_node


class CrossoverOperator(Stateful, SingletonNameable, Generic[IndividualType]):
    """Abstract base class for crossover operators in evolutionary algorithms.

    Provides a framework for recombining individuals to produce offspring.
    """

    def __init__(
        self, ind_cls: Type[IndividualType], new_rule_name_prefix: Optional[str] = None
    ):
        """Initialize the crossover operator.

        Args:
            ind_cls (Type[IndividualType]): Class of individuals to operate on
            new_rule_name_prefix (Optional[str], optional): Prefix for new rule names.
                Defaults to None, which generates a UUID.
        """
        # Use separate Random instance to ensure reproducibility
        self._random = random.Random(cfg.RANDOM_SEED)
        self.new_rule_name_prefix = (
            new_rule_name_prefix if new_rule_name_prefix else uuid.uuid4().hex
        )
        self.ind_cls = ind_cls

    @abstractmethod
    def __call__(
        self, ind1: IndividualType, ind2: IndividualType
    ) -> Tuple[IndividualType, IndividualType] | None:
        """Recombined two individuals and return exactly 2 offspring.

        Args:
            ind1 (Individual): Parent 1
            ind2 (Individual): Parent 2

        Returns:
            Tuple[Individual, Individual] | None: Two offspring, or None if crossover cannot be performed
        """

    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {"random_state": self._random.getstate()}

    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self._random.setstate(fallback_state["random_state"])


class SubtreeCrossoverOperator(CrossoverOperator[IndividualType]):
    """Subtree crossover operator that exchanges subtrees between individuals.

    Performs crossover by randomly selecting compatible nodes and swapping their subtrees.
    """

    def __call__(
        self, ind1: IndividualType, ind2: IndividualType
    ) -> Tuple[IndividualType, IndividualType] | None:
        """Perform subtree crossover between two individuals.

        Args:
            ind1 (IndividualType): First parent individual
            ind2 (IndividualType): Second parent individual

        Returns:
            Tuple[IndividualType, IndividualType] | None: Two offspring individuals,
                or None if crossover cannot be performed

        Raises:
            TypeError: If individuals are not of the expected type
        """
        # 1. Create deep copy to avoid modifying original parents
        if not (type(ind1) is self.ind_cls):
            raise TypeError("Individual must be same type as init.")
        if not (type(ind2) is self.ind_cls):
            raise TypeError("Individual must be same type as init.")

        offspring1_rule = copy.deepcopy(ind1.chromosome)
        offspring2_rule = copy.deepcopy(ind2.chromosome)

        # 2. Collect information about nodes that can be crossed over
        parent1_nodes_by_type = get_nodes_by_effective_type(offspring1_rule.root)
        parent2_nodes_by_type = get_nodes_by_effective_type(offspring2_rule.root)

        # 3. Find common types that both parents have
        common_types = set(parent1_nodes_by_type.keys()) & set(
            parent2_nodes_by_type.keys()
        )
        common_types.discard(offspring1_rule.root.return_type)

        if not common_types:
            # If no common points, crossover cannot be performed. Return None to signal.
            return None

        crossover_type = self._random.choice(list(common_types))

        point1 = self._random.choice(parent1_nodes_by_type[crossover_type])
        point2 = self._random.choice(parent2_nodes_by_type[crossover_type])

        # 5. Perform the exchange
        # To avoid complex issues, we'll create a copy of the crossover points
        # before performing the replacement.

        subtree1 = copy.deepcopy(point1)
        subtree2 = copy.deepcopy(point2)

        # Create Offspring 1: Parent 1's tree + Parent 2's subtree
        replace_node(offspring1_rule.root, point1, subtree2)

        # Create Offspring 2: Parent 2's tree + Parent 1's subtree
        replace_node(offspring2_rule.root, point2, subtree1)

        offspring1_rule.auto_id_name(self.new_rule_name_prefix)
        offspring2_rule.auto_id_name(self.new_rule_name_prefix)

        # 6. Create and return offspring Individual objects
        return self.ind_cls.from_rule(offspring1_rule), self.ind_cls.from_rule(
            offspring2_rule
        )


class OnePointCrossoverOperator(CrossoverOperator[IndividualType]):
    """One-point crossover operator that exchanges subtrees at structurally similar points.

    Finds structurally equivalent points in two individuals and performs crossover there.
    """

    def _find_common_points(
        self, node1: _TreeNode, node2: _TreeNode
    ) -> List[Tuple[_TreeNode, _TreeNode]]:
        """Recursive function to find all pairs of nodes at the same position with the same type.

        Args:
            node1 (_TreeNode): First node to compare
            node2 (_TreeNode): Second node to compare

        Returns:
            List[Tuple[_TreeNode, _TreeNode]]: List of node pairs at equivalent positions
        """
        common_points = []

        # Conditions for a pair to be "common":
        # - Same return type
        # - Both OperatorNodes OR both the same type of TerminalNode
        # - If Operators, must have the same number of children

        are_operators = hasattr(node1, "children") and hasattr(node2, "children")

        if get_effective_type(node1) == get_effective_type(node2):
            # Check if they have the same basic structure
            if are_operators and len(node1.children) == len(node2.children):
                common_points.append((node1, node2))
                # Recursively search in corresponding child pairs
                for child1, child2 in zip(node1.children, node2.children):
                    common_points.extend(self._find_common_points(child1, child2))
            elif not are_operators:
                # If both are leaf nodes and same type, they are a common point
                common_points.append((node1, node2))

        return common_points

    def __call__(
        self, ind1: IndividualType, ind2: IndividualType
    ) -> Tuple[IndividualType, IndividualType] | None:
        """Perform one-point crossover between two individuals.

        Args:
            ind1 (IndividualType): First parent individual
            ind2 (IndividualType): Second parent individual

        Returns:
            Tuple[IndividualType, IndividualType] | None: Two offspring individuals,
                or None if crossover cannot be performed

        Raises:
            TypeError: If individuals are not of the expected type
        """
        if not (type(ind1) is self.ind_cls):
            raise TypeError("Individual must be same type as init.")
        if not (type(ind2) is self.ind_cls):
            raise TypeError("Individual must be same type as init.")

        offspring1_rule = copy.deepcopy(ind1.chromosome)
        offspring2_rule = copy.deepcopy(ind2.chromosome)

        # 1. Find all common crossover points
        common_points = self._find_common_points(
            offspring1_rule.root, offspring2_rule.root
        )

        if not common_points:
            # If no common points, return None
            return None

        # 2. Randomly select a common point pair to exchange
        point1, point2 = self._random.choice(common_points)

        # 3. Perform the exchange
        subtree1 = copy.deepcopy(point1)
        subtree2 = copy.deepcopy(point2)

        replace_node(offspring1_rule.root, point1, subtree2)
        replace_node(offspring2_rule.root, point2, subtree1)

        offspring1_rule.auto_id_name(self.new_rule_name_prefix)
        offspring2_rule.auto_id_name(self.new_rule_name_prefix)

        # 6. Create and return offspring Individual objects
        return self.ind_cls.from_rule(offspring1_rule), self.ind_cls.from_rule(
            offspring2_rule
        )
