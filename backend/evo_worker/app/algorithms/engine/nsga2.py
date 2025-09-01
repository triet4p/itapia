from copy import deepcopy
from ..pop import DominanceIndividual, Individual, Population
from ..comparator import DominateComparator, non_dominated_sorting, crowding_distance_assignment
from ..operators.construct import InitOperator
from ..operators.crossover import CrossoverOperator
from ..operators.mutation import MutationOperator
from ..operators.selection import SelectionOperator
from ..operators.replacement import ReplacementOperator
from ..objective import ObjectiveExtractor
from app.backtest.evaluator import Evaluator

import app.core.config as cfg

from typing import Any, Dict, List, Optional
from ._base import BaseStructureEvoEngine
import random

from itapia_common.rules.rule import Rule
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger("NSGA-II Evo Engine")

class NSGA2EvoEngine(BaseStructureEvoEngine):
    
    def __init__(self, 
                 run_id: str,
                 evaluator: Evaluator,
                 obj_extractor: ObjectiveExtractor,
                 init_opr: InitOperator[DominanceIndividual],
                 crossover_opr: CrossoverOperator[DominanceIndividual],
                 mutation_opr: MutationOperator[DominanceIndividual],
                 selection_opr: SelectionOperator[DominanceIndividual],
                 replacement_opr: ReplacementOperator[DominanceIndividual],
                 dominate_comparator: DominateComparator,
                 seeding_rules: Optional[List[Rule]] = None,
                 pop_size: int = 150,
                 num_gen: int = 500,
                 pc: float = 0.8,
                 pm: float = 0.2):
        super().__init__(run_id, evaluator, obj_extractor, init_opr, seeding_rules)
        self.pareto_front: List[DominanceIndividual] = None
    
        self.crossover_opr = crossover_opr
        self.mutation_opr = mutation_opr
        self.selection_opr = selection_opr
        self.replacement_opr = replacement_opr
        self.dominate_comparator = dominate_comparator
        
        self.pop_size = pop_size
        self.num_gen = num_gen
        self.pc = pc
        self.pm = pm
        self._cur_gen = 0
        
    def _classify_pop(self):
        # Mỗi cá thể đã được gán rank trong chính hàm non dominated sorting
        fronts = non_dominated_sorting(self.pop.population, self.dominate_comparator)
        for front in fronts:
            crowding_distance_assignment(front)
        self.pareto_front = fronts[0]
        
    def _apply_mutation(self, ind: DominanceIndividual, pm: float, force: bool = False) -> DominanceIndividual | None:
        """
        Áp dụng đột biến cho một cá thể. 
        'force=True' sẽ đảm bảo đột biến được thực hiện.
        """
        if force or self._random.random() < pm:
            mutated_ind = self.mutation_opr(ind)
            return mutated_ind
        return ind
            
    def _gen_offs_each_epoch(self, last_pop: List[DominanceIndividual],
                             pc: float,
                             pm: float) -> Population:
        offs: List[DominanceIndividual] = []
        while len(offs) < len(last_pop):
            # Choose 2 parents
            p1, p2 = self.selection_opr(last_pop, num_selections=2)
            
            if self._is_similar(p1, p2):
                continue
            
            # Crossover
            c1, c2 = None, None
            was_crossover = False
            
            if self._random.random() < pc:
                pairs = self.crossover_opr(p1, p2)
                if pairs:
                    c1, c2 = pairs
                    was_crossover = True
                    
            if not was_crossover:
                c1 = DominanceIndividual.from_rule(deepcopy(p1.chromosome))
                c2 = DominanceIndividual.from_rule(deepcopy(p2.chromosome))
                
            c1 = self._apply_mutation(c1, pm, force=not was_crossover)
            c2 = self._apply_mutation(c2, pm, force=not was_crossover)
            
            if c1 is None or c2 is None:
                continue
            
            if self._is_similar(p1, c1) or self._is_similar(p2, c2):
                continue
            
            offs.extend([c1, c2])  
        
        offs = offs[:len(last_pop)]  
        
        offs_pop = Population(len(offs), ind_cls=DominanceIndividual)
        offs_pop.population = offs
        return offs_pop
    
    def _run_each_gen(self, pop_size: int, pc: float, pm: float):
        logger.info("Generating offspring population...")
        # Generate offsprings
        offs = self._gen_offs_each_epoch(self.pop.population, pc, pm)
        logger.info(f"Calculating fitness for offs population of {self.pop.population_size} individuals...")
        offs.cal_fitness(self.evaluator, self.obj_extractor)
        self.archived.population.extend(self._random.sample(offs.population, k=30))
        
        # Create new population
        logger.info("Performing survival selection...")
        self.pop.population = self.replacement_opr(population=self.pop.population, 
                                                    offspring_population=offs.population, 
                                                    target_size=pop_size)
        
    
        # 4. Phân loại quần thể mới cho thế hệ tiếp theo
        logger.info("Classifying new population...")
        return self._classify_pop()
    
    def run(self, **kwargs):
        pop_size = self.pop_size
        num_gen = self.num_gen
        pc = self.pc
        pm = self.pm
        stop_gen = int(kwargs.get("stop_gen", num_gen))
        
        logger.info("Initializing population (Generation 0)...")
        self._init_pop(pop_size)
        
        logger.info(f"Calculating fitness for initial population of {self.pop.population_size} individuals...")
        self.pop.cal_fitness(self.evaluator, self.obj_extractor)
        self.archived.population.extend(self.pop.population)
        
        logger.info("Classifing into fronts ...")
        
        self._classify_pop()
        
        for gen in range(1, num_gen + 1):
            self._cur_gen = gen
            logger.info(f"--- Starting Generation {gen}/{num_gen} ---")
            self._run_each_gen(pop_size, pc, pm)
            logger.info(f"Generation {gen} classification complete. Pareto front size: {len(self.pareto_front)}")
            if gen >= stop_gen:
                break
        
        return self.pareto_front
    
    def rerun(self,**kwargs):
        
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
            if gen >= next_stop_gen:
                break

        return self.pareto_front
    
    @property
    def fallback_state(self) -> Dict[str, Any]:
        state = super().fallback_state
        state.update({
            'curr_gen': self._cur_gen 
        })
        return state
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        super().set_from_fallback_state(fallback_state)
        self._cur_gen = fallback_state["curr_gen"]