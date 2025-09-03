from abc import ABC, abstractmethod
import copy
import random
from typing import Any, Dict, Generic, List, Optional, Protocol, Tuple, Type
import uuid

from app.state import SingletonNameable, Stateful
from itapia_common.rules.nodes import _TreeNode

from ..pop import Individual, IndividualType
import app.core.config as cfg

from ..utils import get_all_nodes, get_effective_type, get_nodes_by_effective_type, replace_node

class CrossoverOperator(Stateful, SingletonNameable, Generic[IndividualType]):
    
    def __init__(self, ind_cls: Type[IndividualType], new_rule_name_prefix: Optional[str] = None):
        # Sử dụng instance Random riêng để đảm bảo khả năng tái tạo
        self._random = random.Random(cfg.RANDOM_SEED)
        self.new_rule_name_prefix = new_rule_name_prefix if new_rule_name_prefix else uuid.uuid4().hex
        self.ind_cls = ind_cls
    
    @abstractmethod
    def __call__(self, ind1: IndividualType, ind2: IndividualType) -> Tuple[IndividualType, IndividualType] | None:
        """
        Recombined to individuals and return exactly 2 offsprings.

        Args:
            ind1 (Individual): Parent 1.
            ind2 (Individual): Parent 2.

        Returns:
            Tuple[Individual, Individual]: Two offsprings.
        """
        pass
    
    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {
            'random_state': self._random.getstate()
        }
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self._random.setstate(fallback_state['random_state'])
        
class SubtreeCrossoverOperator(CrossoverOperator[IndividualType]):
    
    def __call__(self, ind1: IndividualType, ind2: IndividualType) -> Tuple[IndividualType, IndividualType] | None:
        # 1. Tạo bản sao sâu (deep copy) để không làm thay đổi cha mẹ gốc
        if not (type(ind1) is self.ind_cls):
            raise TypeError('Individual must be same type as init.')
        if not (type(ind2) is self.ind_cls):
            raise TypeError('Individual must be same type as init.')
        
        offspring1_rule = copy.deepcopy(ind1.chromosome)
        offspring2_rule = copy.deepcopy(ind2.chromosome)

        # 2. Thu thập thông tin về các nút có thể lai ghép
        parent1_nodes_by_type = get_nodes_by_effective_type(offspring1_rule.root)
        parent2_nodes_by_type = get_nodes_by_effective_type(offspring2_rule.root)
        
        # 3. Tìm các kiểu chung mà cả hai cha mẹ đều có
        common_types = set(parent1_nodes_by_type.keys()) & set(parent2_nodes_by_type.keys())
        common_types.discard(offspring1_rule.root.return_type)
        
        if not common_types:
            # Nếu không có điểm chung nào, không thể lai ghép. Trả về none để báo.
            return None
        
        crossover_type = self._random.choice(list(common_types))
        
        point1 = self._random.choice(parent1_nodes_by_type[crossover_type])
        point2 = self._random.choice(parent2_nodes_by_type[crossover_type])
        
        # 5. Thực hiện phép trao đổi
        # Để tránh các vấn đề phức tạp, chúng ta sẽ tạo một bản sao của các điểm trao đổi
        # trước khi thực hiện thay thế.
        
        subtree1 = copy.deepcopy(point1)
        subtree2 = copy.deepcopy(point2)

        # Tạo Đứa con 1: Cây của Cha mẹ 1 + nhánh cây của Cha mẹ 2
        replace_node(offspring1_rule.root, point1, subtree2)
        
        # Tạo Đứa con 2: Cây của Cha mẹ 2 + nhánh cây của Cha mẹ 1
        replace_node(offspring2_rule.root, point2, subtree1)
        
        offspring1_rule.auto_id_name(self.new_rule_name_prefix)
        offspring2_rule.auto_id_name(self.new_rule_name_prefix)

        # 6. Tạo và trả về các đối tượng Individual con
        return self.ind_cls.from_rule(offspring1_rule), self.ind_cls.from_rule(offspring2_rule)

class OnePointCrossoverOperator(CrossoverOperator[IndividualType]):
    def _find_common_points(self, node1: _TreeNode, node2: _TreeNode) -> List[Tuple[_TreeNode, _TreeNode]]:
        """
        Hàm đệ quy để tìm tất cả các cặp nút ở cùng vị trí và có cùng kiểu.
        """
        common_points = []
        
        # Điều kiện để một cặp là "chung":
        # - Cùng kiểu trả về
        # - Cùng là OperatorNode HOẶC cùng là loại TerminalNode khác
        # - Nếu là Operator, phải có cùng số lượng con
        
        are_operators = hasattr(node1, 'children') and hasattr(node2, 'children')
        
        if get_effective_type(node1) == get_effective_type(node2):
            # Kiểm tra xem chúng có cùng cấu trúc cơ bản không
            if are_operators and len(node1.children) == len(node2.children):
                common_points.append((node1, node2))
                # Đệ quy tìm kiếm trong các cặp con tương ứng
                for child1, child2 in zip(node1.children, node2.children):
                    common_points.extend(self._find_common_points(child1, child2))
            elif not are_operators:
                # Nếu cả hai đều là nút lá và cùng kiểu, chúng là một điểm chung
                common_points.append((node1, node2))

        return common_points
    
    def __call__(self, ind1: IndividualType, ind2: IndividualType) -> Tuple[IndividualType, IndividualType] | None:
        if not (type(ind1) is self.ind_cls):
            raise TypeError('Individual must be same type as init.')
        if not (type(ind2) is self.ind_cls):
            raise TypeError('Individual must be same type as init.')
        
        offspring1_rule = copy.deepcopy(ind1.chromosome)
        offspring2_rule = copy.deepcopy(ind2.chromosome)

        # 1. Tìm tất cả các cặp điểm chung có thể lai ghép
        common_points = self._find_common_points(offspring1_rule.root, offspring2_rule.root)
        
        if not common_points:
            # Nếu không có điểm chung, trả về None
            return None

        # 2. Chọn ngẫu nhiên một cặp điểm chung để trao đổi
        point1, point2 = self._random.choice(common_points)
        
        # 3. Thực hiện phép trao đổi
        subtree1 = copy.deepcopy(point1)
        subtree2 = copy.deepcopy(point2)
        
        replace_node(offspring1_rule.root, point1, subtree2)
        replace_node(offspring2_rule.root, point2, subtree1)
        
        offspring1_rule.auto_id_name(self.new_rule_name_prefix)
        offspring2_rule.auto_id_name(self.new_rule_name_prefix)

        # 6. Tạo và trả về các đối tượng Individual con
        return self.ind_cls.from_rule(offspring1_rule), self.ind_cls.from_rule(offspring2_rule)