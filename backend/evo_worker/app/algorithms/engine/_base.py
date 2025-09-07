"""Base evolutionary algorithm engine for coordinating optimization processes."""

from app.state import SingletonNameable, Stateful
from itapia_common.schemas.entities.evo import EvoRuleEntity, EvoRunEntity, EvoRunStatus
from ..pop import Individual, IndividualType, Population
from ..operators.construct import InitOperator
from ..objective import ObjectiveExtractor
from app.backtest.evaluator import Evaluator

import app.core.config as cfg

from typing import Any, Dict, List, Optional, Self, Type
import random

from itapia_common.rules.rule import Rule

from abc import ABC, abstractmethod


class BaseEvoEngine(Stateful, SingletonNameable):
    """Base class for evolutionary algorithm engines.
    
    Coordinates the optimization process by managing populations, evaluators, 
    and operators for evolutionary computation.
    """
    
    def __init__(self, run_id: str,
                 seeding_rules: Optional[List[Rule]] = None):
        """Initialize the base evolutionary engine.
        
        Args:
            run_id (str): Unique identifier for this evolutionary run
            seeding_rules (Optional[List[Rule]], optional): Initial rules to seed the population. 
                Defaults to None.
        """
        self.run_id = run_id
        self.evaluator: Evaluator = None
        self.obj_extractor: ObjectiveExtractor = None
        self.init_opr: InitOperator = None
        self.seeding_rules = seeding_rules
        self.status = EvoRunStatus.RUNNING
        
        self.pop: Population = None
        self.archived: Population = None
        
        self._random = random.Random(cfg.RANDOM_SEED)
        
    def set_evaluator(self, evaluator: Evaluator) -> Self:
        self.evaluator = evaluator
        return self
    
    def set_obj_extractor(self, obj_extractor: ObjectiveExtractor) -> Self:
        self.obj_extractor = obj_extractor
        return self
    
    def set_init_opr(self, init_opr: InitOperator) -> Self:
        self.init_opr = init_opr
        return self
        
    def _init_pop(self, pop_size: int) -> None:
        """Initialize the population with individuals.
        
        Args:
            pop_size (int): Size of population to initialize
        """
        ind_cls: Type[IndividualType] = self.init_opr.ind_cls
        self.pop = Population(ind_cls=ind_cls, max_population_size=pop_size)
        
        # Seeding
        if self.seeding_rules:
            self.pop.extend_pop([ind_cls.from_rule(rule) for rule in self.seeding_rules])
        
        # Initialize remaining individuals
        for _ in range(pop_size - len(self.pop.population)):
            self.pop.add_ind(self.init_opr())
        
    def _is_similar(self, ind1: Individual, ind2: Individual) -> bool:
        """Check if two individuals are similar.
        
        Args:
            ind1 (Individual): First individual to compare
            ind2 (Individual): Second individual to compare
            
        Returns:
            bool: True if individuals are similar, False otherwise
        """
        # If id equal
        if id(ind1) == id(ind2):
            return True
        
        # If entity of root (tree) (A Pydantic Model)
        if ind1.chromosome.to_entity().root == ind2.chromosome.to_entity().root:
            return True
        
        return False
    
    @abstractmethod
    def run(self, **kwargs) -> List[Individual]:
        """Run the evolutionary algorithm.
        
        Args:
            **kwargs: Additional arguments for algorithm configuration
            
        Returns:
            List[Individual]: List of best individuals from the run
        """
        pass
    
    @abstractmethod
    def rerun(self, **kwargs) -> List[Individual]:
        """Rerun the evolutionary algorithm using metadata attributes.
        
        Args:
            **kwargs: Configuration to stop this rerun
            
        Returns:
            List[Individual]: List of best individuals from the rerun
        """
        pass
    
    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {
            'random_state': self._random.getstate(),
            'pop': self.pop.fallback_state,
            'archived': self.archived.fallback_state,
        }
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self._random.setstate(fallback_state['random_state'])
        self.pop = Population(ind_cls=self.init_opr.ind_cls)
        self.archived = Population(ind_cls=self.init_opr.ind_cls)
        self.pop.set_from_fallback_state(fallback_state['pop'])
        self.archived.set_from_fallback_state(fallback_state['archived'])
        
    def _check_ready_oprs(self) -> bool:
        """Check if all required operators are ready.
        
        Returns:
            bool: True if all required operators are set, False otherwise
        """
        if not self.init_opr:
            return False
        if not self.evaluator:
            return False
        if not self.obj_extractor:
            return False
        return True