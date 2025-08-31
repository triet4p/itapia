from typing import List
from sqlalchemy.orm import Session
from itapia_common.dblib.crud.evo import EvoRuleCRUD, EvoRunCRUD
from itapia_common.schemas.entities.evo import EvoRuleEntity, EvoRunEntity, EvoRunStatus
from itapia_common.schemas.entities.rules import RuleStatus

class EvoService:
    def __init__(self, rdbms_session: Session):
        self.run_crud = EvoRunCRUD(rdbms_session)
        self.rule_crud = EvoRuleCRUD(rdbms_session)
        
    def save_evo_rules(self, evo_rules: List[EvoRuleEntity]):
        for rule_entity in evo_rules:
            rule_dict = rule_entity.model_dump()
            self.rule_crud.create_or_update_rule(rule_entity.rule_id, rule_dict)
    
    def change_status_of_last_rules(self, evo_run_id: str):
        rows = self.rule_crud.get_all_rules_by_evo(RuleStatus.EVOLVING, evo_run_id)
        last_rule_entities = [EvoRuleEntity(**row) for row in rows]
        for rule_entity in last_rule_entities:
            rule_entity.rule_status = RuleStatus.DEPRECATED
        
        self.save_evo_rules(last_rule_entities)
        
    def get_all_rules(self, rule_status: RuleStatus, evo_run_id: str|None = None) -> List[EvoRuleEntity]:
        if evo_run_id:
            rows = self.rule_crud.get_all_rules_by_evo(rule_status, evo_run_id)
        else:
            rows = self.rule_crud.get_all_rules(rule_status)
        last_rule_entities = [EvoRuleEntity(**row) for row in rows]
        return last_rule_entities
        
    def save_evo_run(self, evo_run: EvoRunEntity):
        evo_run_dict = evo_run.model_dump()
        
        # Deperecated last save rules
        self.change_status_of_last_rules(evo_run.run_id)
        
        # Save current run rules
        self.save_evo_rules(evo_run.rules)
        
        # Save other info
        return self.run_crud.save_evo_run(evo_run.run_id, evo_run_dict)
        
    def get_evo_run(self, evo_run_id: str) -> EvoRunEntity | None:
        row = self.run_crud.get_evo_run(evo_run_id)
        rules = self.get_all_rules(RuleStatus.EVOLVING, evo_run_id)
        if row is None or not rules:
            return None
        return EvoRunEntity(rules=rules, **row)
    
    
        
    