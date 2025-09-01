# algorithms/structures/tree_utils.py

import copy
import random
from typing import List, Set, Tuple, Dict

from itapia_common.rules.nodes import _TreeNode
from itapia_common.rules.nodes.registry import create_node, get_spec_ent
from itapia_common.schemas.entities.rules import SemanticType
import app.core.config as cfg

_random = random.Random(cfg.RANDOM_SEED)

def get_all_nodes(root: _TreeNode) -> List[_TreeNode]:
    """
    Duyệt cây theo thứ tự trước (pre-order) và trả về một danh sách
    phẳng chứa tất cả các nút trong cây.
    """
    nodes = [root]
    if hasattr(root, 'children') and root.children:
        for child in root.children:
            nodes.extend(get_all_nodes(child))
    return nodes

def get_effective_type(node: _TreeNode) -> SemanticType:
    """
    Xác định kiểu dữ liệu hiệu quả (concrete type) mà một nút hoặc nhánh cây sẽ trả về.
    Đây là hàm đệ quy để xử lý các kiểu đa hình như ANY và ANY_NUMERIC.
    """
    # 1. Trường hợp cơ sở: Nếu kiểu khai báo đã là cụ thể, trả về nó.
    declared_type = node.return_type
    if declared_type not in {SemanticType.ANY, SemanticType.ANY_NUMERIC}:
        return declared_type

    # 2. Trường hợp đệ quy: Kiểu khai báo là đa hình.
    if not hasattr(node, 'children') or not node.children:
        # Nút đa hình không có con (không nên xảy ra trong cây hợp lệ)
        # Trả về kiểu khai báo như một giải pháp an toàn.
        return declared_type
    
    index_to_check = -1
    for idx, arg_type in enumerate(node.args_type):
        if arg_type in {SemanticType.ANY, SemanticType.ANY_NUMERIC}:
            index_to_check = idx
            break

    # Với các toán tử đa hình, kiểu hiệu quả được quyết định bởi kiểu hiệu quả
    # của các nhánh con của nó. Ta có thể khái quát hóa bằng cách lấy kiểu
    # hiệu quả của đứa con đầu tiên (vì các con phải có cùng kiểu hiệu quả).
    return get_effective_type(node.children[index_to_check])

def get_nodes_by_effective_type(root: _TreeNode) -> Dict[SemanticType, List[_TreeNode]]:
    """
    Duyệt cây và trả về một dictionary nhóm tất cả các nút theo KIỂU HIỆU QUẢ của chúng.
    Đây là hàm được Crossover sử dụng để đảm bảo tính an toàn ngữ nghĩa.
    """
    nodes_by_type = {}
    all_nodes = get_all_nodes(root)
    for node in all_nodes:
        effective_type = get_effective_type(node)
        # Chỉ nhóm các kiểu cụ thể, bỏ qua các kiểu trừu tượng
        if effective_type not in {SemanticType.ANY, SemanticType.ANY_NUMERIC}:
            nodes_by_type.setdefault(effective_type, []).append(node)
    return nodes_by_type
    
def replace_node(root: _TreeNode, old_node: _TreeNode, new_node: _TreeNode) -> _TreeNode:
    """
    Tìm và thay thế một nút (`old_node`) bằng một nút mới (`new_node`) trong cây.
    Trả về gốc của cây mới. Thao tác này thay đổi cây ban đầu.
    """
    if root is old_node:
        return new_node
    
    if hasattr(root, 'children') and root.children:
        for i, child in enumerate(root.children):
            if child is old_node:
                # Tạo một list mới của children với nút đã được thay thế
                root.children = root.children[:i] + [new_node] + root.children[i+1:]
                return root # Trả về gốc sau khi đã thay đổi
            else:
                # Đệ quy tìm kiếm trong các cây con
                replace_node(child, old_node, new_node)
    return root

def get_concreate_type(required_type: SemanticType,
                       random_ins: random.Random,
                       available_types: Set[SemanticType]) -> SemanticType:
    # Sử dụng các danh sách đã được tính toán trước
    if not required_type.concreates:
        return required_type
    
    safe_concreate_types = tuple(
        t for t in required_type.concreates
        if t in available_types
    )
    
    if not safe_concreate_types:
        raise TypeError('Not exist any safe concreate types.')
    
    return random_ins.choice(safe_concreate_types)

def grow_tree(current_depth: int, 
              max_depth: int,
              operators_by_type: Dict[SemanticType, List[str]],
              terminals_by_type: Dict[SemanticType, List[str]],
              required_type: SemanticType,
              random_ins: random.Random,
              ) -> _TreeNode:
    """
    Hàm đệ quy cốt lõi để xây dựng cây một cách ngẫu nhiên.
    """
    is_max_depth = current_depth >= max_depth
    specific_operators = operators_by_type.get(required_type, [])
    any_return_operators = operators_by_type.get(SemanticType.ANY, []) if current_depth > 1 else []
    any_numeric_return_operators = operators_by_type.get(SemanticType.ANY_NUMERIC, []) if current_depth > 1 else []

    possible_operators = specific_operators + any_return_operators + any_numeric_return_operators
    
    has_operators = len(possible_operators) > 0
    
    available_types = set(terminals_by_type.keys())
    
    # Quyết định có tạo terminal hay không
    # Phải tạo terminal nếu: ở độ sâu tối đa HOẶC không có operator nào phù hợp
    # Nếu không, có xác suất `INIT_TERMINAL_PROB` để tạo terminal
    if is_max_depth or not has_operators or (current_depth > 1 and random_ins.random() < cfg.INIT_TERMINAL_PROB):
        # --- Tạo một Terminal Node (nút lá) ---
        concreate_type = get_concreate_type(required_type, random_ins, available_types)
        possible_terminals = terminals_by_type.get(concreate_type)
    
        if not possible_terminals:
            raise ValueError(f"Could not find a terminal for required type '{required_type}' at depth {current_depth}.")
        
        terminal_name = random_ins.choice(possible_terminals)
        return create_node(terminal_name)
    else:
        # --- Tạo một Operator Node (nút trong) ---
        op_name = random_ins.choice(possible_operators)
        op_spec = get_spec_ent(op_name)
        
        # Xử lý các tham số
        args_types = list(op_spec.args_type)
        resolved_types: Dict[SemanticType, SemanticType] = {}
        
        for arg_type in set(args_types):
            if arg_type.concreates:
                if op_spec.return_type == arg_type:
                    resolved_types[arg_type] = required_type
                else:
                    resolved_types[arg_type] = get_concreate_type(arg_type, random_ins, available_types)
            
        final_args_type = [resolved_types.get(t, t) for t in args_types]
        
        children = [
            grow_tree(current_depth=current_depth + 1, 
                      max_depth=max_depth,
                      operators_by_type=operators_by_type,
                      terminals_by_type=terminals_by_type,
                      required_type=child_type,
                      random_ins=random_ins)
            for child_type in final_args_type
        ]
        
        return create_node(op_name, children=children)