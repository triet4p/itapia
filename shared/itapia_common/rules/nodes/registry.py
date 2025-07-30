import inspect
from typing import NamedTuple, Dict, List, Any, Set, Type

from ._nodes import _TreeNode, NODE_TYPE
from itapia_common.schemas.enums import SemanticType

class NodeSpec(NamedTuple):
    node_class: Type[_TreeNode]
    description: str
    params: Dict[str, Any]
    return_type: SemanticType
    args_type: List[SemanticType] = None
    node_type: NODE_TYPE
    
_NODE_REGISTRY: Dict[str, NodeSpec] = {}
_CONST_NODES_ID: Set[str] = set()
_VAR_NODES_ID: Set[str] = set()
_OPR_NODES_ID: Set[str] = set()
    
def register_node_by_spec(node_name: str, spec: NodeSpec):
    """Đăng ký một bản thiết kế node mới."""
    node_name = node_name.upper()
    if node_name in _NODE_REGISTRY:
        raise ValueError(f"Node có tên '{node_name}' đã được đăng ký.")
    _NODE_REGISTRY[node_name] = spec
    
    if spec.node_type == 'constant':
        _CONST_NODES_ID.add(node_name)
    elif spec.node_type == 'variable':
        _VAR_NODES_ID.add(node_name)
    elif spec.node_type == 'operator':
        _OPR_NODES_ID.add(node_name)

# --- HÀM "NHÀ MÁY" (FACTORY FUNCTION) ---
# ... các import khác ...

def create_node(node_name: str, **kwargs) -> _TreeNode:
    """
    Hàm nhà máy chính (phiên bản nâng cao).
    Tạo một đối tượng Node dựa trên tên đã đăng ký.
    Hàm này tự động kiểm tra các tham số hợp lệ cho constructor của node.
    """
    node_name = node_name.upper()
    spec = _NODE_REGISTRY.get(node_name)
    if spec is None:
        raise ValueError(f"Không tìm thấy bản thiết kế nào cho node có tên '{node_name}'.")
    
    # --- Bước 1: Tổng hợp tất cả các tham số có thể có ---
    
    # a. Các tham số từ spec và kwargs
    possible_params = spec.params.copy()
    possible_params.update(kwargs)
    
    # b. Các tham số cố định từ spec
    possible_params['node_name'] = node_name
    possible_params['description'] = spec.description
    possible_params['return_type'] = spec.return_type
    if spec.args_type is not None:
        possible_params['args_type'] = spec.args_type

    # --- Bước 2: Lấy danh sách các tham số mà constructor thực sự cần ---
    
    constructor_params = inspect.signature(spec.node_class.__init__).parameters
    # constructor_params là một dict: {'self': ..., 'node_name': ..., 'description': ...}
    
    valid_param_names = set(constructor_params.keys())
    
    # --- Bước 3: Lọc và chỉ giữ lại những tham số hợp lệ ---
    
    final_params = {
        key: value for key, value in possible_params.items() 
        if key in valid_param_names
    }

    # --- Bước 4: Tạo đối tượng node ---
    
    try:
        return spec.node_class(**final_params)
    except TypeError as e:
        # Báo lỗi rõ ràng hơn nếu vẫn có vấn đề
        raise TypeError(
            f"Lỗi khi khởi tạo node '{node_name}' với lớp '{spec.node_class.__name__}'. "
            f"Tham số cuối cùng: {final_params}. Lỗi gốc: {e}"
        ) from e
        
def get_all_const_nodes() -> Set[str]:
    return _CONST_NODES_ID

def get_all_var_nodes() -> Set[str]:
    return _VAR_NODES_ID

def get_all_opr_nodes() -> Set[str]:
    return _OPR_NODES_ID

def get_nodes_by_type(node_type: NODE_TYPE, semantic_type: SemanticType) -> List[str]:
    return [
        node_name for node_name, spec in _NODE_REGISTRY.items()
        if spec.node_type == node_type and spec.return_type == semantic_type
    ]
    
