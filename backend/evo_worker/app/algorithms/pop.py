from typing import Any, Dict, Generic, List, Self, TypeVar, Type
from itapia_common.rules.rule import Rule
from app.backtest.evaluator import Evaluator
from app.backtest.metrics import BacktestPerformanceMetrics
from app.state import Stateful
from .objective import AcceptedObjective, ObjectiveExtractor, SingleObjectiveExtractor

IndividualType = TypeVar("IndividualType", bound='Individual')

class Individual(Stateful):
    def __init__(self):
        self.chromosome: Rule = None
        self.fitness: AcceptedObjective = None
        self.metrics: BacktestPerformanceMetrics = None
    
    def cal_fitness(self, evaluator: Evaluator, obj_extractor: ObjectiveExtractor) -> AcceptedObjective:
        self.metrics = evaluator.evaluate(self.chromosome)
        self.fitness = obj_extractor.extract(self.metrics)
        return self.fitness
    
    @classmethod
    def from_rule(cls, rule: Rule) -> Self:
        new_ind = cls()
        new_ind.chromosome = rule
    
        return new_ind
    
    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {
            'chromosome': self.chromosome.to_entity(),
            'fitness': self.fitness,
            'metrics': self.metrics
        }
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self.chromosome = Rule.from_entity(fallback_state['chromosome'])
        self.fitness: AcceptedObjective = fallback_state['fitness']
        self.metrics: BacktestPerformanceMetrics = fallback_state['metrics']
        
class DominanceIndividual(Individual):
    def __init__(self):
        super().__init__()
        self.rank: int = -1
        self.crowding_distance: float = 0.0
        
    def flatten_fitness(self, single_obj_extractor: SingleObjectiveExtractor) -> float:
        if not self.metrics:
            raise ValueError('Metrics must be set before flatten fitness.')
        return single_obj_extractor.extract(self.metrics)
        
    @property
    def fallback_state(self) -> Dict[str, Any]:
        state = super().fallback_state
        state.update({
            'rank': self.rank,
            'crowding_distance': self.crowding_distance,
        })
        return state
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        super().set_from_fallback_state(fallback_state)
        self.rank = fallback_state['rank']
        self.crowding_distance = fallback_state['crowding_distance']
    
class Population(Stateful, Generic[IndividualType]):
    def __init__(self, population_size: int, ind_cls: Type[IndividualType]):
        self.population_size: int = population_size
        self.population: list[IndividualType] = []
        self.ind_cls: Type[IndividualType] = ind_cls
        
    def reassign(self, population: List[IndividualType]):
        self.population = population
        self.population_size = len(self.population)
        
    def cal_fitness(self, evaluator: Evaluator, obj_extractor: ObjectiveExtractor):
        for ind in self.population:
            ind.cal_fitness(evaluator, obj_extractor)
            
    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {
            'population_size': self.population_size,
            'population': [ind.fallback_state for ind in self.population],
            'ind_cls': self.ind_cls
        }
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self.population_size: int = fallback_state['population_size']
        self.ind_cls: Type[IndividualType] = fallback_state['ind_cls']
        for i in range(self.population_size):
            ind = self.ind_cls()
            ind.set_from_fallback_state(fallback_state['population'][i])
            self.population.append(ind)