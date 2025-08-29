from ..pop import Individual, Population
from ..operators.construct import InitOperator
from ..objective import ObjectiveExtractor
from app.backtest.evaluator import Evaluator

import app.core.config as cfg

from typing import List, Optional
import random

from itapia_common.rules.rule import Rule

from abc import ABC, abstractmethod

class BaseStructureEvoEngine(ABC):
    def __init__(self, evaluator: Evaluator,
                 obj_extractor: ObjectiveExtractor,
                 init_opr: InitOperator,
                 seeding_rules: Optional[List[Rule]] = None):
        self.evaluator = evaluator
        self.obj_extractor = obj_extractor
        self.init_opr = init_opr
        self.seeding_rules = seeding_rules
        
        self.pop: Population = None
        
        self._random = random.Random(cfg.RANDOM_SEED)
        
    def _init_pop(self, pop_size: int) -> None:
        self.pop = Population(pop_size)
        
        # Seeding
        if self.seeding_rules:
            self.pop.population.extend([Individual.from_rule(rule) for rule in self.seeding_rules])
        
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