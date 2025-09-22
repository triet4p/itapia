"""Decomposition techniques for multi-objective evolutionary algorithms."""

import math
from typing import Any, Dict, List

import numpy as np
from app.state import Stateful

from .pop import MOEADIndividual


class DecompositionManager(Stateful):
    """Manages decomposition techniques for MOEA/D algorithm.

    Generates weight vectors and calculates neighborhoods for multi-objective optimization.
    """

    def __init__(self, num_objs: int, num_divisions: int, neighborhood_size: int):
        """Initialize the decomposition manager.

        Args:
            num_objs (int): Number of objectives in the optimization problem
            num_divisions (int): Number of divisions for weight vector generation
            neighborhood_size (int): Size of neighborhood for each weight vector

        Raises:
            ValueError: If any parameter is invalid
        """
        if num_objs < 2:
            raise ValueError("Number of objectives must be at least 2.")
        if num_divisions < 1:
            raise ValueError("Number of divisions must be at least 1.")
        if neighborhood_size < 1:
            raise ValueError("Neighborhood size must be at least 1.")

        self.num_objs = num_objs
        self.num_divisions = num_divisions
        self.neighborhood_size = neighborhood_size

        self.problem_weight_vectors: np.ndarray = None
        self.neighborhoods: np.ndarray = None
        self.problem_weight_vectors

    @property
    def num_vectors(self) -> int:
        """Get the number of weight vectors.

        Returns:
            int: Number of weight vectors

        Raises:
            ValueError: If weight vectors have not been generated yet
        """
        if self.problem_weight_vectors is None:
            raise ValueError(
                "Weight vectors must be generated before calculating neighborhoods."
            )
        return len(self.problem_weight_vectors)

    def generate_weight_vectors(self) -> "DecompositionManager":
        """Generate weight vectors using systematic division method.

        Returns:
            DecompositionManager: Self for method chaining
        """
        weights = []

        def _recursive_generator(idx: int, curr_sum: int, vector: List[int]):
            """Recursively generate weight vectors."""
            if idx == self.num_objs - 1:
                vector[idx] = self.num_divisions - curr_sum
                weights.append(list(vector))
                return

            for i in range(self.num_divisions - curr_sum + 1):
                vector[idx] = i
                _recursive_generator(idx + 1, curr_sum + i, vector)

        _recursive_generator(0, 0, [0] * self.num_objs)

        self.problem_weight_vectors = np.array(weights) / self.num_divisions

        num_generated = len(self.problem_weight_vectors)
        expected_num = int(
            math.comb(self.num_divisions + self.num_objs - 1, self.num_objs - 1)
        )

        assert (
            num_generated == expected_num
        ), f"Generated {num_generated} vectors, but expected {expected_num}."

        return self

    def calculate_neighborhoods(self) -> "DecompositionManager":
        """Calculate neighborhoods for each weight vector.

        Returns:
            DecompositionManager: Self for method chaining
        """
        num_vectors = self.num_vectors
        T = self.neighborhood_size

        if T >= num_vectors:
            # If T is greater than or equal to total vectors, "neighbors" of each vector are all other vectors.
            # This is a boundary case, usually doesn't occur.
            self.neighborhoods = np.array(
                [
                    np.roll(np.arange(num_vectors), -i - 1)[: num_vectors - 1]
                    for i in range(num_vectors)
                ]
            )
            return self

        # 1. Calculate distance matrix
        # Use numpy broadcasting to efficiently compute Euclidean distances between all pairs
        # without explicit for loops.
        diff = (
            self.problem_weight_vectors[:, np.newaxis, :]
            - self.problem_weight_vectors[np.newaxis, :, :]
        )
        dist_matrix = np.sqrt((diff**2).sum(axis=2))

        # 2. Sort and get indices
        # np.argsort returns indices of sorted elements,
        # not the values themselves.
        # axis=1 to sort by rows.
        sorted_indices = np.argsort(dist_matrix, axis=1)

        # 3. Get T nearest neighbors
        # Result of argsort includes the vector itself (at position 0, distance = 0),
        # so we take indices from 1 to T+1.
        self.neighborhoods = sorted_indices[:, 1 : T + 1]

        return self

    def scalar_tchebycheff(
        self, ind: MOEADIndividual, neighbor_idx: int, reference_point: np.ndarray
    ) -> float:
        """Calculate scalarized Tchebycheff decomposition value.

        Args:
            ind (MOEADIndividual): Individual to evaluate
            neighbor_idx (int): Index of the neighbor (weight vector) to use
            reference_point (np.ndarray): Reference point for decomposition

        Returns:
            float: Scalarized Tchebycheff value
        """
        # Can use ind.problem_idx to find problem of this ind.
        fitness_arr = np.array(ind.fitness)

        # 1. Calculate difference from reference point
        # Assuming objectives are to maximize, so we want fitness > reference_point
        # We can calculate |fitness - reference| or (reference - fitness)
        # Common approach is to calculate (reference - fitness), because if fitness is better
        # than reference, result will be negative, not affecting the max operation.
        diff = reference_point - fitness_arr

        weight_vector = self.problem_weight_vectors[neighbor_idx]

        # 2. Multiply by weights
        # This "stretches" or "compresses" the distance in each dimension
        weighted_diff = weight_vector * diff

        # 3. Take maximum value
        # This is the "worst" component after adjustment by weights.
        return np.max(weighted_diff)

    @property
    def fallback_state(self) -> Dict[str, Any]:
        """Get fallback state for serialization.

        Returns:
            Dict[str, Any]: Dictionary containing weight vectors and neighborhoods
        """
        return {
            "problem_weight_vectors": self.problem_weight_vectors.tolist(),
            "neighborhoods": self.neighborhoods.tolist(),
        }

    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        """Restore state from fallback state.

        Args:
            fallback_state (Dict[str, Any]): Fallback state dictionary to restore from
        """
        self.problem_weight_vectors = np.array(fallback_state["problem_weight_vectors"])
        self.neighborhoods = np.array(fallback_state["neighborhoods"])
