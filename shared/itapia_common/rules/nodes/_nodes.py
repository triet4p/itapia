from abc import ABC, abstractmethod
from typing import Literal, Any, Set, Tuple, Dict, List
from itapia_common.schemas.entities.reports import QuickCheckReport
from itapia_common.rules.exceptions import NotFoundVarPathError
from itapia_common.schemas.enums import SemanticType

def normalize(raw_value: int|float, default_value: int|float,
              source_range: Tuple[float, float], target_range: Tuple[float, float]):
    if not isinstance(raw_value, (int, float)):
        return default_value
    
    source_min, source_max = source_range
    target_min, target_max = target_range

    # Kẹp giá trị vào trong khoảng nguồn
    clamped_value = max(source_min, min(source_max, raw_value))
    
    # Công thức chuẩn hóa
    source_span = source_max - source_min
    target_span = target_max - target_min
    
    if source_span == 0:
        return target_min
        
    scaled_value = (clamped_value - source_min) / source_span
    return target_min + (scaled_value * target_span)

def denormalize(encoded_value: int|float,
                source_range: Tuple[float, float], target_range: Tuple[float, float]):
    source_min, source_max = source_range
    target_min, target_max = target_range
    
    target_span = target_max - target_min
    source_span = source_max - source_min

    if target_span == 0:
        return source_min

    scaled_value = (encoded_value - target_min) / target_span
    return source_min + (scaled_value * source_span)

NODE_TYPE = Literal['constant', 'variable', 'operator']

class _TreeNode(ABC):
    def __init__(self, node_name: str, node_type: NODE_TYPE,
                 description: str, return_type: SemanticType):
        self.node_name = node_name
        self.node_type = node_type
        self.description = description
        self.return_type = return_type
        
    @abstractmethod
    def evaluate(self, report: QuickCheckReport) -> float:
        pass
    
    def __eq__(self, value):
        if not isinstance(value, _TreeNode):
            return False
        return self.node_name == value.node_name and self.return_type == value.return_type
    
class ConstantNode(_TreeNode):
    def __init__(self, node_name: str, description: str, return_type: SemanticType,
                 value: float, use_normalize: bool = False,
                 source_range: Tuple[float, float]|None = None,
                 target_range: Tuple[float, float]|None = None):
        super().__init__(node_name, node_type='constant', description=description, return_type=return_type)
        self.value = value
        
        if use_normalize:
            if source_range is None or target_range is None:
                raise ValueError('use_normarlize=True requiered source range and target range')
        
        self.source_range = source_range
        self.target_range = target_range
        self.use_normalize = use_normalize
    
    def evaluate(self, report):
        if not self.use_normalize:
            return self.value
        return normalize(self.value, 0, self.source_range, self.target_range)
    
# -- Lớp VarNode được tái cấu trúc --
class VarNode(_TreeNode):
    """
    Lớp cơ sở cho các "Biến thông minh".
    Nó biết cách trích xuất một giá trị thô từ report và mã hóa nó thành số.
    """
    def __init__(self, node_name: str, description: str, return_type: SemanticType,
                 path: str, default_value: float = 0.0):
        # Lưu ý: node_type sẽ được gán ở lớp con
        super().__init__(node_name, node_type='variable', description=description, return_type=return_type)
        self.path = path
        self.default_value = default_value
        
    def _get_raw_value_from_report(self, report: QuickCheckReport) -> Any:
        """
        Hàm nội bộ để lấy giá trị thô, hỗ trợ cả thuộc tính object, key của dict, và chỉ số của list.
        """
        try:
            keys = self.path.split('.')
            value = report
            for key in keys:
                if value is None:
                    # Nếu một mắt xích trung gian là None, dừng lại và trả về None
                    return None

                if key.isdigit() or (key.startswith('-') and key[1:].isdigit()):
                    # Xử lý trường hợp là chỉ số của danh sách (ví dụ: '0', '-1')
                    index = int(key)
                    if isinstance(value, list) and -len(value) <= index < len(value):
                        value = value[index]
                    else:
                        # Index không hợp lệ hoặc value không phải là list
                        return None
                elif isinstance(value, dict):
                    # Xử lý trường hợp là key của dictionary
                    value = value.get(key)
                else:
                    # Xử lý trường hợp là thuộc tính của object
                    value = getattr(value, key)
            
            return value
        except (AttributeError, KeyError, TypeError, IndexError):
            raise NotFoundVarPathError(self.path)

    def evaluate(self, report: QuickCheckReport) -> float:
        """
        Luồng thực thi chính của một VarNode.
        1. Lấy giá trị thô, nếu path sai thì ném lỗi (cái này quan trọng, nó khác có path nhưng ko có giá trị)
        2. Nếu không có, trả về giá trị mặc định.
        3. Nếu có, mã hóa nó và trả về.
        """
        raw_value = self._get_raw_value_from_report(report)
        if raw_value is None:
            return self.default_value
        
        return self.encode(raw_value)

    @abstractmethod
    def encode(self, raw_value: Any) -> float:
        """Mã hóa giá trị thô thành một số float."""
        pass
    
    @abstractmethod
    def decode(self, encoded_value: float) -> Any:
        """Giải mã một số float trở lại giá trị thô (hữu ích cho việc giải thích)."""
        pass

class NumericalVarNode(VarNode):
    """Node biến dành cho các giá trị số."""
    def __init__(self, node_name: str, description: str, return_type: SemanticType,
                 path: str, default_value: float = 0.0,
                 source_range: Tuple[float, float] = (0, 100),
                 target_range: Tuple[float, float] = (-1, 1)):
        super().__init__(node_name, description, return_type, path, default_value)
        self.source_range = source_range
        self.target_range = target_range

    def encode(self, raw_value: float) -> float:
        """
        Chuẩn hóa giá trị số từ `source_range` về `target_range`.
        Ví dụ: Chuẩn hóa RSI (0-100) về thang điểm (-1, 1).
        """
        return normalize(raw_value, self.default_value, self.source_range, self.target_range)

    def decode(self, encoded_value: float) -> float:
        """Thực hiện giải mã ngược lại từ target_range về source_range."""
        return denormalize(encoded_value, self.source_range, self.target_range)

class CategoricalVarNode(VarNode):
    """Node biến dành cho các giá trị hạng mục (chuỗi)."""
    def __init__(self, node_name: str, description: str, return_type: SemanticType,
                 path: str, default_value: float = 0.0,
                 mapping: Dict[str, float] = None,
                 use_default_label_mapping: bool = False,
                 available_values: Set[str]|None = None):
        super().__init__(node_name, description, return_type, path, default_value)
        self.mapping = mapping if mapping is not None else {}
        if use_default_label_mapping:
            self.create_label_mapping(available_values)
        # Tạo sẵn bản đồ ngược để decode hiệu quả
        self._reverse_mapping = {v: k for k, v in self.mapping.items()}
        
    def create_label_mapping(self, available_values: Set[str]):
        it = 0
        self.mapping = {}
        for val in available_values:
            self.mapping[val] = it
            it += 1

    def encode(self, raw_value: str) -> float:
        """Ánh xạ giá trị chuỗi thành số float dựa trên bản đồ `mapping`."""
        if not isinstance(raw_value, str):
            return self.default_value
        return self.mapping.get(raw_value, self.default_value)

    def decode(self, encoded_value: float) -> str:
        """Tìm lại chuỗi gốc từ giá trị đã mã hóa."""
        # Cần xử lý trường hợp nhiều key cùng map tới 1 value, ở đây lấy key đầu tiên
        return self._reverse_mapping.get(encoded_value, "unknown")

    @staticmethod
    def get_possible_values_from_schema(schema_class: Any, path: str) -> Set[str]:
        """
        Hàm tĩnh để lấy các giá trị khả dĩ của một trường Literal từ schema.
        Hữu ích cho Evo-worker hoặc UI để biết các lựa chọn.
        
        Cách dùng: get_possible_values_from_schema(QuickCheckReport, "technical.daily.trend.ma_direction")
        """
        try:
            keys = path.split('.')
            current_class = schema_class
            for key in keys:
                field_info = current_class.model_fields[key]
                # Lấy class của kiểu dữ liệu của trường
                current_class = field_info.annotation
            
            # Sau khi duyệt xong, current_class sẽ là kiểu Literal
            # Sử dụng __args__ để lấy tuple các giá trị khả dĩ
            return set(current_class.__args__)
        except (AttributeError, KeyError, TypeError):
            raise NotFoundVarPathError(path)
            
class OperatorNode(_TreeNode):
    """Node thực hiện một phép toán trên các node con của nó."""
    def __init__(self, node_name: str, description: str, num_child: int|None,
                 return_type: SemanticType, args_type: List[SemanticType],
                 children: List[_TreeNode] = []):
        super().__init__(node_name, node_type='operator', description=description, return_type=return_type)
        self.num_child = num_child
        self.children = children
        
        if num_child is not None and num_child != len(args_type):
            raise ValueError('Lenght of Args type must equal num child')
        
        self.args_type = args_type
        
        
    def add_child_node(self, child_node: _TreeNode):
        if self.num_child is not None:
            if len(self.children) == self.num_child:
                raise ValueError('Children of this node is full!')
        self.children.append(child_node)
        
    def update_node(self, old_idx: int, new_node: _TreeNode):
        if not (0 <= old_idx < len(self.children)):
            raise IndexError("Chỉ số của node con không hợp lệ.")
        self.children[old_idx] = new_node
        
    def clear(self):
        self.children.clear()
        
    def check_valid_children(self) -> bool:
        if self.num_child is None:
            return True
        if len(self.children) != self.num_child:
            return False
        return True
    
    @abstractmethod
    def _evaluate_valid(self, report: QuickCheckReport) -> float:
        pass
    
    def evaluate(self, report):
        if not self.check_valid_children():
            raise ValueError('Children node are not valid')
        return self._evaluate_valid(report)
    
class FunctionalOperatorNode(OperatorNode):
    def __init__(self, node_name: str, description: str, num_child: int|None,
                 return_type: SemanticType, args_type: List[SemanticType], 
                 opr_func: Any, children: List[_TreeNode] = []):
        super().__init__(node_name, description, num_child, return_type, args_type, children)
        self.opr_func = opr_func
        
    def _evaluate_valid(self, report):
        child_results = [child.evaluate(report) for child in self.children]
        return self.opr_func(*child_results)
    
class BranchOperatorNode(OperatorNode):
    """If A then B else C"""
    def __init__(self, node_name: str, description: str,
                 return_type: SemanticType, args_type: List[SemanticType],
                 children: List[_TreeNode] = []):
        super().__init__(node_name, description, num_child=3, 
                         return_type=return_type, args_type=args_type, children=children)
        
    def _evaluate_valid(self, report):
        condition = self.children[0].evaluate(report)
        
        if condition > 0: # if condition == 1.0
            return self.children[1].evaluate(report)
        else:
            return self.children[2].evaluate(report)