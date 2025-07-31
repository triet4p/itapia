from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import json

class RuleCRUD:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_or_update_rule(self, rule_id: uuid.UUID, rule_data: Dict[str, Any]) -> uuid.UUID:
        """
        Tạo hoặc cập nhật một quy tắc trong CSDL bằng dữ liệu thô.
        Hàm này sử dụng `ON CONFLICT DO UPDATE` (UPSERT) của Postgres.

        Args:
            rule_id (uuid.UUID): ID của quy tắc.
            rule_data (Dict[str, Any]): Dictionary chứa toàn bộ định nghĩa quy tắc.

        Returns:
            uuid.UUID: ID của quy tắc đã được lưu.
        """
        # Trích xuất các trường ở cột riêng để có thể query
        name = rule_data.get("name", "Untitled Rule")
        description = rule_data.get("description", "")
        version = rule_data.get("version", 1.0)
        is_active = rule_data.get("is_active", True)
        purpose = rule_data.get("purpose")
        created_at = rule_data.get("created_at")
        
        # Chuyển toàn bộ dict thành chuỗi JSON để lưu vào cột jsonb
        rule_definition_str = json.dumps(rule_data.get('rule_definition'))
        
        stmt = text("""
            INSERT INTO rules (rule_id, name, description, purpose, version, is_active, created_at, rule_definition)
            VALUES (:rule_id, :name, :description, :purpose, :version, :is_active, :created_at, :rule_definition)
            ON CONFLICT (rule_id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                purpose = EXCLUDED.purpose,
                version = EXCLUDED.version,
                is_active = EXCLUDED.is_active,
                rule_definition = EXCLUDED.rule_definition,
                updated_at = NOW()
            RETURNING rule_id;
        """)
        
        self.db.execute(stmt, {
            "rule_id": rule_id,
            "name": name,
            "description": description,
            "purpose": purpose,
            "version": version,
            "is_active": is_active,
            "created_at": created_at, 
            "rule_definition": rule_definition_str
        })
        self.db.commit()
        return rule_id

    def get_rule_by_id(self, rule_id: uuid.UUID) -> Dict[str, Any] | None:
        """Lấy dữ liệu thô (dict) của một quy tắc bằng ID."""
        stmt = text("""SELECT rule_id, name, description, purpose, version, is_active, created_at, updated_at, rule_definition 
                    FROM rules WHERE is_active=TRUE AND rule_id = :rule_id;""")
        result = self.db.execute(stmt, {"rule_id": rule_id}).fetchone()
        
        if result:
            # result[0] chứa cột rule_definition (kiểu jsonb),
            # SQLAlchemy tự động parse nó thành dict
            return result[0]
        return None

    def get_active_rules_by_purpose(self, purpose_name: str) -> List[Dict[str, Any]]:
        """
        Lấy danh sách dữ liệu thô (list of dicts) của các quy tắc đang hoạt động
        theo một mục đích cụ thể.
        """
        # Postgres JSONB query: `->>` trích xuất trường dưới dạng text
        stmt = text("""SELECT rule_id, name, description, purpose, version, is_active, created_at, updated_at, rule_definition 
                    FROM rules WHERE is_active=TRUE AND purpose = :purpose;""")
        
        results = self.db.execute(stmt, {"purpose": purpose_name}).fetchall()
        
        # Trả về một list các dictionary
        return [row[0] for row in results]