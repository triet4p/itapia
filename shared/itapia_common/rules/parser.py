# itapia_common/rules/serializer.py

from typing import Dict, Any, List

# Import các lớp Node để kiểm tra kiểu
from .nodes import _TreeNode, ConstantNode, VarNode, OperatorNode
from .nodes.registry import create_node

def serialize_tree_to_dict(node: _TreeNode) -> Dict[str, Any]:
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
    # Lưu ý: node.node_id đã được .upper() trong constructor
    node_dict: Dict[str, Any] = {
        "node_id": node.node_id,
    }
    
    # Nếu là một Operator, đệ quy serialize các con của nó
    if isinstance(node, OperatorNode):
        if node.children: # Chỉ thêm key 'children' nếu có
            node_dict["children"] = [serialize_tree_to_dict(child) for child in node.children]
            
    # Các loại node khác (Constant, Var) không có 'children' hay tham số đặc biệt
    # nên không cần làm gì thêm. Tên của chúng (node_id) đã đủ để tái tạo lại.

    return node_dict

def parse_tree_from_dict(data: Dict[str, Any]) -> _TreeNode:
    """
    Phân tích (parse) một cấu trúc dictionary và tái tạo lại một cây Node hoàn chỉnh.
    Hàm này hoạt động theo kiểu đệ quy và sử dụng Node Factory.

    Args:
        data (Dict[str, Any]): Dictionary đại diện cho một node (và các con của nó).

    Returns:
        _TreeNode: Node gốc của cây hoặc nhánh cây đã được tái tạo.
    """
    if not isinstance(data, dict) or "node_id" not in data:
        raise ValueError("Dữ liệu không hợp lệ, thiếu key 'node_name'.")
    
    node_id = data["node_id"]

    # Chuẩn bị các tham số sẽ được truyền vào factory
    # Đây là các tham số động, không được định nghĩa sẵn trong Spec
    factory_kwargs: Dict[str, Any] = {}

    # 1. Đệ quy parse các node con trước (nếu có)
    if "children" in data:
        children_data = data["children"]
        if not isinstance(children_data, list):
            raise TypeError("'children' phải là một danh sách.")
        
        # Tái tạo lại từng node con và thêm vào kwargs
        factory_kwargs["children"] = [parse_tree_from_dict(child_data) for child_data in children_data]
        
    # Thêm các tham số đặc biệt khác ở đây nếu có...

    # 3. Gọi Node Factory để tạo node hiện tại
    # node_id của một node trong cây sẽ được tự tạo hoặc có thể lấy từ dict nếu muốn
    # Ở đây, ta đơn giản hóa bằng cách dùng chính node_name
    try:
        # Nhà máy sẽ sử dụng node_name để tra cứu Spec và dùng kwargs để truyền các tham số động
        node_instance = create_node(node_id=node_id, **factory_kwargs)
    except Exception as e:
        # Bọc lỗi gốc để cung cấp thêm ngữ cảnh khi debug
        raise ValueError(f"Lỗi khi tạo node với tên '{node_id}'. Lỗi gốc: {e}") from e

    return node_instance