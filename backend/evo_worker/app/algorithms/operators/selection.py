# algorithms/structures/operators/selection.py

import random
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, List, Protocol, Tuple, Type

from ..objective import AcceptedObjective
from app.state import SingletonNameable, Stateful

from ..pop import IndividualType
from ..comparator import Comparator # Import hàm tiện ích
import app.core.config as cfg

class SelectionOperator(Stateful, SingletonNameable, Generic[IndividualType]):
    def __init__(self, ind_cls: Type[IndividualType]):
        self._random = random.Random(cfg.RANDOM_SEED)
        self.ind_cls = ind_cls

    @abstractmethod
    def __call__(self, population: List[IndividualType], num_selections: int) -> List[IndividualType]:
        """
        Chọn ra một số lượng cá thể từ quần thể để làm cha mẹ.

        Args:
            population (List[Individual]): Quần thể hiện tại.
            num_selections (int): Số lượng cha mẹ cần chọn.

        Returns:
            List[Individual]: Danh sách các cha mẹ đã được chọn.
        """
        pass
    
    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {
            'random_state': self._random.getstate()
        }
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self._random.setstate(fallback_state['random_state'])

class TournamentSelectionOperator(SelectionOperator[IndividualType]):
    """
    Thực hiện chọn lọc giải đấu dựa trên quan hệ trội và crowding distance.
    Đây là phương pháp chọn lọc tiêu chuẩn cho NSGA-II.
    """
    def __init__(self, ind_cls: Type[IndividualType], comparator: Comparator, k: int = 4):
        super().__init__(ind_cls)
        if k < 2:
            raise ValueError("Tournament size (k) must be at least 2.")
        self.k = k
        self.comparator = comparator

    def __call__(self, population: List[IndividualType], num_selections: int) -> List[IndividualType]:
        selected_parents: List[IndividualType] = []
        pop_size = len(population)

        if pop_size == 0:
            return []

        for _ in range(num_selections):
            # 1. Chọn ngẫu nhiên k "đấu sĩ" từ quần thể
            tournament_contenders = self._random.sample(population, self.k)
            
            # 2. Tìm ra người chiến thắng
            winner = tournament_contenders[0]
            for i in range(1, self.k):
                if self.comparator(tournament_contenders[i], winner):
                    winner = tournament_contenders[i]
            
            selected_parents.append(winner)
            
        return selected_parents

class RouletteWheelSelectionOperator(SelectionOperator[IndividualType]):
    """
    Thực hiện chọn lọc bánh xe Roulette.
    Lưu ý: Phương pháp này thường không phù hợp với tối ưu hóa đa mục tiêu
    vì nó yêu cầu một giá trị fitness vô hướng duy nhất.
    """
    def __init__(self, ind_cls: Type[IndividualType], fitness_score_mapper: Callable[[AcceptedObjective], float]):
        super().__init__(ind_cls)
        self.fitness_score_mapper = fitness_score_mapper
    
    def __call__(self, population: List[IndividualType], num_selections: int) -> List[IndividualType]:
        # Để Roulette Wheel hoạt động, chúng ta cần chuyển đổi rank đa mục tiêu
        # thành một "điểm số" vô hướng duy nhất.
        # Một cách phổ biến là dùng rank làm điểm số chính.
        
        # Gán "điểm" dựa trên rank, rank càng thấp điểm càng cao.
        # Ví dụ: rank 0 -> điểm N, rank 1 -> điểm N-1, ...
        scores = [self.fitness_score_mapper(ind.fitness) for ind in population]
        total_score = sum(scores)

        if total_score == 0:
             # Nếu tất cả đều có điểm 0, chọn ngẫu nhiên
            return self._random.sample(population, k=num_selections)

        selected_parents = []
        for _ in range(num_selections):
            pick = self._random.uniform(0, total_score)
            current = 0
            for ind, score in zip(population, scores):
                current += score
                if current > pick:
                    selected_parents.append(ind)
                    break
        
        return selected_parents