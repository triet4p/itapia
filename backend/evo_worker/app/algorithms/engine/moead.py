from copy import deepcopy
from typing import Any, Dict, List, Optional, Self, Tuple

from ..pop import MOEADIndividual, Population
from ..operators.construct import InitOperator
from ..operators.crossover import CrossoverOperator
from ..operators.mutation import MutationOperator
from ..objective import ObjectiveExtractor, MultiObjectiveExtractor, SingleObjectiveExtractor
from app.backtest.evaluator import Evaluator
from ..decomposition import DecompositionManager
from ..adap import AdaptiveScoreManager
import app.core.config as cfg
from ._base import BaseEvoEngine
from itapia_common.rules.rule import Rule
from itapia_common.logger import ITAPIALogger
import numpy as np

logger = ITAPIALogger("MOEA/D Evo Engine")

class MOEADEvoEngine(BaseEvoEngine):
    """MOEAD (Multi-Objective Evolutionary Algorithm based on Decomposition) evolutionary engine.
    
    Implements the NSGA-II algorithm for multi-objective optimization with 
    adaptive operator selection and specialized genetic operators.
    """
    def __init__(self, run_id: str,
                 num_objs: int,
                 num_divisions: int,
                 neighborhood_size: int,
                 num_gen: int = 500,
                 pc: float = 1.0,
                 pm: float = 0.2,
                 lr: float = 0.5,
                 update_score_period: int = 50,
                 archive_each_gen: int = 50,
                 seeding_rules: Optional[List[Rule]] = None):
        """Initialize MOEA/D evolutionary engine.
        
        Args:
            run_id (str): Unique identifier for this evolutionary run
            num_objs (int): Number of objectives in the optimization problem
            num_divisions (int): Number of divisions for weight vector generation
            neighborhood_size (int): Size of neighborhood for each weight vector
            num_gen (int, optional): Number of generations. Defaults to 500.
            pc (float, optional): Crossover probability. Defaults to 1.0.
            pm (float, optional): Mutation probability. Defaults to 0.2.
            lr (float, optional): Learning rate for adaptive scoring. Defaults to 0.5.
            update_score_period (int, optional): Period to update adaptive scores. Defaults to 50.
            archive_each_gen (int, optional): Number of individuals to archive each generation. Defaults to 50.
            seeding_rules (Optional[List[Rule]], optional): Initial rules to seed the population. 
                Defaults to None.
        """
        super().__init__(run_id, seeding_rules)
        self.pop: Population[MOEADIndividual] = None
        self.archived: Population[MOEADIndividual] = None
        
        self.adaptive_obj_extractor: SingleObjectiveExtractor = None
        
        self.crossover_oprs: Dict[str, CrossoverOperator[MOEADIndividual]] = {}
        self.crossover_adap = AdaptiveScoreManager(lr)
        
        self.mutation_oprs: Dict[str, MutationOperator[MOEADIndividual]] = {}
        self.mutation_adap = AdaptiveScoreManager(lr)
        
        self.num_objs = num_objs
        self.num_divisions = num_divisions
        self.neighborhood_size = neighborhood_size
        
        self.num_gen = num_gen
        self.pc = pc
        self.pm = pm
        self.lr = lr
        self.update_score_period = update_score_period
        self.archive_each_gen = archive_each_gen
        self._cur_gen = 0
        
        self._init_decomposer()
        self.pop_size = self.decomposer.num_vectors
        
        
    def _init_decomposer(self):
        self.decomposer = DecompositionManager(self.num_objs, self.num_divisions, self.neighborhood_size)
        self.decomposer.generate_weight_vectors().calculate_neighborhoods()
        
        self.reference_points = np.full(self.num_objs, -np.inf)
        
    def set_init_opr(self, init_opr: InitOperator[MOEADIndividual]) -> Self:
        return super().set_init_opr(init_opr)
    
    def add_crossover_opr(self, crossover_opr: CrossoverOperator[MOEADIndividual], init_score: float = 1.0) -> Self:

        self.crossover_oprs[crossover_opr.singleton_name] = crossover_opr
        self.crossover_adap.init_score(crossover_opr, init_score)
        return self
    
    def add_mutation_opr(self, mutation_opr: MutationOperator[MOEADIndividual], init_score: float = 1.0) -> Self:

        self.mutation_oprs[mutation_opr.singleton_name] = mutation_opr
        self.mutation_adap.init_score(mutation_opr, init_score)
        return self
    
    def set_adaptive_obj_extractor(self, adaptive_obj_extractor: SingleObjectiveExtractor) -> Self:

        self.adaptive_obj_extractor = adaptive_obj_extractor
        return self
    
    def _check_ready_oprs(self) -> bool:
        """Check if all required operators are ready for NSGA-II execution.
        
        Returns:
            bool: True if all required operators are set, False otherwise
        """
        super_check = super()._check_ready_oprs()
        if not super_check:
            return False
        if not self.crossover_oprs:
            return False
        if not self.mutation_oprs:
            return False
        return True
    
    def _update_reference_point(self, individual: MOEADIndividual):
        """
        Update z* reference points with a tuple fitness of a MOEA/D individual
        """
        # Compare each objectives and hold greater value
        self.reference_points = np.maximum(self.reference_points, np.array(individual.fitness))
        
    def _select_parents_from_neighborhood(self, subproblem_index: int) -> Tuple[MOEADIndividual, MOEADIndividual]:

        neighborhood_indices = self.decomposer.neighborhoods[subproblem_index]
        
        p1_idx, p2_idx = self._random.sample(list(neighborhood_indices), 2)
        
        return self.pop.population[p1_idx], self.pop.population[p2_idx]
    
    def _apply_mutation(self, mutation_opr: MutationOperator[MOEADIndividual],
                        ind: MOEADIndividual, pm: float, force: bool = False) -> MOEADIndividual | None:
        """
        Apply mutation to an individual.
        'force=True' will ensure mutation is performed.
        
        Args:
            mutation_opr (MutationOperator[DominanceIndividual]): Mutation operator to apply
            ind (DominanceIndividual): Individual to mutate
            pm (float): Mutation probability
            force (bool, optional): Force mutation regardless of probability. Defaults to False.
            
        Returns:
            DominanceIndividual | None: Mutated individual or None if mutation failed
        """
        if force or self._random.random() < pm:
            mutated_ind = mutation_opr(ind)
            if mutated_ind:
                mutated_ind.cal_fitness(self.evaluator, self.obj_extractor)
                improvement = max(0.0, 
                                  mutated_ind.flatten_fitness(self.adaptive_obj_extractor) - 
                                  ind.flatten_fitness(self.adaptive_obj_extractor))
                self.mutation_adap.add_temp_score(mutation_opr, improvement)
            return mutated_ind
        return ind
    
    def _run_each_gen(self):
        for i in range(self.pop_size):
            # 1. Choose adaptive operator
            crossover_opr = self.crossover_oprs[self.crossover_adap.select()]
            mutation_opr = self.mutation_oprs[self.mutation_adap.select()]
            
            # 2. Select parent from neighborhood
            p1, p2 = self._select_parents_from_neighborhood(i)
            if self._is_similar(p1, p2): 
                continue
            
            c = None
            was_crossover = False
            
            logger.info(f'Choose Crossover: {crossover_opr.singleton_name}')
            if self._random.random() < self.pc:
                pairs = crossover_opr(p1, p2)
                if pairs:
                    c = self._random.choice(pairs)
                    was_crossover = True
                    c.cal_fitness(self.evaluator, self.obj_extractor)
                    worst_parent_fitness = min(p1.flatten_fitness(self.adaptive_obj_extractor), 
                                               p2.flatten_fitness(self.adaptive_obj_extractor))
                    improvement = 0.0
                    improvement += max(0.0, 
                                       c.flatten_fitness(self.adaptive_obj_extractor) - worst_parent_fitness)
                    self.crossover_adap.add_temp_score(crossover_opr, improvement)

            if not c: # Nếu lai ghép thất bại hoặc không diễn ra
                p = self._random.choice([p1, p2])
                c = MOEADIndividual.from_rule(deepcopy(p.chromosome))
                c.metrics, c.fitness = p.metrics, p.fitness

            c = self._apply_mutation(mutation_opr, c, self.pm, force=not was_crossover)
            
            if c is None:
                continue
            
            if self._is_similar(c, p1) or self._is_similar(c, p2):
                continue
            
            # update neighborhood
            indices_to_update = self.decomposer.neighborhoods[i]
            for neighbor_idx in indices_to_update:
                neighbor = self.pop.population[neighbor_idx]
                
                child_scalar_fitness = self.decomposer.scalar_tchebycheff(
                    c.fitness, neighbor_idx, self.reference_points
                )
                neighbor_scalar_fitness = self.decomposer.scalar_tchebycheff(
                    neighbor.fitness, neighbor_idx, self.reference_points
                )
                
                if child_scalar_fitness <= neighbor_scalar_fitness:
                    
                    new_neighbor = deepcopy(c)
                    new_neighbor.problem_idx = neighbor_idx
                    
                    self.archived.add_ind(self.pop.population[neighbor_idx])
                    
                    self.pop.population[neighbor_idx] = new_neighbor
                    
    def run(self, **kwargs) -> List[MOEADIndividual]:
        """Run the complete MOEA/D evolutionary algorithm.
        
        Args:
            **kwargs: Additional configuration parameters. Required:
                - stop_gen (int, optional): Generation to stop at. Defaults to num_gen.
                
        Returns:
            List[MOEADIndividual]: All of last population of Engine.
        """
        pop_size = self.pop_size
        num_gen = self.num_gen
        stop_gen = int(kwargs.get("stop_gen", num_gen))
        
        logger.info("Initializing population (Generation 0)...")
        self._init_pop(pop_size)
        
        logger.info(f"Calculating fitness for initial population of {self.pop.population_size} individuals...")
        self.pop.cal_fitness(self.evaluator, self.obj_extractor)
        self.archived = Population(max_population_size=cfg.MAX_ARCHIVED_RULES, ind_cls=self.pop.ind_cls)
        self.archived.extend_pop(self.pop.population)
        
        logger.info("Classifing into fronts ...")
        
        for gen in range(1, num_gen + 1):
            self._cur_gen = gen
            logger.info(f"--- Starting Generation {gen}/{num_gen} ---")
            
            logger.info('Updating ref points')
            for ind in self.pop.population:
                self._update_reference_point(ind)
            
            self._run_each_gen()
            logger.info(f"Generation {gen} classification complete")
            
            if gen % self.update_score_period == 0:
                self.crossover_adap.update_score()
                self.mutation_adap.update_score()
            
            if gen >= stop_gen:
                break
        
        return self.pop
    
    def rerun(self, **kwargs) -> List[MOEADIndividual]:
        """Rerun the MOEA/D evolutionary algorithm from current state.
        
        Args:
            **kwargs: Additional configuration parameters. Required
                - next_stop_gen (int, optional): Generation to stop at. Defaults to num_gen.
                
        Returns:
            List[MOEADIndividual]: All pop from final.
            
        Raises:
            ValueError: If current generation is not in valid range [1, next_stop_gen]
        """
        num_gen = self.num_gen

        next_stop_gen = int(kwargs.get('next_stop_gen', num_gen))
        
        if self._cur_gen == 0 or self._cur_gen > next_stop_gen:
            raise ValueError("Required Current gen in [1, next_stop_gen]")
        
        for gen in range(self._cur_gen + 1, num_gen + 1):
            self._cur_gen = gen
            logger.info(f"--- Starting Generation {gen}/{num_gen} ---")
            
            logger.info('Updating ref points')
            for ind in self.pop.population:
                self._update_reference_point(ind)
            
            self._run_each_gen()
            logger.info(f"Generation {gen} classification complete.")
            
            if gen % self.update_score_period == 0:
                self.crossover_adap.update_score()
                self.mutation_adap.update_score()
            
            if gen >= next_stop_gen:
                break

        return self.pop
    
    @property
    def fallback_state(self) -> Dict[str, Any]:
        state = super().fallback_state
        state.update({
            'curr_gen': self._cur_gen,
            'crossover_adap': self.crossover_adap.fallback_state,
            'mutation_adap': self.mutation_adap.fallback_state,
            'decomposer': self.decomposer.fallback_state,
            'reference_points': self.reference_points.tolist()
        })
        return state
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        super().set_from_fallback_state(fallback_state)
        self._cur_gen = fallback_state["curr_gen"]
        self.crossover_adap.set_from_fallback_state(fallback_state['crossover_adap'])
        self.mutation_adap.set_from_fallback_state(fallback_state['mutation_adap'])
        self.decomposer.set_from_fallback_state(fallback_state['decomposer'])
        self.reference_points = np.array(fallback_state['reference_points'])