from itapia_common.rules.rule import Rule
from app.backtest.evaluator import ObjectiveValues, FitnessEvaluator
from app.backtest.metrics import BacktestPerformanceMetrics

class Individual:
    def __init__(self):
        self.chromosome: Rule = None
        self.fitness: ObjectiveValues = None
        self.metrics: BacktestPerformanceMetrics = None
        
    def random_init(self, max_depth: int) -> None:
        pass
    
    def cal_fitness(self, evaluator: FitnessEvaluator) -> ObjectiveValues:
        self.fitness, self.metrics = evaluator.evaluate(self.chromosome)
        return self.fitness
    
class Population:
    def __init__(self, population_size: int):
        self.population_size: int = population_size
        self.population: list[Individual] = []
        
    def random_init(self, max_ind_depth: int, evaluator: FitnessEvaluator) -> None:
        for _ in range(self.population_size):
            individual = Individual()
            individual.random_init(max_ind_depth)
            individual.cal_fitness(evaluator)
            
            