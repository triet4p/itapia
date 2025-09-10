from typing import List, Optional
from sqlalchemy.orm import Session
from itapia_common.dblib.crud.evo import EvoRuleCRUD, EvoRunCRUD
from itapia_common.schemas.entities.evo import EvoRuleEntity, EvoRunEntity, EvoRunStatus
from itapia_common.schemas.entities.rules import RuleStatus

class EvoService:
    """Service class for managing evolutionary algorithms and rules."""
    
    def __init__(self, rdbms_session: Optional[Session]):
        self.run_crud: EvoRunCRUD = None
        self.rule_crud: EvoRuleCRUD = None
        
        if rdbms_session is not None:
            self.set_rdbms_session(rdbms_session)
        
    def set_rdbms_session(self, rdbms_session: Session):
        self.run_crud = EvoRunCRUD(rdbms_session)
        self.rule_crud = EvoRuleCRUD(rdbms_session)
        
    def save_evo_rules(self, evo_rules: List[EvoRuleEntity]) -> None:
        """Save a list of evolutionary rules to the database.
        
        Args:
            evo_rules (List[EvoRuleEntity]): List of EvoRuleEntity objects to save.
        """
        if self.rule_crud is None:
            raise ValueError("Connection to Rule DB is empty!")
        for rule_entity in evo_rules:
            rule_dict = rule_entity.model_dump()
            self.rule_crud.create_or_update_rule(rule_entity.rule_id, rule_dict)
    
    def change_status_of_last_rules(self, evo_run_id: str) -> None:
        """Change the status of the last evolutionary rules to DEPRECATED.
        
        Args:
            evo_run_id (str): Identifier of the evolution run.
        """
        if self.rule_crud is None:
            raise ValueError("Connection to Rule DB is empty!")
        rows = self.rule_crud.get_all_rules_by_evo(RuleStatus.EVOLVING, evo_run_id)
        last_rule_entities = [EvoRuleEntity(**row) for row in rows]
        for rule_entity in last_rule_entities:
            rule_entity.rule_status = RuleStatus.DEPRECATED
        
        self.save_evo_rules(last_rule_entities)
        
    def get_all_rules(self, rule_status: RuleStatus, evo_run_id: str|None = None) -> List[EvoRuleEntity]:
        """Retrieve all rules with a specific status, optionally filtered by evolution run.
        
        Args:
            rule_status (RuleStatus): Status of rules to retrieve.
            evo_run_id (str | None): Optional identifier of the evolution run to filter by.
            
        Returns:
            List[EvoRuleEntity]: List of EvoRuleEntity objects matching the criteria.
        """
        if self.rule_crud is None:
            raise ValueError("Connection to Rule DB is empty!")
        if evo_run_id:
            rows = self.rule_crud.get_all_rules_by_evo(rule_status, evo_run_id)
        else:
            rows = self.rule_crud.get_all_rules(rule_status)
        last_rule_entities = [EvoRuleEntity(**row) for row in rows]
        return last_rule_entities
        
    def save_evo_run(self, evo_run: EvoRunEntity) -> str:
        """Save an evolutionary run and its associated rules.
        
        This method deprecates previous rules, saves the current run rules,
        and saves the evolution run information.
        
        Args:
            evo_run (EvoRunEntity): EvoRunEntity object to save.
            
        Returns:
            str: The run_id of the saved evolution run.
        """
        if self.run_crud is None or self.rule_crud is None:
            raise ValueError("Connection to Rule and Run DB is empty!")
        evo_run_dict = evo_run.model_dump()
        
        # Deprecated last save rules
        self.change_status_of_last_rules(evo_run.run_id)
        
        # Save current run rules
        self.save_evo_rules(evo_run.rules)
        
        # Save other info
        return self.run_crud.save_evo_run(evo_run.run_id, evo_run_dict)
        
    def get_evo_run(self, evo_run_id: str) -> EvoRunEntity | None:
        """Retrieve an evolutionary run by its ID along with its associated rules.
        
        Args:
            evo_run_id (str): Identifier of the evolution run to retrieve.
            
        Returns:
            EvoRunEntity | None: EvoRunEntity object with associated rules or None if not found.
        """
        if self.run_crud is None or self.rule_crud is None:
            raise ValueError("Connection to Rule and Run DB is empty!")
        row = self.run_crud.get_evo_run(evo_run_id)
        rules = self.get_all_rules(RuleStatus.EVOLVING, evo_run_id)
        if row is None or not rules:
            return None
        res_dict = dict(row)
        if isinstance(res_dict['fallback_state'], memoryview):
            res_dict['fallback_state'] = res_dict['fallback_state'].tobytes()
        
        return EvoRunEntity(rules=rules, 
                            **res_dict)