from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import json

class EvoRuleCRUD:
    """CRUD operations for evolutionary rules."""
    
    def __init__(self, db_session: Session):
        """Initialize the EvoRuleCRUD instance with a database session.
        
        Args:
            db_session (Session): The SQLAlchemy database session.
        """
        self.db = db_session

    def create_or_update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> str:
        """Create a new rule or update an existing rule in the database.
        
        Args:
            rule_id (str): Unique identifier for the rule.
            rule_data (Dict[str, Any]): Dictionary containing rule data including
                name, description, rule_status, purpose, created_at, root, evo_run_id, and metrics.
                
        Returns:
            str: The rule_id of the created or updated rule.
        """
        # Extract fields into separate columns for querying
        name = rule_data.get("name", "Untitled Rule")
        description = rule_data.get("description", "")
        rule_status = rule_data.get("rule_status")
        purpose = rule_data.get("purpose")
        created_at = rule_data.get("created_at")
        
        # Convert the entire dict to a JSON string for storage in the jsonb column
        root_str = json.dumps(rule_data.get('root'))
        evo_run_id = rule_data.get('evo_run_id')
        metrics = json.dumps(rule_data.get('metrics'))
        
        stmt = text("""
            INSERT INTO evo_rules (rule_id, name, description, purpose, rule_status, created_at, root, evo_run_id, metrics)
            VALUES (:rule_id, :name, :description, :purpose, :rule_status, :created_at, :root, :evo_run_id, :metrics)
            ON CONFLICT (rule_id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                purpose = EXCLUDED.purpose,
                rule_status = EXCLUDED.rule_status,
                root = EXCLUDED.root,
                evo_run_id = EXCLUDED.evo_run_id,
                metrics = EXCLUDED.metrics,
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
            "root": root_str,
            "evo_run_id": evo_run_id,
            "metrics": metrics
        })
        self.db.commit()
        return rule_id
    
    def get_all_rules_by_evo(self, rule_status: str, evo_run_id: str) -> List[Dict[str, Any]]:
        """Get a list of raw data (list of dicts) of all rules for a specific evolution run.
        
        Args:
            rule_status (str): Status of rules to retrieve.
            evo_run_id (str): Identifier of the evolution run.
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing rule data.
        """
        # Postgres JSONB query: `->>` extracts field as text
        stmt = text("""SELECT rule_id, name, description, purpose, rule_status, created_at, updated_at, root, evo_run_id, metrics
                    FROM evo_rules WHERE rule_status = :rule_status AND evo_run_id = :evo_run_id;""")
        
        results = self.db.execute(stmt, {'rule_status': rule_status, 'evo_run_id': evo_run_id})
        
        # Return a list of dictionaries
        return results.mappings().all()
    
    def get_all_rules(self, rule_status: str) -> List[Dict[str, Any]]:
        """Get a list of raw data (list of dicts) of all active rules.
        
        Args:
            rule_status (str): Status of rules to retrieve.
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing rule data.
        """
        # Postgres JSONB query: `->>` extracts field as text
        stmt = text("""SELECT rule_id, name, description, purpose, rule_status, created_at, updated_at, root, evo_run_id, metrics
                    FROM evo_rules WHERE rule_status = :rule_status;""")
        
        results = self.db.execute(stmt, {'rule_status': rule_status})
        
        # Return a list of dictionaries
        return results.mappings().all()
    
class EvoRunCRUD:
    """CRUD operations for evolutionary runs."""
    
    def __init__(self, db_session: Session):
        """Initialize the EvoRunCRUD instance with a database session.
        
        Args:
            db_session (Session): The SQLAlchemy database session.
        """
        self.db = db_session
        
    def save_evo_run(self, evo_run_id: str, evo_run_data: Dict[str, Any]) -> str:
        """Save or update an evolutionary run in the database.
        
        Args:
            evo_run_id (str): Unique identifier for the evolution run.
            evo_run_data (Dict[str, Any]): Dictionary containing evolution run data including
                status, config, fallback_state, and algorithm.
                
        Returns:
            str: The run_id of the saved or updated evolution run.
        """
        status = evo_run_data.get('status')
        config = json.dumps(evo_run_data.get('config'))
        fallback_state = evo_run_data.get('fallback_state')
        algorithm = evo_run_data.get('algorithm')
        
        stmt = text("""
            INSERT INTO evo_runs (run_id, status, algorithm, config, fallback_state)
            VALUES (:run_id, :status, :algorithm, :config, :fallback_state)
            ON CONFLICT (run_id) DO UPDATE SET
                status = EXCLUDED.status,
                config = EXCLUDED.config,
                algorithm = EXCLUDED.algorithm,
                fallback_state = EXCLUDED.fallback_state
            RETURNING run_id;
        """)
        
        self.db.execute(stmt, {
            "run_id": evo_run_id,
            "status": status,
            "config": config,
            "fallback_state": fallback_state,
            "algorithm": algorithm
        })
        
        self.db.commit()
        return evo_run_id
    
    def get_evo_run(self, evo_run_id: str) -> Dict[str, Any] | None:
        """Retrieve an evolutionary run by its ID.
        
        Args:
            evo_run_id (str): Identifier of the evolution run to retrieve.
            
        Returns:
            Dict[str, Any] | None: Dictionary containing evolution run data or None if not found.
        """
        stmt = text("""SELECT run_id, status, config, fallback_state, algorithm
                    FROM evo_runs WHERE run_id = :run_id;""")
        result = self.db.execute(stmt, {'run_id': evo_run_id})
        if result is None:
            return None
        return result.mappings().one()