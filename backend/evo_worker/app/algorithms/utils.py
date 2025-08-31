# algorithms/structures/tree_utils.py

import copy
import random
from typing import List, Tuple, Dict

from itapia_common.rules.nodes import _TreeNode
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