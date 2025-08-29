from typing import List
import uuid
from itapia_common.rules.rule import Rule
from app.backtest.evaluator import Evaluator
from app.backtest.metrics import BacktestPerformanceMetrics
from .objective import AcceptedObjective, ObjectiveExtractor

class Individual:
    def __init__(self):
        self.chromosome: Rule = None
        self.fitness: AcceptedObjective = None
        self.metrics: BacktestPerformanceMetrics = None
        self.crowding_distance: float = 0.0
        self.rank: int = -1
    
    def cal_fitness(self, evaluator: Evaluator, obj_extractor: ObjectiveExtractor) -> AcceptedObjective:
        self.metrics = evaluator.evaluate(self.chromosome)
        self.fitness = obj_extractor.extract(self.metrics)
        return self.fitness
    
    @staticmethod
    def from_rule(rule: Rule) -> 'Individual':
        new_ind = Individual()
        new_ind.chromosome = rule
    
        return new_ind
    
class Population:
    def __init__(self, population_size: int):
        self.population_size: int = population_size
        self.population: list[Individual] = []
        
    def reassign(self, population: List[Individual]):
        self.population = population
        self.population_size = len(self.population)
        
    def cal_fitness(self, evaluator: Evaluator, obj_extractor: ObjectiveExtractor):
        for ind in self.population:
            ind.cal_fitness(evaluator, obj_extractor)
            