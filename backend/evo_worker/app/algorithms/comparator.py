import math
from typing import List, Dict, Tuple
from abc import ABC, abstractmethod
from .pop import DominanceIndividual, Individual

class Comparator(ABC):
    
    @abstractmethod
    def __call__(self, ind1: Individual, ind2: Individual) -> bool: 
        """ 
        Return `True` if ind1 "better" ind2 
        """
        pass

class DominateComparator(Comparator):
    
    @abstractmethod
    def __call__(self, ind1: DominanceIndividual, ind2: DominanceIndividual) -> bool: 
        """ 
        Return `True` if ind1 "dominate" ind2 
        """
        pass
    
class FixedDominateComparator(DominateComparator):
    
    def __call__(self, ind1: DominanceIndividual, ind2: DominanceIndividual) -> bool:
        """
        Kiểm tra xem cá thể 1 (ind1) có trội hơn (dominate) cá thể 2 (ind2) hay không.

        Một cá thể `p` trội hơn `q` nếu:
        1. `p` không tệ hơn `q` ở bất kỳ mục tiêu nào.
        2. `p` tốt hơn `q` ở ít nhất một mục tiêu.

        Args:
            ind1 (Individual): Cá thể p.
            ind2 (Individual): Cá thể q.

        Returns:
            bool: True nếu ind1 trội hơn ind2, ngược lại là False.
        """
        if not isinstance(ind1.fitness, tuple):
            return ind1.fitness > ind2.fitness
        is_better_in_one = False
        for f1, f2 in zip(ind1.fitness, ind2.fitness):
            if f1 < f2:
                return False
            if f1 > f2:
                is_better_in_one = True
                
        return is_better_in_one
    
class RankAndCrowdingComparator(DominateComparator):
    def __call__(self, ind1: DominanceIndividual, ind2: DominanceIndividual):
        if ind1.rank < 0 or ind2.rank < 0:
            raise ValueError("Individuals must be ranked!")
        if ind1.rank > ind2.rank:
            return True
        if ind1.rank < ind2.rank:
            return False
        return ind1.crowding_distance > ind2.crowding_distance
    
class EpsilonBoxDominateComparator(DominateComparator):
    """
    So sánh hai cá thể dựa trên khái niệm Epsilon-Box Dominance.
    Lượng tử hóa không gian mục tiêu thành một lưới các "hộp" và so sánh
    vị trí của các cá thể trên lưới đó.
    """
    def __init__(self, epsilons: Tuple[float, ...]):
        """
        Khởi tạo comparator với một vector epsilon.

        Args:
            epsilons (Tuple[float, ...]): Một tuple các giá trị epsilon,
                                         mỗi giá trị cho một mục tiêu tương ứng.
                                         Độ dài phải bằng số lượng mục tiêu.
        """
        if not all(e > 0 for e in epsilons):
            raise ValueError("All epsilon values must be positive.")
        self.epsilons = epsilons

    def __call__(self, ind1: DominanceIndividual, ind2: DominanceIndividual) -> bool:
        """ 
        Trả về True nếu ind1 ε-trội hơn ind2.
        """
        if not isinstance(ind1.fitness, tuple):
            # Nếu là đơn mục tiêu, epsilon không có ý nghĩa nhiều,
            # quay về so sánh thông thường.
            return ind1.fitness > ind2.fitness

        if len(ind1.fitness) != len(self.epsilons):
            raise ValueError(
                f"Mismatch between number of objectives ({len(ind1.fitness)}) "
                f"and number of epsilons ({len(self.epsilons)})."
            )

        # Chuyển đổi fitness của mỗi cá thể thành "tọa độ hộp"
        box1 = [math.floor(f / e) for f, e in zip(ind1.fitness, self.epsilons)]
        box2 = [math.floor(f / e) for f, e in zip(ind2.fitness, self.epsilons)]
        
        # Áp dụng Pareto dominance tiêu chuẩn trên "tọa độ hộp"
        is_better_in_one = False
        for b1, b2 in zip(box1, box2):
            if b1 < b2: # Tọa độ hộp của ind1 thấp hơn -> không thể trội hơn
                return False
            if b1 > b2: # Tọa độ hộp của ind1 cao hơn
                is_better_in_one = True
                
        return is_better_in_one

def non_dominated_sorting(inds: List[DominanceIndividual],
                          dominate_comparator: DominateComparator) -> List[List[DominanceIndividual]]:
    """
    Thực hiện thuật toán non-dominated sorting trên một quần thể.
    Phân loại các cá thể vào các "mặt trận" (fronts) không bị trội.

    Args:
        inds (List[Individual]): Quần thể cần được sắp xếp.

    Returns:
        List[List[Individual]]: Một danh sách các mặt trận (fronts).
                                Front đầu tiên (index 0) là tốt nhất.
    """
    
    domination_counts = {id(ind): 0 for ind in inds}
    dominated_sets = {id(ind): [] for ind in inds}
    fronts = [[]]
    
    ind_map = {id(ind): ind for ind in inds}
    
    # Lặp qua mọi cặp để tính toán quan hệ trội / bị trội
    for i in range(len(inds)):
        for j in range(i + 1, len(inds)):
            p = inds[i]
            q = inds[j]
            
            if dominate_comparator(p, q):
                dominated_sets[id(p)].append(id(q))
                domination_counts[id(q)] += 1
            elif dominate_comparator(q, p):
                dominated_sets[id(q)].append(id(p))
                domination_counts[id(p)] += 1
                
    # Tìm front đầu tiên (F1)
    for ind_id, cnt in domination_counts.items():
        if cnt == 0:
            fronts[0].append(ind_map[ind_id])
            ind_map[ind_id].rank = 0
            
    # Xây các front tiếp
    front_idx = 0
    while fronts[front_idx]:
        next_front = []
        for p_ind in fronts[front_idx]:
            for q_id in dominated_sets[id(p_ind)]:
                domination_counts[q_id] -= 1
                
                if domination_counts[q_id] == 0:
                    next_front.append(ind_map[q_id])
                    ind_map[q_id].rank = front_idx + 1
                    
        front_idx += 1
        
        if next_front:
            fronts.append(next_front)
        else:
            break
    
    return fronts

def crowding_distance_assignment(front: List[DominanceIndividual]) -> None:
    """
    Tính toán và gán crowding distance cho mỗi cá thể trong một mặt trận.
    Hàm này sửa đổi các cá thể tại chỗ (in-place) bằng cách thêm thuộc tính
    `crowding_distance`.

    Args:
        front (List[Individual]): Một mặt trận duy nhất (một danh sách các cá thể).
    """
    
    if not front:
        return
    
    num_inds = len(front)
    num_objs = len(front[0].fitness)
    
    for ind in front:
        ind.crowding_distance = 0.0
        
    for m in range(num_objs):
        front.sort(key=lambda ind: ind.fitness[m])
        
        min_val = front[0].fitness[m]
        max_val = front[-1].fitness[m]
        
        front[0].crowding_distance = float('inf')
        front[-1].crowding_distance = float('inf')
        
        if max_val == min_val or num_inds <= 2:
            return
        
        for i in range(1, num_inds - 1):
            distance = front[i + 1].fitness[m] - front[i - 1].fitness[m]
            normalized_distance = distance / (max_val - min_val)
            
            front[i].crowding_distance += normalized_distance