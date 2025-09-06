"""Replacement operators for evolutionary algorithms."""

import random
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Protocol, Tuple, Type

from app.state import SingletonNameable, Stateful

from ..pop import DominanceIndividual, Individual, IndividualType
from ..comparator import Comparator, DominateComparator
from ..dominance import non_dominated_sorting, crowding_distance_assignment
import app.core.config as cfg


class ReplacementOperator(Stateful, SingletonNameable, Generic[IndividualType]):
    """Abstract base class for replacement operators in evolutionary algorithms.
    
    Provides a framework for selecting individuals from parent and offspring populations 
    to create the next generation.
    """
    
    def __init__(self, ind_cls: Type[IndividualType]):
        """Initialize the replacement operator.
        
        Args:
            ind_cls (Type[IndividualType]): Class of individuals to operate on
        """
        self._random = random.Random(cfg.RANDOM_SEED)
        self.ind_cls = ind_cls

    @abstractmethod
    def __call__(self, 
                 population: List[IndividualType], 
                 offspring_population: List[IndividualType],
                 target_size: int) -> List[IndividualType]:
        """Select individuals from parents and offspring to create the next generation.
        
        Args:
            population (List[Individual]): Parent population.
            offspring_population (List[Individual]): Offspring population.
            target_size (int): Target size of the new population.
            
        Returns:
            List[Individual]: Next generation population.
        """
        pass
    
    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {
            'random_state': self._random.getstate()
        }
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self._random.setstate(fallback_state['random_state'])


class NSGA2ReplacementOperator(ReplacementOperator[DominanceIndividual]):
    """Performs full survival selection using the NSGA-II algorithm.
    
    This is the recommended method for multi-objective evolutionary algorithms.
    """
    
    def __init__(self, comparator: DominateComparator):
        """Initialize NSGA-II replacement operator.
        
        Args:
            comparator (DominateComparator): Comparator to determine dominance relationships
        """
        super().__init__(ind_cls=DominanceIndividual)
        self.comparator = comparator
    
    def __call__(self, 
                 population: List[DominanceIndividual], 
                 offspring_population: List[DominanceIndividual],
                 target_size: int) -> List[DominanceIndividual]:
        """Perform NSGA-II replacement selection.
        
        Args:
            population (List[DominanceIndividual]): Parent population
            offspring_population (List[DominanceIndividual]): Offspring population
            target_size (int): Target size of the new population
            
        Returns:
            List[DominanceIndividual]: Next generation population according to NSGA-II
        """
        
        # 1. Merge parent and offspring populations
        combined_population = population + offspring_population

        # 2. Classify the entire merged population
        fronts = non_dominated_sorting(combined_population, dominate_comparator=self.comparator)

        # 3. Build next generation
        next_generation: List[DominanceIndividual] = []
        for front in fronts:
            # If adding this entire front still isn't enough...
            if len(next_generation) + len(front) <= target_size:
                next_generation.extend(front)
            else:
                # This is the last partially added front
                # Calculate crowding distance ONLY for this front
                crowding_distance_assignment(front)
                
                # Sort this front by crowding distance in descending order
                front.sort(key=lambda ind: ind.crowding_distance, reverse=True)
                
                # Take the number of individuals needed to fill the target
                num_needed = target_size - len(next_generation)
                next_generation.extend(front[:num_needed])
                break # Enough, exit loop
        
        return next_generation