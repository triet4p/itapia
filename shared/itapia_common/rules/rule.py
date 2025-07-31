# itapia_common/rules/rule.py

import uuid
from datetime import datetime, timezone
from typing import Dict, Any

# Giả định các module này tồn tại và chứa các hàm tương ứng
# Trong thực tế, bạn sẽ import chúng một cách chính xác
from .nodes import OperatorNode, _TreeNode
from itapia_common.schemas.enums import SemanticType
from .parser import parse_tree_from_dict, serialize_tree_to_dict

# Giả định sự tồn tại của schema báo cáo
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport


class Rule:
    """
    Đại diện cho một quy tắc nghiệp vụ hoàn chỉnh.
    
    Một quy tắc bao gồm siêu dữ liệu (để quản lý) và một cây logic (root)
    để thực thi. Gốc của cây logic luôn phải là một OperatorNode.
    """
    def __init__(self,
                 root: OperatorNode,
                 rule_id: str | None = None,
                 name: str = "Untitled Rule",
                 description: str = "",
                 is_active: bool = True,
                 version: int = 1,
                 created_at: datetime | None = None,
                 updated_at: datetime | None = None):
        """
        Khởi tạo một đối tượng Rule.

        Args:
            root (OperatorNode): Gốc của cây biểu thức logic. Phải là một OperatorNode.
            rule_id (str, optional): ID duy nhất của quy tắc. Nếu None, sẽ tự tạo UUID.
            name (str, optional): Tên quy tắc để con người đọc.
            description (str, optional): Mô tả chi tiết về quy tắc.
            purpose (str, optional): Mục đích của quy tắc (ví dụ: DECISION_MAKING).
            is_active (bool, optional): Cờ để bật/tắt quy tắc.
            version (float, optional): Phiên bản của quy tắc.
            created_at (datetime, optional): Thời gian tạo.
            updated_at (datetime, optional): Thời gian cập nhật lần cuối.
        """
        if not isinstance(root, OperatorNode):
            raise TypeError("Gốc (root) của một quy tắc phải là một thể hiện của OperatorNode.")
            
        self.rule_id = rule_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.root = root
        self.is_active = is_active
        self.version = version
        # Luôn sử dụng timezone-aware datetimes
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        
    @property
    def purpose(self):
        return self.root.return_type

    def __repr__(self) -> str:
        return f"Rule(rule_id='{self.rule_id}', name='{self.name}', version={self.version}, is_active={self.is_active})"

    def execute(self, report: QuickCheckAnalysisReport) -> float:
        """
        Thực thi quy tắc dựa trên một báo cáo phân tích và trả về kết quả.

        Đây là một facade, che giấu logic đệ quy của việc `evaluate` cây.
        """
        if not self.is_active:
            # Có thể trả về giá trị trung tính hoặc báo lỗi tùy thiết kế
            return 0.0 
        return self.root.evaluate(report)

    def to_dict(self) -> Dict[str, Any]:
        """
        Chuyển đổi (serialize) toàn bộ đối tượng Rule thành một dictionary.
        
        Cấu trúc dictionary này phù hợp để lưu trữ dưới dạng JSON trong CSDL 
        hoặc truyền qua API.
        """
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "purpose": self.purpose.value,
            "is_active": self.is_active,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            # Sử dụng helper để chuyển đổi cây logic thành dict
            "root": serialize_tree_to_dict(self.root)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """
        Tạo (deserialize) một đối tượng Rule từ một dictionary.

        Đây là một factory method, thường được sử dụng sau khi đọc dữ liệu
        từ CSDL hoặc một request API.
        """
        root_json = data.get("root")
        if not root_json:
            raise ValueError("Dữ liệu quy tắc thiếu cây logic 'root'.")
        
        # Sử dụng parser để tái tạo lại cây logic từ cấu trúc JSON
        try:
            root_node = parse_tree_from_dict(root_json)
        except Exception as e:
            # Bọc lỗi gốc để cung cấp thêm ngữ cảnh
            raise ValueError(f"Không thể phân tích cây logic cho rule_id '{data.get('rule_id')}'. Lỗi: {e}") from e
            
        # created_at và updated_at có thể không có trong dữ liệu cũ
        created_ts = data.get("created_at")
        updated_ts = data.get("updated_at")
        
        purpose_from_data_str = data.get("purpose")
        if purpose_from_data_str:
            try:
                # Chuyển chuỗi từ JSON thành Enum
                purpose_from_data = SemanticType[purpose_from_data_str]
                if purpose_from_data != root_node.return_type:
                    raise TypeError(
                        f"Purpose trong metadata ('{purpose_from_data.name}') "
                        f"không khớp với return_type của root node ('{root_node.return_type.name}')."
                    )
            except KeyError:
                raise ValueError(f"Purpose không hợp lệ: '{purpose_from_data_str}'")

        return cls(
            rule_id=data.get('rule_id'),
            name=data["name"],
            description=data.get("description", ""),
            is_active=data.get("is_active", True),
            version=data.get("version", 1.0),
            created_at=created_ts,
            updated_at=updated_ts,
            # Truyền cây logic đã được tái tạo
            root=root_node
        )