"""Provides CRUD operations for business rules entities."""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import json

class RuleCRUD:
    """CRUD operations for business rules stored in the database."""
    
    def __init__(self, db_session: Session):
        """Initialize the RuleCRUD instance with a database session.

        Args:
            db_session (Session): The SQLAlchemy database session.
        """
        self.db = db_session

    def create_or_update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> str:
        """Create or update a rule in the database using raw data.
        
        This function uses PostgreSQL's `ON CONFLICT DO UPDATE` (UPSERT) feature.

        Args:
            rule_id (str): ID of the rule.
            rule_data (Dict[str, Any]): Dictionary containing the complete rule definition.

        Returns:
            str: ID of the saved rule.
        """
        # Extract fields into separate columns for querying
        name = rule_data.get("name", "Untitled Rule")
        description = rule_data.get("description", "")
        version = rule_data.get("version", 1.0)
        is_active = rule_data.get("is_active", True)
        purpose = rule_data.get("purpose")
        created_at = rule_data.get("created_at")
        
        # Convert the entire dict to a JSON string for storage in the jsonb column
        root_str = json.dumps(rule_data.get('root'))
        
        stmt = text("""
            INSERT INTO rules (rule_id, name, description, purpose, version, is_active, created_at, root)
            VALUES (:rule_id, :name, :description, :purpose, :version, :is_active, :created_at, :root)
            ON CONFLICT (rule_id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                purpose = EXCLUDED.purpose,
                version = EXCLUDED.version,
                is_active = EXCLUDED.is_active,
                root = EXCLUDED.root,
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
            "root": root_str
        })
        self.db.commit()
        return rule_id

    def get_rule_by_id(self, rule_id: str) -> Dict[str, Any] | None:
        """Get raw data (dict) of a rule by its ID.

        Args:
            rule_id (str): The ID of the rule to retrieve.

        Returns:
            Dict[str, Any] | None: The rule data as a dictionary, or None if not found.
        """
        stmt = text("""SELECT rule_id, name, description, purpose, version, is_active, created_at, updated_at, root 
                    FROM rules WHERE is_active=TRUE AND rule_id = :rule_id;""")
        result = self.db.execute(stmt, {"rule_id": rule_id})
        
        if result:
            # result[0] contains the root column (jsonb type),
            # SQLAlchemy automatically parses it into a dict
            return result.mappings().one()
        return None

    def get_active_rules_by_purpose(self, purpose_name: str) -> List[Dict[str, Any]]:
        """Get a list of raw data (list of dicts) of active rules for a specific purpose.

        Args:
            purpose_name (str): The purpose to filter rules by.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing rule data.
        """
        # Postgres JSONB query: `->>` extracts field as text
        stmt = text("""SELECT rule_id, name, description, purpose, version, is_active, created_at, updated_at, root 
                    FROM rules WHERE is_active=TRUE AND purpose = :purpose;""")
        
        results = self.db.execute(stmt, {"purpose": purpose_name})
        
        # Return a list of dictionaries
        return results.mappings().all()
    
    def get_all_active_rules(self) -> List[Dict[str, Any]]:
        """Get a list of raw data (list of dicts) of all active rules.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing rule data.
        """
        # Postgres JSONB query: `->>` extracts field as text
        stmt = text("""SELECT rule_id, name, description, purpose, version, is_active, created_at, updated_at, root 
                    FROM rules WHERE is_active=TRUE;""")
        
        results = self.db.execute(stmt)
        
        # Return a list of dictionaries
        return results.mappings().all()