# algorithms/structures/operators/replacement.py

import random
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Protocol, Tuple, Type

from app.state import SingletonNameable, Stateful

from ..pop import DominanceIndividual, Individual, IndividualType
from ..comparator import Comparator, DominateComparator, non_dominated_sorting, crowding_distance_assignment
import app.core.config as cfg

class ReplacementOperator(Stateful, SingletonNameable, Generic[IndividualType]):
    def __init__(self, ind_cls: Type[IndividualType]):
        self._random = random.Random(cfg.RANDOM_SEED)
        self.ind_cls = ind_cls

    @abstractmethod
    def __call__(self, 
                 population: List[IndividualType], 
                 offspring_population: List[IndividualType],
                 target_size: int) -> List[IndividualType]:
        """
        Chọn lọc các cá thể từ cha mẹ và con cái để tạo ra thế hệ tiếp theo.

        Args:
            population (List[Individual]): Quần thể cha mẹ.
            offspring_population (List[Individual]): Quần thể con cái.
            target_size (int): Kích thước mục tiêu của quần thể mới.

        Returns:
            List[Individual]: Quần thể thế hệ tiếp theo.
        """
        pass
    
    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {
            'random_state': self._random.getstate()
        }
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self._random.setstate(fallback_state['random_state'])

class NSGA2ReplacementOperator(ReplacementOperator[DominanceIndividual]):
    """
    Thực hiện chọn lọc sinh tồn đầy đủ theo thuật toán NSGA-II.
    Đây là phương pháp được khuyến nghị.
    """
    def __init__(self, comparator: DominateComparator):
        super().__init__(ind_cls=DominanceIndividual)
        self.comparator = comparator
    
    def __call__(self, 
                 population: List[DominanceIndividual], 
                 offspring_population: List[DominanceIndividual],
                 target_size: int) -> List[DominanceIndividual]:
        
        # 1. Gộp quần thể cha mẹ và con cái
        combined_population = population + offspring_population

        # 2. Phân loại toàn bộ quần thể gộp
        fronts = non_dominated_sorting(combined_population, dominate_comparator=self.comparator)

        # 3. Xây dựng thế hệ tiếp theo
        next_generation: List[DominanceIndividual] = []
        for front in fronts:
            # Nếu thêm cả mặt trận này vào vẫn chưa đủ...
            if len(next_generation) + len(front) <= target_size:
                next_generation.extend(front)
            else:
                # Đây là mặt trận cuối cùng được thêm vào một phần
                # Tính toán crowding distance CHỈ cho mặt trận này
                crowding_distance_assignment(front)
                
                # Sắp xếp mặt trận này theo crowding distance giảm dần
                front.sort(key=lambda ind: ind.crowding_distance, reverse=True)
                
                # Lấy số lượng cá thể cần thiết để lấp đầy
                num_needed = target_size - len(next_generation)
                next_generation.extend(front[:num_needed])
                break # Đã đủ, thoát khỏi vòng lặp
        
        return next_generation