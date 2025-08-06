# itapia_common/rules/serializer.py

from typing import Dict, Any, List

# Import các lớp Node để kiểm tra kiểu
from .nodes import _TreeNode, ConstantNode, VarNode, OperatorNode
from .nodes.registry import create_node
from itapia_common.schemas.entities.rules import NodeEntity

def serialize_tree(node: _TreeNode) -> NodeEntity:
    """
    Chuyển đổi (serialize) một cây Node (bắt đầu từ node gốc) thành một cấu trúc dictionary lồng nhau.
    Hàm này hoạt động theo kiểu đệ quy.

    Args:
        node (_TreeNode): Node gốc của cây hoặc nhánh cây cần chuyển đổi.

    Returns:
        Dict[str, Any]: Một dictionary đại diện cho cây.
    """
    if not isinstance(node, _TreeNode):
        raise TypeError("Đầu vào phải là một thể hiện của _TreeNode.")

    # Tạo dictionary cơ bản
    # Lưu ý: node.node_name đã được .upper() trong constructor
    node_name = node.node_name
    node_children = None
    
    # Nếu là một Operator, đệ quy serialize các con của nó
    if isinstance(node, OperatorNode):
        if node.children: # Chỉ thêm key 'children' nếu có
            node_children = [serialize_tree(child) for child in node.children]
            
    # Các loại node khác (Constant, Var) không có 'children' hay tham số đặc biệt
    # nên không cần làm gì thêm. Tên của chúng (node_name) đã đủ để tái tạo lại.

    return NodeEntity(node_name=node_name, children=node_children)

def parse_tree(data: NodeEntity) -> _TreeNode:
    """
    Phân tích (parse) một cấu trúc dictionary và tái tạo lại một cây Node hoàn chỉnh.
    Hàm này hoạt động theo kiểu đệ quy và sử dụng Node Factory.

    Args:
        data (Dict[str, Any]): Dictionary đại diện cho một node (và các con của nó).

    Returns:
        _TreeNode: Node gốc của cây hoặc nhánh cây đã được tái tạo.
    """
    node_name = data.node_name

    # Chuẩn bị các tham số sẽ được truyền vào factory
    # Đây là các tham số động, không được định nghĩa sẵn trong Spec
    factory_kwargs: Dict[str, Any] = {}

    # 1. Đệ quy parse các node con trước (nếu có)
    if data.children is not None:
        children_data = data.children
        if not isinstance(children_data, list):
            raise TypeError("'children' phải là một danh sách.")
        
        # Tái tạo lại từng node con và thêm vào kwargs
        factory_kwargs["children"] = [parse_tree(child_data) for child_data in children_data]
        
    # Thêm các tham số đặc biệt khác ở đây nếu có...

    # 3. Gọi Node Factory để tạo node hiện tại
    # node_name của một node trong cây sẽ được tự tạo hoặc có thể lấy từ dict nếu muốn
    # Ở đây, ta đơn giản hóa bằng cách dùng chính node_name
    try:
        # Nhà máy sẽ sử dụng node_name để tra cứu Spec và dùng kwargs để truyền các tham số động
        node_instance = create_node(node_name=node_name, **factory_kwargs)
    except Exception as e:
        # Bọc lỗi gốc để cung cấp thêm ngữ cảnh khi debug
        raise ValueError(f"Lỗi khi tạo node với tên '{node_name}'. Lỗi gốc: {e}") from e

    return node_instance