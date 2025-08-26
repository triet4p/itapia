from abc import ABC, abstractmethod
from copy import deepcopy
import random
from typing import Dict, List, Type
import uuid

from itapia_common.rules.nodes import _TreeNode, OperatorNode
from itapia_common.rules.nodes.registry import get_operators_by_type, get_terminals_by_type, get_spec_ent, create_node
from itapia_common.schemas.entities.rules import SemanticType

from ..pop import Individual
from .construct import RandomMaxDepthInitOperator
import app.core.config as cfg

from ..utils import get_all_nodes, get_effective_type, get_nodes_by_effective_type, replace_node

class MutationOperator(ABC):
    
    def __init__(self):
        self._random = random.Random(cfg.RANDOM_SEED)
        
    @abstractmethod
    def __call__(self, ind: Individual) -> Individual | None:
        """
        Mutate an individual to create exactly one new individual.

        Args:
            ind (Individual): Need mutate individual

        Returns:
            Individual: Mutated individual
        """
        pass
    
class SubtreeMutationOperator(MutationOperator):
    def __init__(self, max_subtree_depth: int,
                 init_opr_template: Type[RandomMaxDepthInitOperator]):
        super().__init__()
        self.init_oprs: Dict[SemanticType, RandomMaxDepthInitOperator] = {
            p: RandomMaxDepthInitOperator(purpose=p, max_depth=max_subtree_depth)
            for p in SemanticType.ANY.concreates
        }
        # Sử dụng các kiểu được thay thế bởi ANY, 
        # vì phải đột biến ở các nút ko phải final purpose trả về (decision signal,...) 
        # mà là 1 purpose trung gian
        
    def __call__(self, ind: Individual) -> Individual | None:
        mutated_rule = deepcopy(ind.chromosome)
        
        # 1. Chọn một điểm đột biến ngẫu nhiên trong cây (không chọn gốc)
        all_nodes = get_all_nodes(mutated_rule.root)
        if len(all_nodes) <= 1:
            # Nếu cây chỉ có 1 nút, không thể đột biến, trả về bản sao
            return None

        mutation_point = self._random.choice(all_nodes[1:])
        
        # 2. Xác định kiểu hiệu quả cần thiết tại điểm đó
        required_type = get_effective_type(mutation_point)
        
        init_opr = self.init_oprs.get(required_type)
        if init_opr is None:
            return None
        
        new_subtree = init_opr._grow_tree(current_depth=1, required_type=required_type)
        
        replace_node(mutated_rule.root, mutation_point, new_subtree)
        
        mutated_rule.rule_id = f'evo_{uuid.uuid4()}'
        return Individual.from_rule(mutated_rule)
    
class PointMutationOperator(MutationOperator):
    
    def __init__(self):
        super().__init__()
        self.terminals_by_type = get_terminals_by_type()
        self.operators_by_type = get_operators_by_type()
    
    def __call__(self, ind: Individual) -> Individual | None:
        mutated_rule = deepcopy(ind.chromosome)
        all_nodes = get_all_nodes(mutated_rule.root)
        
        if not all_nodes:
            return None
        
        mutation_point = self._random.choice(all_nodes[1:])
        print(mutation_point.node_name)
        
        if isinstance(mutation_point, OperatorNode) and mutation_point.children:
            new_node = self._mutate_operator(mutation_point)
        else:
            new_node = self._mutate_terminal(mutation_point)
            
        if new_node is None:
            return None
        
        replace_node(mutated_rule.root, mutation_point, new_node)
        
        mutated_rule.rule_id = f'evo_{uuid.uuid4()}'
        return Individual.from_rule(mutated_rule)
        
    
    def _mutate_operator(self, node: OperatorNode):
        """Thay thế một operator bằng một operator khác tương thích."""
        # Tìm các operator khác có cùng kiểu trả về và cùng số lượng tham số
        possible_replacements: List[str] = []
        for op_name in self.operators_by_type.get(node.return_type, []):
            spec = get_spec_ent(op_name)
            if len(spec.args_type) == node.num_child and op_name != node.node_name:
                possible_replacements.append(op_name)
        
        if possible_replacements:
            new_op_name = self._random.choice(possible_replacements)
            # Phải tạo node mới, children được truyền qua
            return create_node(new_op_name, children=node.children) 
            
        return None

    def _mutate_terminal(self, node: _TreeNode):
        """Thay thế một terminal bằng một terminal khác có cùng kiểu."""
        # Tìm các terminal khác có cùng kiểu trả về
        possible_replacements = [
            term_name for term_name in self.terminals_by_type.get(node.return_type, [])
            if term_name != node.node_name
        ]
        
        if possible_replacements:
            new_term_name = self._random.choice(possible_replacements)
            # Thay đổi tên và giá trị của nút
            # Đây là một sự đơn giản hóa. Một hệ thống hoàn chỉnh sẽ cần
            # một hàm `reinitialize_node(node, new_name)` để cập nhật tất cả
            # các thuộc tính (value, description, ...) từ spec mới.
            return create_node(node_name=new_term_name)
        return None
    
class ShrinkMutationOperator(MutationOperator):
    def __init__(self):
        super().__init__()
        self.terminals_by_type = get_terminals_by_type()

    def __call__(self, ind: Individual) -> Individual:
        mutated_rule = deepcopy(ind.chromosome)
        all_nodes = get_all_nodes(mutated_rule.root)
        
        # Chỉ có thể "shrink" các nút không phải là lá
        shrinkable_nodes = [n for n in all_nodes[1:] if isinstance(n, OperatorNode) and n.children]
        
        if not shrinkable_nodes:
            return None
            
        mutation_point = self._random.choice(shrinkable_nodes)
        print(mutation_point.node_name)
        required_type = get_effective_type(mutation_point)
        
        # Tìm một terminal phù hợp để thay thế
        possible_terminals = self.terminals_by_type.get(required_type)
        if not possible_terminals:
            # Nếu không tìm thấy terminal thay thế, không làm gì cả
            return None
            
        new_terminal_name = self._random.choice(possible_terminals)
        print(new_terminal_name)
        
        new_terminal_node = create_node(new_terminal_name)
        
        # Thay thế toàn bộ nhánh cây tại điểm đột biến bằng nút terminal mới
        replace_node(mutated_rule.root, mutation_point, new_terminal_node)
        
        mutated_rule.rule_id = f'evo_{uuid.uuid4()}'
        return Individual.from_rule(mutated_rule)