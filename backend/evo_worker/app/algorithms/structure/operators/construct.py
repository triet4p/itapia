import random
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List

from ..pop import Individual
import app.core.config as cfg

from itapia_common.rules.rule import Rule
from itapia_common.rules.nodes import _TreeNode
from itapia_common.rules.nodes.registry import get_spec_ent, get_operators_by_type, get_terminals_by_type, create_node
from itapia_common.schemas.entities.rules import RuleStatus, SemanticType

class InitOperator(ABC):
    
    def __init__(self, purpose: SemanticType):
        # Kiểm tra chặt chẽ hơn
        self.final_purposes = {
            SemanticType.DECISION_SIGNAL, 
            SemanticType.OPPORTUNITY_RATING, 
            SemanticType.RISK_LEVEL
        }
        self.purpose = purpose
    
        # Sử dụng instance Random riêng để đảm bảo khả năng tái tạo
        self._random = random.Random(cfg.RANDOM_SEED)
        
    @abstractmethod
    def __call__(self) -> Individual:
        pass
    
class RandomMaxDepthInitOperator(InitOperator):
    def __init__(self, purpose: SemanticType, max_depth: int = 5):
        super().__init__(purpose)
        if max_depth < 1:
            raise ValueError("Max depth must be at least 1.")
        self.max_depth = max_depth
                
        # Lấy danh sách các node đã được tiền xử lý
        self.terminals_by_type: Dict[SemanticType, List[str]] = get_terminals_by_type()
        self.operators_by_type: Dict[SemanticType, List[str]] = get_operators_by_type()
    
        # 1. Lấy tập hợp tất cả các kiểu có terminal tương ứng
        self.types_with_terminals = set(self.terminals_by_type.keys())
        
        # 2. Tạo ra các danh sách con an toàn cho các kiểu trừu tượng
        self.safe_concreates_for_any = tuple(
            t for t in SemanticType.ANY.concreates 
            if t in self.types_with_terminals
        )
        self.safe_concreates_for_any_numeric = tuple(
            t for t in SemanticType.ANY_NUMERIC.concreates
            if t in self.types_with_terminals
        )
        
        # Kiểm tra để đảm bảo không có lỗi cấu hình
        if not self.safe_concreates_for_any or not self.safe_concreates_for_any_numeric:
            raise RuntimeError("Configuration error: No valid concrete types with terminals found for ANY or ANY_NUMERIC.")
        
    def _get_concrete_type(self, required_type: SemanticType) -> SemanticType:
        """
        Nếu kiểu yêu cầu là trừu tượng, trả về một kiểu con cụ thể và an toàn (có terminal).
        """
        # Sử dụng các danh sách đã được tính toán trước
        if required_type == SemanticType.ANY:
            return self._random.choice(self.safe_concreates_for_any)
        if required_type == SemanticType.ANY_NUMERIC:
            return self._random.choice(self.safe_concreates_for_any_numeric)
            
        # Nếu không, trả về chính nó (đã là kiểu cụ thể)
        return required_type
        
    def _grow_tree(self, current_depth: int, required_type: SemanticType) -> _TreeNode:
        """
        Hàm đệ quy cốt lõi để xây dựng cây một cách ngẫu nhiên.
        """
        is_max_depth = current_depth >= self.max_depth
        specific_operators = self.operators_by_type.get(required_type, [])
        any_return_operators = self.operators_by_type.get(SemanticType.ANY, []) if current_depth > 1 else []
        any_numeric_return_operators = self.operators_by_type.get(SemanticType.ANY_NUMERIC, []) if current_depth > 1 else []

        possible_operators = specific_operators + any_return_operators + any_numeric_return_operators
        
        has_operators = len(possible_operators) > 0
        
        # Quyết định có tạo terminal hay không
        # Phải tạo terminal nếu: ở độ sâu tối đa HOẶC không có operator nào phù hợp
        # Nếu không, có xác suất `INIT_TERMINAL_PROB` để tạo terminal
        if is_max_depth or not has_operators or (current_depth > 1 and self._random.random() < cfg.INIT_TERMINAL_PROB):
            # --- Tạo một Terminal Node (nút lá) ---
            concreate_type = self._get_concrete_type(required_type)
            possible_terminals = self.terminals_by_type.get(concreate_type)
        
            if not possible_terminals:
                raise ValueError(f"Could not find a terminal for required type '{required_type}' at depth {current_depth}.")
            
            terminal_name = self._random.choice(possible_terminals)
            return create_node(terminal_name)
        else:
            # --- Tạo một Operator Node (nút trong) ---
            op_name = self._random.choice(possible_operators)
            op_spec = get_spec_ent(op_name)
            
            # Xử lý các tham số
            args_types = list(op_spec.args_type)
            resolved_types: Dict[SemanticType, SemanticType] = {}
            
            for arg_type in set(args_types):
                if arg_type.concreates:
                    if op_spec.return_type == arg_type:
                        resolved_types[arg_type] = required_type
                    else:
                        resolved_types[arg_type] = self._get_concrete_type(arg_type)
                
            final_args_type = [resolved_types.get(t, t) for t in args_types]
            
            children = [
                self._grow_tree(current_depth + 1, child_type)
                for child_type in final_args_type
            ]
            
            return create_node(op_name, children=children)
        
    def __call__(self) -> Individual:
        root = self._grow_tree(current_depth=1, required_type=self.purpose)
        
        random_id = uuid.uuid4().hex
        
        new_rule = Rule(
            root=root,
            rule_id=f'evo_{random_id}',
            name=f'Evolved Rule {random_id}',
            description='An automatically generated rule by the evolution algorithm.',
            rule_status=RuleStatus.EVOLVING
        )
        
        ind = Individual()
        ind.chromosome = new_rule
        
        return ind