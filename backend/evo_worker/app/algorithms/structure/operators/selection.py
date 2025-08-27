# algorithms/structures/operators/selection.py

import random
from abc import ABC, abstractmethod
from typing import List, Tuple

from ..pop import Individual
from ..dominance import _is_is_dominates # Import hàm tiện ích
import app.core.config as cfg

class SelectionOperator(ABC):
    def __init__(self):
        self._random = random.Random(cfg.RANDOM_SEED)

    @abstractmethod
    def __call__(self, population: List[Individual], num_selections: int) -> List[Individual]:
        """
        Chọn ra một số lượng cá thể từ quần thể để làm cha mẹ.

        Args:
            population (List[Individual]): Quần thể hiện tại.
            num_selections (int): Số lượng cha mẹ cần chọn.

        Returns:
            List[Individual]: Danh sách các cha mẹ đã được chọn.
        """
        pass

class TournamentSelectionOperator(SelectionOperator):
    """
    Thực hiện chọn lọc giải đấu dựa trên quan hệ trội và crowding distance.
    Đây là phương pháp chọn lọc tiêu chuẩn cho NSGA-II.
    """
    def __init__(self, k: int = 4):
        super().__init__()
        if k < 2:
            raise ValueError("Tournament size (k) must be at least 2.")
        self.k = k

    def _is_better(self, ind1: Individual, ind2: Individual) -> bool:
        """
        So sánh hai cá thể dựa trên xếp hạng NSGA-II.
        Ưu tiên rank (mặt trận), sau đó là crowding distance.
        """
        if ind1.rank < ind2.rank: # Rank nhỏ hơn là tốt hơn
            return True
        if ind1.rank > ind2.rank:
            return False
        
        # Nếu rank bằng nhau, ưu tiên cá thể có crowding distance lớn hơn
        return ind1.crowding_distance > ind2.crowding_distance

    def __call__(self, population: List[Individual], num_selections: int) -> List[Individual]:
        selected_parents = []
        pop_size = len(population)

        if pop_size == 0:
            return []

        for _ in range(num_selections):
            # 1. Chọn ngẫu nhiên k "đấu sĩ" từ quần thể
            tournament_contenders = self._random.sample(population, self.k)
            
            # 2. Tìm ra người chiến thắng
            winner = tournament_contenders[0]
            for i in range(1, self.k):
                if self._is_better(tournament_contenders[i], winner):
                    winner = tournament_contenders[i]
            
            selected_parents.append(winner)
            
        return selected_parents

class RouletteWheelSelectionOperator(SelectionOperator):
    """
    Thực hiện chọn lọc bánh xe Roulette.
    Lưu ý: Phương pháp này thường không phù hợp với tối ưu hóa đa mục tiêu
    vì nó yêu cầu một giá trị fitness vô hướng duy nhất. 
    Đây là phiên bản được điều chỉnh để hoạt động với NSGA-II.
    """
    def __call__(self, population: List[Individual], num_selections: int) -> List[Individual]:
        # Để Roulette Wheel hoạt động, chúng ta cần chuyển đổi rank đa mục tiêu
        # thành một "điểm số" vô hướng duy nhất.
        # Một cách phổ biến là dùng rank làm điểm số chính.
        
        # Gán "điểm" dựa trên rank, rank càng thấp điểm càng cao.
        # Ví dụ: rank 0 -> điểm N, rank 1 -> điểm N-1, ...
        max_rank = max(ind.rank for ind in population)
        scores = [max_rank - ind.rank + 1 for ind in population]
        total_score = sum(scores)

        if total_score == 0:
             # Nếu tất cả đều có điểm 0, chọn ngẫu nhiên
            return self._random.choices(population, k=num_selections)

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