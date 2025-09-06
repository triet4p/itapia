"""Comparison utilities for evolutionary algorithms."""

import math
from typing import List, Dict, Tuple
from abc import ABC, abstractmethod
from .pop import DominanceIndividual, Individual


class Comparator(ABC):
    """Abstract base class for comparing individuals in evolutionary algorithms."""
    
    @abstractmethod
    def __call__(self, ind1: Individual, ind2: Individual) -> bool: 
        """ 
        Return `True` if ind1 is "better" than ind2.
        
        Args:
            ind1 (Individual): First individual to compare
            ind2 (Individual): Second individual to compare
            
        Returns:
            bool: True if ind1 is better than ind2
        """
        pass


class DominateComparator(Comparator):
    """Abstract base class for dominance comparison in multi-objective optimization."""
    
    @abstractmethod
    def __call__(self, ind1: DominanceIndividual, ind2: DominanceIndividual) -> bool: 
        """ 
        Return `True` if ind1 "dominates" ind2.
        
        Args:
            ind1 (DominanceIndividual): First individual to compare
            ind2 (DominanceIndividual): Second individual to compare
            
        Returns:
            bool: True if ind1 dominates ind2
        """
        pass
    

class FixedDominateComparator(DominateComparator):
    """Fixed dominance comparator implementing standard Pareto dominance."""
    
    def __call__(self, ind1: DominanceIndividual, ind2: DominanceIndividual) -> bool:
        """
        Check if individual 1 (ind1) dominates individual 2 (ind2).
        
        An individual `p` dominates `q` if:
        1. `p` is not worse than `q` in any objective.
        2. `p` is better than `q` in at least one objective.
        
        Args:
            ind1 (Individual): Individual p.
            ind2 (Individual): Individual q.
            
        Returns:
            bool: True if ind1 dominates ind2, otherwise False.
        """
        if not isinstance(ind1.fitness, tuple):
            return ind1.fitness > ind2.fitness
        is_better_in_one = False
        for f1, f2 in zip(ind1.fitness, ind2.fitness):
            if f1 < f2:
                return False
            if f1 > f2:
                is_better_in_one = True
                
        return is_better_in_one
    

class RankAndCrowdingComparator(DominateComparator):
    """Compare individuals based on rank and crowding distance."""
    
    def __call__(self, ind1: DominanceIndividual, ind2: DominanceIndividual) -> bool:
        """Compare two individuals based on rank and crowding distance.
        
        Args:
            ind1 (DominanceIndividual): First individual to compare
            ind2 (DominanceIndividual): Second individual to compare
            
        Returns:
            bool: True if ind1 is better than ind2 based on rank/crowding criteria
            
        Raises:
            ValueError: If individuals are not ranked
        """
        if ind1.rank < 0 or ind2.rank < 0:
            raise ValueError("Individuals must be ranked!")
        if ind1.rank > ind2.rank:
            return True
        if ind1.rank < ind2.rank:
            return False
        return ind1.crowding_distance > ind2.crowding_distance
    

class EpsilonBoxDominateComparator(DominateComparator):
    """
    Compare two individuals based on Epsilon-Box Dominance concept.
    
    Quantizes the objective space into a grid of "boxes" and compares
    the positions of individuals on that grid.
    """
    
    def __init__(self, epsilons: Tuple[float, ...]):
        """
        Initialize comparator with an epsilon vector.
        
        Args:
            epsilons (Tuple[float, ...]): A tuple of epsilon values,
                                         one for each corresponding objective.
                                         Length must equal number of objectives.
                                         
        Raises:
            ValueError: If any epsilon value is not positive
        """
        if not all(e > 0 for e in epsilons):
            raise ValueError("All epsilon values must be positive.")
        self.epsilons = epsilons

    def __call__(self, ind1: DominanceIndividual, ind2: DominanceIndividual) -> bool:
        """ 
        Return True if ind1 ε-dominates ind2.
        
        Args:
            ind1 (DominanceIndividual): First individual to compare
            ind2 (DominanceIndividual): Second individual to compare
            
        Returns:
            bool: True if ind1 ε-dominates ind2
        """
        if not isinstance(ind1.fitness, tuple):
            # If single objective, epsilon has little meaning,
            # fall back to standard comparison.
            return ind1.fitness > ind2.fitness

        if len(ind1.fitness) != len(self.epsilons):
            raise ValueError(
                f"Mismatch between number of objectives ({len(ind1.fitness)}) "
                f"and number of epsilons ({len(self.epsilons)})."
            )

        # Convert each individual's fitness to "box coordinates"
        box1 = [math.floor(f / e) for f, e in zip(ind1.fitness, self.epsilons)]
        box2 = [math.floor(f / e) for f, e in zip(ind2.fitness, self.epsilons)]
        
        # Apply standard Pareto dominance on "box coordinates"
        is_better_in_one = False
        for b1, b2 in zip(box1, box2):
            if b1 < b2: # Box coordinate of ind1 is lower -> cannot dominate
                return False
            if b1 > b2: # Box coordinate of ind1 is higher
                is_better_in_one = True
                
        return is_better_in_one