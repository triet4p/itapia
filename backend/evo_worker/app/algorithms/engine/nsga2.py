"""NSGA-II evolutionary algorithm engine implementation."""

from copy import deepcopy
from ..pop import DominanceIndividual, Individual, Population
from ..comparator import DominateComparator
from ..dominance import non_dominated_sorting, crowding_distance_assignment
from ..operators.construct import InitOperator
from ..operators.crossover import CrossoverOperator
from ..operators.mutation import MutationOperator
from ..operators.selection import SelectionOperator
from ..operators.replacement import ReplacementOperator
from ..objective import ObjectiveExtractor, SingleObjectiveExtractor
from app.backtest.evaluator import Evaluator

import app.core.config as cfg

from typing import Any, Dict, List, Optional, Self, Tuple
from ._base import BaseEvoEngine
import random

from ..adap import AdaptiveScoreManager

from itapia_common.rules.rule import Rule
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger("NSGA-II Evo Engine")


class NSGA2EvoEngine(BaseEvoEngine):
    """NSGA-II (Non-dominated Sorting Genetic Algorithm II) evolutionary engine.
    
    Implements the NSGA-II algorithm for multi-objective optimization with 
    adaptive operator selection and specialized genetic operators.
    """
    
    def __init__(self, 
                 run_id: str,
                 seeding_rules: Optional[List[Rule]] = None,
                 pop_size: int = 150,
                 num_gen: int = 500,
                 pc: float = 0.8,
                 pm: float = 0.2,
                 lr: float = 0.5,
                 update_score_period: int = 50,
                 archive_each_gen: int = 50):
        """Initialize NSGA-II evolutionary engine.
        
        Args:
            run_id (str): Unique identifier for this evolutionary run
            seeding_rules (Optional[List[Rule]], optional): Initial rules to seed the population. 
                Defaults to None.
            pop_size (int, optional): Population size. Defaults to 150.
            num_gen (int, optional): Number of generations. Defaults to 500.
            pc (float, optional): Crossover probability. Defaults to 0.8.
            pm (float, optional): Mutation probability. Defaults to 0.2.
            lr (float, optional): Learning rate for adaptive scoring. Defaults to 0.5.
            update_score_period (int, optional): Period to update adaptive scores. Defaults to 50.
            archive_each_gen (int, optional): Number of individuals to archive each generation. Defaults to 50.
        """
        super().__init__(run_id, seeding_rules)
        self.pareto_front: List[DominanceIndividual] = None
        self.pop: Population[DominanceIndividual] = None
        self.archived: Population[DominanceIndividual] = None
        
        self.adaptive_obj_extractor: SingleObjectiveExtractor = None
    
        self.crossover_oprs: Dict[str, CrossoverOperator[DominanceIndividual]] = {}
        self.crossover_adap = AdaptiveScoreManager(lr)
        
        self.mutation_oprs: Dict[str, MutationOperator[DominanceIndividual]] = {}
        self.mutation_adap = AdaptiveScoreManager(lr)
        
        self.selection_opr: SelectionOperator[DominanceIndividual] = None
        self.replacement_opr: ReplacementOperator[DominanceIndividual] = None
        self.dominate_comparator: DominateComparator = None
        
        self.pop_size = pop_size
        self.num_gen = num_gen
        self.pc = pc
        self.pm = pm
        self.lr = lr
        self.update_score_period = update_score_period
        self.archive_each_gen = archive_each_gen
        self._cur_gen = 0
        
    def set_init_opr(self, init_opr: InitOperator[DominanceIndividual]) -> Self:
        return super().set_init_opr(init_opr)
    
    def set_selection_opr(self, selection_opr: SelectionOperator[DominanceIndividual]) -> Self:
        self.selection_opr = selection_opr
        return self
    
    def set_replacement_opr(self, replacement_opr: ReplacementOperator[DominanceIndividual]) -> Self:
        self.replacement_opr = replacement_opr
        return self
    
    def add_crossover_opr(self, crossover_opr: CrossoverOperator[DominanceIndividual], init_score: float = 1.0) -> Self:
        """Add a crossover operator to the NSGA-II engine.
        
        Args:
            crossover_opr (CrossoverOperator[DominanceIndividual]): Crossover operator to add
            init_score (float, optional): Initial score for adaptive selection. Defaults to 1.0.
            
        Returns:
            NSGA2EvoEngine: Self for method chaining
        """
        self.crossover_oprs[crossover_opr.singleton_name] = crossover_opr
        self.crossover_adap.init_score(crossover_opr, init_score)
        return self
    
    def add_mutation_opr(self, mutation_opr: MutationOperator[DominanceIndividual], init_score: float = 1.0) -> Self:
        """Add a mutation operator to the NSGA-II engine.
        
        Args:
            mutation_opr (MutationOperator[DominanceIndividual]): Mutation operator to add
            init_score (float, optional): Initial score for adaptive selection. Defaults to 1.0.
            
        Returns:
            NSGA2EvoEngine: Self for method chaining
        """
        self.mutation_oprs[mutation_opr.singleton_name] = mutation_opr
        self.mutation_adap.init_score(mutation_opr, init_score)
        return self
    
    def set_dominate_comparator(self, dominate_comparator: DominateComparator) -> Self:

        self.dominate_comparator = dominate_comparator
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
        if not self.selection_opr:
            return False
        if not self.replacement_opr:
            return False
        if not self.dominate_comparator:
            return False
        if not self.crossover_oprs:
            return False
        if not self.mutation_oprs:
            return False
        return True
        
    def _classify_pop(self) -> None:
        """Classify population into non-dominated fronts with crowding distances.
        
        Each individual is assigned a rank during the non-dominated sorting process.
        """
        # Each individual has already been assigned rank in the non-dominated sorting function itself
        fronts = non_dominated_sorting(self.pop.population, self.dominate_comparator)
        for front in fronts:
            crowding_distance_assignment(front)
        self.pareto_front = fronts[0]
        
    def _apply_mutation(self, mutation_opr: MutationOperator[DominanceIndividual],
                        ind: DominanceIndividual, pm: float, force: bool = False) -> DominanceIndividual | None:
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
            
    def _gen_offs_each_epoch(self, last_pop: List[DominanceIndividual],
                             pc: float,
                             pm: float) -> Population:
        """Generate offspring population for each epoch/generation.
        
        Args:
            last_pop (List[DominanceIndividual]): Parent population
            pc (float): Crossover probability
            pm (float): Mutation probability
            
        Returns:
            Population: Offspring population
        """
        offs: List[DominanceIndividual] = []
        
        while len(offs) < len(last_pop):
            crossover_opr = self.crossover_oprs[self.crossover_adap.select()]
            
            mutation_opr = self.mutation_oprs[self.mutation_adap.select()]
           
            # Choose 2 parents
            p1, p2 = self.selection_opr(last_pop, num_selections=2)
            
            if self._is_similar(p1, p2):
                continue
            
            # Crossover
            c1, c2 = None, None
            was_crossover = False
            
            logger.info(f'Choose Crossover: {crossover_opr.singleton_name}')
            if self._random.random() < pc:
                pairs = crossover_opr(p1, p2)
                if pairs:
                    c1, c2 = pairs
                    was_crossover = True
                    c1.cal_fitness(self.evaluator, self.obj_extractor)
                    c2.cal_fitness(self.evaluator, self.obj_extractor)
                    
                    worst_parent_fitness = min(p1.flatten_fitness(self.adaptive_obj_extractor), 
                                               p2.flatten_fitness(self.adaptive_obj_extractor))
                    improvement = 0.0
                    improvement += max(0.0, 
                                       c1.flatten_fitness(self.adaptive_obj_extractor) - worst_parent_fitness)
                    improvement += max(0.0, 
                                       c2.flatten_fitness(self.adaptive_obj_extractor) - worst_parent_fitness)
                    self.crossover_adap.add_temp_score(crossover_opr, improvement)
                    
            if not was_crossover:
                c1 = DominanceIndividual.from_rule(deepcopy(p1.chromosome))
                c1.metrics, c1.fitness = p1.metrics, p1.fitness
                c2 = DominanceIndividual.from_rule(deepcopy(p2.chromosome))
                c2.metrics, c2.fitness = p2.metrics, p2.fitness
            logger.info(f'Choose Mutation: {mutation_opr.singleton_name}')     
            c1 = self._apply_mutation(mutation_opr, c1, pm, force=not was_crossover)
            c2 = self._apply_mutation(mutation_opr, c2, pm, force=not was_crossover)
            
            if c1 is None or c2 is None:
                continue
            
            if self._is_similar(p1, c1) or self._is_similar(p2, c2):
                continue
            
            offs.extend([c1, c2])  
        
        offs = offs[:len(last_pop)]  
        
        offs_pop = Population(max_population_size=len(offs), ind_cls=DominanceIndividual)
        offs_pop.population = offs
        return offs_pop
    
    def _run_each_gen(self, pop_size: int, pc: float, pm: float) -> None:
        """Run one generation of the NSGA-II algorithm.
        
        Args:
            pop_size (int): Target population size
            pc (float): Crossover probability
            pm (float): Mutation probability
        """
        logger.info("Generating offspring population...")
        # Generate offsprings
        offs = self._gen_offs_each_epoch(self.pop.population, pc, pm)
        logger.info(f"Calculating fitness for offs population of {self.pop.population_size} individuals...")
        #offs.cal_fitness(self.evaluator, self.obj_extractor) #Remove
        self.archived.population.extend(self._random.sample(offs.population, k=min(self.archive_each_gen, len(offs.population))))
        
        # Create new population
        logger.info("Performing survival selection...")
        new_pop = self.replacement_opr(population=self.pop.population, 
                                                    offspring_population=offs.population, 
                                                    target_size=pop_size)
        
        self.pop.reassign(new_pop)
        
    
        # 4. Classify new population for next generation
        logger.info("Classifying new population...")
        return self._classify_pop()
    
    def run(self, **kwargs) -> List[DominanceIndividual]:
        """Run the complete NSGA-II evolutionary algorithm.
        
        Args:
            **kwargs: Additional configuration parameters. Required:
                - stop_gen (int, optional): Generation to stop at. Defaults to num_gen.
                
        Returns:
            List[DominanceIndividual]: Pareto front individuals from final generation
        """
        pop_size = self.pop_size
        num_gen = self.num_gen
        pc = self.pc
        pm = self.pm
        stop_gen = int(kwargs.get("stop_gen", num_gen))
        
        logger.info("Initializing population (Generation 0)...")
        self._init_pop(pop_size)
        
        logger.info(f"Calculating fitness for initial population of {self.pop.population_size} individuals...")
        self.pop.cal_fitness(self.evaluator, self.obj_extractor)
        self.archived = Population(max_population_size=cfg.MAX_ARCHIVED_RULES, ind_cls=self.pop.ind_cls)
        self.archived.extend_pop(self.pop.population)
        
        logger.info("Classifing into fronts ...")
        
        self._classify_pop()
        
        for gen in range(1, num_gen + 1):
            self._cur_gen = gen
            logger.info(f"--- Starting Generation {gen}/{num_gen} ---")
            self._run_each_gen(pop_size, pc, pm)
            logger.info(f"Generation {gen} classification complete. Pareto front size: {len(self.pareto_front)}")
            
            if gen % self.update_score_period == 0:
                self.crossover_adap.update_score()
                self.mutation_adap.update_score()
            
            if gen >= stop_gen:
                break
        
        return self.pareto_front
    
    def rerun(self,**kwargs) -> List[DominanceIndividual]:
        """Rerun the NSGA-II evolutionary algorithm from current state.
        
        Args:
            **kwargs: Additional configuration parameters. Required
                - next_stop_gen (int, optional): Generation to stop at. Defaults to num_gen.
                
        Returns:
            List[DominanceIndividual]: Pareto front individuals from final generation
            
        Raises:
            ValueError: If current generation is not in valid range [1, next_stop_gen]
        """
        pop_size = self.pop_size
        num_gen = self.num_gen
        pc = self.pc
        pm = self.pm

        next_stop_gen = int(kwargs.get('next_stop_gen', num_gen))
        
        if self._cur_gen == 0 or self._cur_gen > next_stop_gen:
            raise ValueError("Required Current gen in [1, next_stop_gen]")
        
        self._classify_pop()
        
        for gen in range(self._cur_gen + 1, num_gen + 1):
            self._cur_gen = gen
            logger.info(f"--- Starting Generation {gen}/{num_gen} ---")
            self._run_each_gen(pop_size, pc, pm)
            logger.info(f"Generation {gen} classification complete. Pareto front size: {len(self.pareto_front)}")
            
            if gen % self.update_score_period == 0:
                self.crossover_adap.update_score()
                self.mutation_adap.update_score()
            
            if gen >= next_stop_gen:
                break

        return self.pareto_front
    
    @property
    def fallback_state(self) -> Dict[str, Any]:
        state = super().fallback_state
        state.update({
            'curr_gen': self._cur_gen,
            'crossover_adap': self.crossover_adap.fallback_state,
            'mutation_adap': self.mutation_adap.fallback_state
        })
        return state
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        super().set_from_fallback_state(fallback_state)
        self._cur_gen = fallback_state["curr_gen"]
        self.crossover_adap.set_from_fallback_state(fallback_state['crossover_adap'])
        self.mutation_adap.set_from_fallback_state(fallback_state['mutation_adap'])