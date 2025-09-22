# algorithms/structures/operators/selection.py

import random
from abc import abstractmethod
from typing import Any, Callable, Dict, Generic, List, Type

import app.core.config as cfg
from app.state import SingletonNameable, Stateful

from ..comparator import Comparator  # Utility function import
from ..objective import AcceptedObjective
from ..pop import IndividualType


class SelectionOperator(Stateful, SingletonNameable, Generic[IndividualType]):
    """Abstract base class for selection operators in evolutionary algorithms."""

    def __init__(self, ind_cls: Type[IndividualType]):
        """Initialize the selection operator.

        Args:
            ind_cls (Type[IndividualType]): The individual class type
        """
        self._random = random.Random(cfg.RANDOM_SEED)
        self.ind_cls = ind_cls

    @abstractmethod
    def __call__(
        self, population: List[IndividualType], num_selections: int
    ) -> List[IndividualType]:
        """Select a number of individuals from the population to be parents.

        Args:
            population (List[IndividualType]): Current population
            num_selections (int): Number of parents to select

        Returns:
            List[IndividualType]: List of selected parents
        """

    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {"random_state": self._random.getstate()}

    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self._random.setstate(fallback_state["random_state"])


class TournamentSelectionOperator(SelectionOperator[IndividualType]):
    """Tournament selection based on dominance and crowding distance.

    This is the standard selection method for NSGA-II.
    """

    def __init__(
        self, ind_cls: Type[IndividualType], comparator: Comparator, k: int = 4
    ):
        """Initialize the tournament selection operator.

        Args:
            ind_cls (Type[IndividualType]): The individual class type
            comparator (Comparator): Function to compare individuals
            k (int): Tournament size (number of contenders)

        Raises:
            ValueError: If tournament size is less than 2
        """
        super().__init__(ind_cls)
        if k < 2:
            raise ValueError("Tournament size (k) must be at least 2.")
        self.k = k
        self.comparator = comparator

    def __call__(
        self, population: List[IndividualType], num_selections: int
    ) -> List[IndividualType]:
        """Perform tournament selection on a population.

        Args:
            population (List[IndividualType]): Current population
            num_selections (int): Number of parents to select

        Returns:
            List[IndividualType]: List of selected parents
        """
        selected_parents: List[IndividualType] = []
        pop_size = len(population)

        if pop_size == 0:
            return []

        for _ in range(num_selections):
            # 1. Randomly select k "contestants" from the population
            tournament_contenders = self._random.sample(population, self.k)

            # 2. Find the winner
            winner = tournament_contenders[0]
            for i in range(1, self.k):
                if self.comparator(tournament_contenders[i], winner):
                    winner = tournament_contenders[i]

            selected_parents.append(winner)

        return selected_parents


class RouletteWheelSelectionOperator(SelectionOperator[IndividualType]):
    """Roulette wheel selection operator.

    Note: This method is typically not suitable for multi-objective optimization
    as it requires a single scalar fitness value.
    """

    def __init__(
        self,
        ind_cls: Type[IndividualType],
        fitness_score_mapper: Callable[[AcceptedObjective], float],
    ):
        """Initialize the roulette wheel selection operator.

        Args:
            ind_cls (Type[IndividualType]): The individual class type
            fitness_score_mapper (Callable[[AcceptedObjective], float]): Function to map fitness to scalar score
        """
        super().__init__(ind_cls)
        self.fitness_score_mapper = fitness_score_mapper

    def __call__(
        self, population: List[IndividualType], num_selections: int
    ) -> List[IndividualType]:
        """Perform roulette wheel selection on a population.

        Args:
            population (List[IndividualType]): Current population
            num_selections (int): Number of parents to select

        Returns:
            List[IndividualType]: List of selected parents
        """
        # For Roulette Wheel to work, we need to convert multi-objective rank
        # into a single "score" value.
        # A common approach is to use rank as the primary score.

        # Assign "score" based on rank, lower rank gets higher score.
        # Example: rank 0 -> score N, rank 1 -> score N-1, ...
        scores = [self.fitness_score_mapper(ind.fitness) for ind in population]
        total_score = sum(scores)

        if total_score == 0:
            # If all have score 0, select randomly
            return self._random.sample(population, k=num_selections)

        selected_parents = []
        for _ in range(num_selections):
            pick = self._random.uniform(0, total_score)
            current = 0
            for ind, score in zip(population, scores):
                current += score
                if current > pick:
                    selected_parents.append(ind)
                    break

        return selected_parents
