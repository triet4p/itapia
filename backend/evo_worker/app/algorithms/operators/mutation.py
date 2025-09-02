from abc import ABC, abstractmethod
from copy import deepcopy
import random
from typing import Any, Dict, Generic, List, Optional, Type
import uuid

from app.state import SingletonNameable, Stateful
from itapia_common.rules.nodes import _TreeNode, OperatorNode
from itapia_common.rules.nodes.registry import get_spec_ent, create_node
from itapia_common.schemas.entities.rules import SemanticType

from ..pop import DominanceIndividual, Individual, IndividualType
from .construct import RandomMaxDepthInitOperator
import app.core.config as cfg

from ..utils import get_all_nodes, get_effective_type, get_nodes_by_effective_type, grow_tree, replace_node

class MutationOperator(Stateful, SingletonNameable, Generic[IndividualType]):
    
    def __init__(self, new_rule_name_prefix: Optional[str] = None):
        self._random = random.Random(cfg.RANDOM_SEED)
        self.new_rule_name_prefix = new_rule_name_prefix if new_rule_name_prefix else uuid.uuid4().hex
        
    @abstractmethod
    def __call__(self, ind: IndividualType) -> IndividualType | None:
        """
        Mutate an individual to create exactly one new individual.

        Args:
            ind (Individual): Need mutate individual

        Returns:
            Individual: Mutated individual
        """
        pass
    
    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {
            'random_state': self._random.getstate()
        }
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self._random.setstate(fallback_state['random_state'])
    
class SubtreeMutationOperator(MutationOperator[IndividualType]):
    def __init__(self, max_subtree_depth: int,
                 terminals_by_type: Dict[SemanticType, List[str]],
                 operators_by_type: Dict[SemanticType, List[str]],
                 new_rule_name_prefix: Optional[str] = None):
        super().__init__(new_rule_name_prefix)
        self.terminals_by_type = terminals_by_type
        self.operators_by_type = operators_by_type
        self.max_subtree_depth = max_subtree_depth
        # Sử dụng các kiểu được thay thế bởi ANY, 
        # vì phải đột biến ở các nút ko phải final purpose trả về (decision signal,...) 
        # mà là 1 purpose trung gian
        
    def __call__(self, ind: IndividualType) -> IndividualType | None:
        mutated_rule = deepcopy(ind.chromosome)
        
        # 1. Chọn một điểm đột biến ngẫu nhiên trong cây (không chọn gốc)
        all_nodes = get_all_nodes(mutated_rule.root)
        if len(all_nodes) <= 1:
            # Nếu cây chỉ có 1 nút, không thể đột biến, trả về bản sao
            return None

        mutation_point = self._random.choice(all_nodes[1:])
        
        # 2. Xác định kiểu hiệu quả cần thiết tại điểm đó
        required_type = get_effective_type(mutation_point)
        
        new_subtree = grow_tree(current_depth=1,
                                max_depth=self.max_subtree_depth,
                                operators_by_type=self.operators_by_type,
                                terminals_by_type=self.terminals_by_type,
                                required_type=required_type,
                                random_ins=self._random)
        
        replace_node(mutated_rule.root, mutation_point, new_subtree)
        
        mutated_rule.auto_id_name(self.new_rule_name_prefix)
        cls = type(ind)
        return cls.from_rule(mutated_rule)
    
class PointMutationOperator(MutationOperator[IndividualType]):
    
    def __init__(self, terminals_by_type: Dict[SemanticType, List[str]],
                 operators_by_type: Dict[SemanticType, List[str]],
                 new_rule_name_prefix: Optional[str] = None):
        super().__init__(new_rule_name_prefix)
        self.terminals_by_type = terminals_by_type
        self.operators_by_type = operators_by_type
    
    def __call__(self, ind: IndividualType) -> IndividualType | None:
        mutated_rule = deepcopy(ind.chromosome)
        all_nodes = get_all_nodes(mutated_rule.root)
        
        if not all_nodes:
            return None
        
        mutation_point = self._random.choice(all_nodes[1:])
        
        if isinstance(mutation_point, OperatorNode) and mutation_point.children:
            new_node = self._mutate_operator(mutation_point)
        else:
            new_node = self._mutate_terminal(mutation_point)
            
        if new_node is None:
            return None
        
        replace_node(mutated_rule.root, mutation_point, new_node)
        
        mutated_rule.auto_id_name(self.new_rule_name_prefix)
        cls = type(ind)
        return cls.from_rule(mutated_rule)
        
    
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
    def __init__(self, terminals_by_type: Dict[SemanticType, List[str]],
                 new_rule_name_prefix: Optional[str] = None):
        super().__init__(new_rule_name_prefix)
        self.terminals_by_type = terminals_by_type

    def __call__(self, ind: IndividualType) -> IndividualType:
        mutated_rule = deepcopy(ind.chromosome)
        all_nodes = get_all_nodes(mutated_rule.root)
        
        # Chỉ có thể "shrink" các nút không phải là lá
        shrinkable_nodes = [n for n in all_nodes[1:] if isinstance(n, OperatorNode) and n.children]
        
        if not shrinkable_nodes:
            return None
            
        mutation_point = self._random.choice(shrinkable_nodes)
        required_type = get_effective_type(mutation_point)
        
        # Tìm một terminal phù hợp để thay thế
        possible_terminals = self.terminals_by_type.get(required_type)
        if not possible_terminals:
            # Nếu không tìm thấy terminal thay thế, không làm gì cả
            return None
            
        new_terminal_name = self._random.choice(possible_terminals)
        
        new_terminal_node = create_node(new_terminal_name)
        
        # Thay thế toàn bộ nhánh cây tại điểm đột biến bằng nút terminal mới
        replace_node(mutated_rule.root, mutation_point, new_terminal_node)
        
        mutated_rule.auto_id_name(self.new_rule_name_prefix)
        cls = type(ind)
        return cls.from_rule(mutated_rule)