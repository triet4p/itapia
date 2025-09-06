"""Provides CRUD operations for business rules entities."""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import RowMapping, Sequence, text
import uuid
import json

class RuleCRUD:
    """CRUD operations for business rules stored in the database."""
    
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_or_update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> str:

        # Extract fields into separate columns for querying
        name = rule_data.get("name", "Untitled Rule")
        description = rule_data.get("description", "")
        rule_status = rule_data.get("rule_status")
        purpose = rule_data.get("purpose")
        created_at = rule_data.get("created_at")
        
        # Convert the entire dict to a JSON string for storage in the jsonb column
        root_str = json.dumps(rule_data.get('root'))
        
        stmt = text("""
            INSERT INTO rules (rule_id, name, description, purpose, rule_status, created_at, root)
            VALUES (:rule_id, :name, :description, :purpose, :rule_status, :created_at, :root)
            ON CONFLICT (rule_id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                purpose = EXCLUDED.purpose,
                rule_status = EXCLUDED.rule_status,
                root = EXCLUDED.root,
                updated_at = NOW()
            RETURNING rule_id;
        """)
        
        self.db.execute(stmt, {
            "rule_id": rule_id,
            "name": name,
            "description": description,
            "purpose": purpose,
            "rule_status": rule_status,
            "created_at": created_at, 
            "root": root_str
        })
        self.db.commit()
        return rule_id

    def get_rule_by_id(self, rule_id: str) -> Optional[RowMapping]:
        stmt = text("""SELECT rule_id, name, description, purpose, rule_status, created_at, updated_at, root 
                    FROM rules WHERE rule_id = :rule_id;""")
        result = self.db.execute(stmt, {"rule_id": rule_id})
        
        if result:
            # result[0] contains the root column (jsonb type),
            # SQLAlchemy automatically parses it into a dict
            return result.mappings().one()
        return None

    def get_rules_by_purpose(self, purpose_name: str, rule_status: str) -> Sequence[RowMapping]:
        # Postgres JSONB query: `->>` extracts field as text
        stmt = text("""SELECT rule_id, name, description, purpose, rule_status, created_at, updated_at, root 
                    FROM rules WHERE rule_status = :rule_status AND purpose = :purpose;""")
        
        results = self.db.execute(stmt, {"purpose": purpose_name, "rule_status": rule_status})
        
        # Return a list of dictionaries
        return results.mappings().all()
    
    def get_all_rules(self, rule_status: str) -> Sequence[RowMapping]:
        # Postgres JSONB query: `->>` extracts field as text
        stmt = text("""SELECT rule_id, name, description, purpose, rule_status, created_at, updated_at, root 
                    FROM rules WHERE rule_status = :rule_status;""")
        
        results = self.db.execute(stmt, {'rule_status': rule_status})
        
        # Return a list of dictionaries
        return results.mappings().all()