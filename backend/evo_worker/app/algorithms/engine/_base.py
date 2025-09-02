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
    def __init__(self, run_id: str,
                 seeding_rules: Optional[List[Rule]] = None):
        self.run_id = run_id
        self.evaluator: Evaluator = None
        self.obj_extractor: ObjectiveExtractor = None
        self.init_opr: InitOperator = None
        self.seeding_rules = seeding_rules
        self.status = EvoRunStatus.RUNNING
        
        self.pop: Population = None
        self.archived: Population = None
        
        self._random = random.Random(cfg.RANDOM_SEED)
        
    def set_evaluator(self, evaluator: Evaluator):
        self.evaluator = evaluator
        return self
    
    def set_obj_extractor(self, obj_extractor: ObjectiveExtractor):
        self.obj_extractor = obj_extractor
        return self
    
    def set_init_opr(self, init_opr: InitOperator):
        self.init_opr = init_opr
        return self
        
    def _init_pop(self, pop_size: int) -> None:
        ind_cls: Type[IndividualType] = self.init_opr.ind_cls
        self.pop = Population(pop_size, ind_cls)
        
        # Seeding
        if self.seeding_rules:
            self.pop.population.extend([ind_cls.from_rule(rule) for rule in self.seeding_rules])
        
        # Init remain
        for _ in range(pop_size - len(self.pop.population)):
            self.pop.population.append(self.init_opr())
        
    def _is_similar(self, ind1: Individual, ind2: Individual) -> bool:
        # If id equal
        if id(ind1) == id(ind2):
            return True
        
        # If entity of root (tree) (A Pydantic Model)
        if ind1.chromosome.to_entity().root == ind2.chromosome.to_entity().root:
            return True
        
        return False
    
    @abstractmethod
    def run(self, **kwargs) -> List[Individual]:
        pass
    
    @abstractmethod
    def rerun(self, **kwargs) -> List[Individual]:
        """Will use metadata attribute to rerun, kwargs only contain config to stop this rerun"""
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
        self.pop.set_from_fallback_state(fallback_state['pop'])
        self.archived.set_from_fallback_state(fallback_state['archived'])
        
    def _check_ready_oprs(self) -> bool:
        if not self.init_opr:
            return False
        if not self.evaluator:
            return False
        if not self.obj_extractor:
            return False
        return True