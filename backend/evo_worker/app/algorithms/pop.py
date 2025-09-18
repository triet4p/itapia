from typing import Any, Dict, Generic, List, Self, Tuple, TypeVar, Type
from itapia_common.rules.rule import Rule
from app.backtest.evaluator import Evaluator
from app.performances.metrics import PerformanceMetricsCalculator
from app.state import Stateful
from app.algorithms.objective import AcceptedObjective, MultiObjectiveExtractor, ObjectiveExtractor, SingleObjectiveExtractor

IndividualType = TypeVar("IndividualType", bound='Individual')

class Individual(Stateful):
    """Base class representing an individual in the evolutionary algorithm."""
    
    def __init__(self):
        """Initialize an individual with empty chromosome, fitness, and metrics."""
        self.chromosome: Rule = None
        self.fitness: AcceptedObjective = None
        self.metrics: PerformanceMetricsCalculator = None
    
    def cal_fitness(self, evaluator: Evaluator, obj_extractor: ObjectiveExtractor) -> AcceptedObjective:
        """Calculate fitness for the individual.
        
        Args:
            evaluator (Evaluator): Evaluator to assess the chromosome
            obj_extractor (ObjectiveExtractor): Extractor to get objective values from metrics
            
        Returns:
            AcceptedObjective: Calculated fitness value
        """
        self.metrics = evaluator.evaluate(self.chromosome)
        self.fitness = obj_extractor.extract(self.metrics)
        return self.fitness
    
    def flatten_fitness(self, single_obj_extractor: SingleObjectiveExtractor) -> float:
        """Flatten evaluated metrics to single objective.
        
        Args:
            single_obj_extractor (SingleObjectiveExtractor): Extractor to convert multi-objective to single
            
        Returns:
            float: Flattened fitness value
            
        Raises:
            ValueError: If metrics have not been set
        """
        if not self.metrics:
            raise ValueError('Metrics must be set before flatten fitness.')
        return single_obj_extractor.extract(self.metrics)
    
    @classmethod
    def from_rule(cls, rule: Rule) -> Self:
        """Create an individual from a rule.
        
        Args:
            rule (Rule): Rule to create individual from
            
        Returns:
            Self: New individual with the given rule as chromosome
        """
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
        self.metrics: PerformanceMetricsCalculator = fallback_state['metrics']
        
class DominanceIndividual(Individual):
    """Individual class for dominance-based evolutionary algorithms."""
    
    def __init__(self):
        """Initialize a dominance individual with rank and crowding distance."""
        super().__init__()
        self.fitness: Tuple[float, ...] = None
        self.rank: int = -1
        self.crowding_distance: float = 0.0
        
    def cal_fitness(self, evaluator: Evaluator, obj_extractor: MultiObjectiveExtractor) -> Tuple[float, ...]:
        """Calculate fitness for the dominance individual.
        
        Args:
            evaluator (Evaluator): Evaluator to assess the chromosome
            obj_extractor (MultiObjectiveExtractor): Extractor to get objective values from metrics
            
        Returns:
            Tuple[float, ...]: Calculated fitness values
        """
        return super().cal_fitness(evaluator, obj_extractor)
        
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
        
class MOEADIndividual(Individual):
    """Individual class for MOEA/D (Multi-Objective Evolutionary Algorithm based on Decomposition)."""
    
    def __init__(self):
        """Initialize a MOEA/D individual with problem index."""
        super().__init__()
        self.fitness: Tuple[float, ...] = None
        self.problem_idx: int = -1
        
    def cal_fitness(self, evaluator: Evaluator, obj_extractor: MultiObjectiveExtractor) -> Tuple[float, ...]:
        """Calculate fitness for the MOEA/D individual.
        
        Args:
            evaluator (Evaluator): Evaluator to assess the chromosome
            obj_extractor (MultiObjectiveExtractor): Extractor to get objective values from metrics
            
        Returns:
            Tuple[float, ...]: Calculated fitness values
        """
        return super().cal_fitness(evaluator, obj_extractor)
        
    @property
    def fallback_state(self) -> Dict[str, Any]:
        state = super().fallback_state
        state.update({
            'problem_idx': self.problem_idx
        })
        return state
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        super().set_from_fallback_state(fallback_state)
        self.problem_idx = fallback_state['problem_idx']
    
    
class Population(Stateful, Generic[IndividualType]):
    """Population class representing a collection of individuals in the evolutionary algorithm."""
    
    def __init__(self, ind_cls: Type[IndividualType], max_population_size: int=None):
        """Initialize a population.
        
        Args:
            ind_cls (Type[IndividualType]): The individual class type
            max_population_size (int, optional): Maximum population size. Defaults to 1000000.
        """
        self.max_population_size: int = max_population_size if max_population_size else 1000000
        self.population: list[IndividualType] = []
        self.ind_cls: Type[IndividualType] = ind_cls
        
    @property
    def population_size(self) -> int:
        """Get the current population size.
        
        Returns:
            int: Number of individuals in the population
        """
        return len(self.population)
    
    def add_ind(self, ind: IndividualType) -> bool:
        """Add an individual to the population.
        
        Args:
            ind (IndividualType): Individual to add
            
        Returns:
            bool: True if individual was added, False if population is at maximum size
        """
        if self.population_size == self.max_population_size:
            return False
        self.population.append(ind)
        return True
        
    def extend_pop(self, population: List[IndividualType], auto_clip: bool=True) -> bool:
        """Extend the population with a list of individuals.
        
        Args:
            population (List[IndividualType]): List of individuals to add
            auto_clip (bool): Whether to automatically clip if exceeding max size. Defaults to True.
            
        Returns:
            bool: True if operation succeeded, False if would exceed max size and auto_clip is False
        """
        remain = self.max_population_size - self.population_size
        if remain < len(population):
            if auto_clip:
                self.population.extend(population[:remain])
                return True
            return False

        self.population.extend(population)
        return True
        
    def reassign(self, population: List[IndividualType]):
        """Replace the current population with a new list of individuals.
        
        Args:
            population (List[IndividualType]): New list of individuals
        """
        self.population = population
        
    def clear(self) -> None:
        """Clear all individuals from the population."""
        self.population.clear()
        
    def cal_fitness(self, evaluator: Evaluator, obj_extractor: ObjectiveExtractor):
        """Calculate fitness for all individuals in the population.
        
        Args:
            evaluator (Evaluator): Evaluator to assess the chromosomes
            obj_extractor (ObjectiveExtractor): Extractor to get objective values from metrics
        """
        for ind in self.population:
            ind.cal_fitness(evaluator, obj_extractor)
            
    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {
            'population_size': self.population_size,
            'max_population_size': self.max_population_size,
            'population': [ind.fallback_state for ind in self.population]
        }
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        # Use if to ensure legacy fallback state
        if fallback_state.get('max_population_size'):
            self.max_population_size = fallback_state['max_population_size']
        for i in range(len(fallback_state['population'])):
            ind = self.ind_cls()
            ind.set_from_fallback_state(fallback_state['population'][i])
            self.population.append(ind)