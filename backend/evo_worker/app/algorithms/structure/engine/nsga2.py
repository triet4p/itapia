from copy import deepcopy
from ..pop import Individual, Population
from ..dominance import non_dominated_sorting, crowding_distance_assignment
from ..operators.construct import InitOperator
from ..operators.crossover import CrossoverOperator
from ..operators.mutation import MutationOperator
from ..operators.selection import SelectionOperator
from ..operators.replacement import ReplacementOperator
from ..objective import ObjectiveExtractor
from app.backtest.evaluator import Evaluator

import app.core.config as cfg

from typing import List, Optional
from ._base import BaseStructureEvoEngine
import random

from itapia_common.rules.rule import Rule
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger("NSGA-II Evo Engine")

class NSGA2EvoEngine(BaseStructureEvoEngine):
    DEFAULT_CONFIG = {
        'pop_size': 100,
        'num_gen': 500,
        'pc': 0.8,
        'pm': 0.3
    }
    
    def __init__(self, 
                 evaluator: Evaluator,
                 obj_extractor: ObjectiveExtractor,
                 init_opr: InitOperator,
                 crossover_opr: CrossoverOperator,
                 mutation_opr: MutationOperator,
                 selection_opr: SelectionOperator,
                 replacement_opr: ReplacementOperator,
                 seeding_rules: Optional[List[Rule]] = None):
        super().__init__(evaluator, obj_extractor, init_opr, seeding_rules)
        self.pareto_front: List[Individual] = None
    
        self.crossover_opr = crossover_opr
        self.mutation_opr = mutation_opr
        self.selection_opr = selection_opr
        self.replacement_opr = replacement_opr
        
    def _classify_pop(self):
        # Mỗi cá thể đã được gán rank trong chính hàm non dominated sorting
        fronts = non_dominated_sorting(self.pop.population)
        for front in fronts:
            crowding_distance_assignment(front)
        self.pareto_front = fronts[0]
        
    def _apply_mutation(self, ind: Individual, pm: float, force: bool = False) -> Individual | None:
        """
        Áp dụng đột biến cho một cá thể. 
        'force=True' sẽ đảm bảo đột biến được thực hiện.
        """
        if force or self._random.random() < pm:
            mutated_ind = self.mutation_opr(ind)
            return mutated_ind
        return ind
            
    def _gen_offs_each_epoch(self, last_pop: List[Individual],
                             pc: float,
                             pm: float) -> Population:
        offs: List[Individual] = []
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
                c1 = Individual.from_rule(deepcopy(p1.chromosome))
                c2 = Individual.from_rule(deepcopy(p2.chromosome))
                
            c1 = self._apply_mutation(c1, pm, force=not was_crossover)
            c2 = self._apply_mutation(c2, pm, force=not was_crossover)
            
            if c1 is None or c2 is None:
                continue
            
            if self._is_similar(p1, c1) or self._is_similar(p2, c2):
                continue
            
            offs.extend([c1, c2])  
        
        offs = offs[:len(last_pop)]  
        
        offs_pop = Population(len(offs))
        offs_pop.population = offs
        return offs_pop
        
    def run(self, **kwargs):
        pop_size = int(kwargs.get("pop_size", self.DEFAULT_CONFIG['pop_size']))
        num_gen = int(kwargs.get("num_gen", self.DEFAULT_CONFIG['num_gen']))
        pc = float(kwargs.get("pc", self.DEFAULT_CONFIG['pc']))
        pm = float(kwargs.get("pm", self.DEFAULT_CONFIG['pm']))
        
        logger.info("Initializing population (Generation 0)...")
        self._init_pop(pop_size)
        
        logger.info(f"Calculating fitness for initial population of {self.pop.population_size} individuals...")
        self.pop.cal_fitness(self.evaluator, self.obj_extractor)
        
        logger.info("Classifing into fronts ...")
        self._classify_pop()
        
        for gen in range(1, num_gen + 1):
            logger.info(f"--- Starting Generation {gen}/{num_gen} ---")
            
            logger.info("Generating offspring population...")
            # Generate offsprings
            offs = self._gen_offs_each_epoch(self.pop.population, pc, pm)
            logger.info(f"Calculating fitness for offs population of {self.pop.population_size} individuals...")
            offs.cal_fitness(self.evaluator, self.obj_extractor)
        
            # Create new population
            logger.info("Performing survival selection...")
            self.pop.population = self.replacement_opr(population=self.pop.population, 
                                                       offspring_population=offs.population, 
                                                       target_size=pop_size)
        
            # 4. Phân loại quần thể mới cho thế hệ tiếp theo
            logger.info("Classifying new population...")
            self._classify_pop()
            logger.info(f"Generation {gen} classification complete. Pareto front size: {len(self.pareto_front)}")

        return self.pareto_front