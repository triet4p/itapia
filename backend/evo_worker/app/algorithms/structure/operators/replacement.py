# algorithms/structures/operators/replacement.py

import random
from abc import ABC, abstractmethod
from typing import List, Tuple

from ..pop import Individual
from ..dominance import non_dominated_sorting, crowding_distance_assignment
import app.core.config as cfg

class ReplacementOperator(ABC):
    def __init__(self):
        self._random = random.Random(cfg.RANDOM_SEED)

    @abstractmethod
    def __call__(self, 
                 population: List[Individual], 
                 offspring_population: List[Individual],
                 target_size: int) -> List[Individual]:
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

class ElitismReplacementOperator(ReplacementOperator):
    """
    Thực hiện chọn lọc sinh tồn bằng phương pháp Elitism đơn giản, kết hợp
    với chọn lọc ngẫu nhiên để lấp đầy phần còn lại.

    Đây là một phương pháp đơn giản hơn so với NSGA-II đầy đủ.
    """
    def __init__(self, num_parent_elites: int, num_offspring_elites: int):
        super().__init__()
        self.k1 = num_parent_elites
        self.k2 = num_offspring_elites

    def __call__(self, 
                 population: List[Individual], 
                 offspring_population: List[Individual],
                 target_size: int) -> List[Individual]:
        
        next_generation: List[Individual] = []
        
        # Sắp xếp cha mẹ và con cái dựa trên rank và crowding distance
        # Để làm điều này, chúng ta cần chạy non_dominated_sorting trên từng nhóm
        
        # Gán rank và crowding distance cho cha mẹ
        parent_fronts = non_dominated_sorting(population)
        for i, front in enumerate(parent_fronts):
            for ind in front:
                ind.rank = i
            crowding_distance_assignment(front)

        # Gán rank và crowding distance cho con cái
        offspring_fronts = non_dominated_sorting(offspring_population)
        for i, front in enumerate(offspring_fronts):
            for ind in front:
                ind.rank = i
            crowding_distance_assignment(front)
            
        # Sắp xếp cả hai quần thể
        population.sort(key=lambda ind: (ind.rank, -ind.crowding_distance))
        offspring_population.sort(key=lambda ind: (ind.rank, -ind.crowding_distance))
        
        # 1. Chọn k1 cá thể cha mẹ tốt nhất
        parent_elites = population[:self.k1]
        next_generation.extend(parent_elites)

        # 2. Chọn k2 cá thể con cái tốt nhất
        offspring_elites = offspring_population[:self.k2]
        next_generation.extend(offspring_elites)
        
        # 3. Lấp đầy phần còn lại bằng cách chọn ngẫu nhiên
        remaining_slots = target_size - len(next_generation)
        if remaining_slots > 0:
            # Tạo một pool chứa tất cả các cá thể chưa được chọn
            combined_pool = [ind for ind in population if ind not in next_generation] + \
                            [ind for ind in offspring_population if ind not in next_generation]
            
            if len(combined_pool) < remaining_slots:
                # Nếu không đủ cá thể, lấy hết những gì còn lại
                next_generation.extend(combined_pool)
            else:
                # Chọn ngẫu nhiên từ pool
                random_fill = self._random.sample(combined_pool, remaining_slots)
                next_generation.extend(random_fill)
        
        return next_generation[:target_size]

class NSGA2ReplacementOperator(ReplacementOperator):
    """
    Thực hiện chọn lọc sinh tồn đầy đủ theo thuật toán NSGA-II.
    Đây là phương pháp được khuyến nghị.
    """
    def __call__(self, 
                 population: List[Individual], 
                 offspring_population: List[Individual],
                 target_size: int) -> List[Individual]:
        
        # 1. Gộp quần thể cha mẹ và con cái
        combined_population = population + offspring_population

        # 2. Phân loại toàn bộ quần thể gộp
        fronts = non_dominated_sorting(combined_population)

        # 3. Xây dựng thế hệ tiếp theo
        next_generation: List[Individual] = []
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