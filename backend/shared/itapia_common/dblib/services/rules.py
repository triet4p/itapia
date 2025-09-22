"""Service layer for business rules operations.

This module provides a high-level interface for managing business rules,
handling the conversion between Pydantic models and database representations.
"""

from typing import List, Optional

from itapia_common.dblib.crud.rules import RuleCRUD
from itapia_common.schemas.entities.rules import RuleEntity, RuleStatus, SemanticType
from sqlalchemy.orm import Session


class RuleService:
    """Service class for managing business rules."""

    def __init__(self, rdbms_session: Optional[Session]):
        self.crud: RuleCRUD = None
        if rdbms_session is not None:
            self.set_rdbms_session(rdbms_session)

    def set_rdbms_session(self, rdbms_session: Session) -> None:
        self.crud = RuleCRUD(rdbms_session)

    def check_health(self):
        if self.crud is None:
            raise ValueError("Connection is empty!")

    def save_rule(self, rule_entity: RuleEntity) -> str:
        """Take a Rule object, convert it to a dict, save it to the database
        through the CRUD layer, and return the saved Rule object.

        Args:
            rule_entity (RuleEntity): The rule entity to save.

        Returns:
            str: The ID of the saved rule.
        """
        self.check_health()
        # Convert the business object to raw data
        rule_dict = rule_entity.model_dump()

        # Call CRUD to perform the database operation
        res_uuid = self.crud.create_or_update_rule(rule_entity.rule_id, rule_dict)

        # Return the original Rule object so it can continue to be used
        return res_uuid

    def get_rule_by_id(self, rule_id: str) -> RuleEntity | None:
        """Take a rule_id (str), get raw data from the CRUD layer,
        and "assemble" it into a Rule object.

        Args:
            rule_id (str): The ID of the rule to retrieve.

        Returns:
            RuleEntity | None: The rule entity if found, otherwise None.
        """
        self.check_health()
        # Get raw data
        rule_data = self.crud.get_rule_by_id(rule_id)

        if rule_data:
            # "Assemble" the raw data into a business object
            return RuleEntity(**rule_data)
        return None

    def get_rules_by_purpose(
        self, purpose: SemanticType, rule_status: RuleStatus
    ) -> List[RuleEntity]:
        """Take a SemanticType, get a list of raw data from the CRUD layer,
        and "assemble" them into a list of Rule objects.

        Args:
            purpose (SemanticType): The semantic type to filter rules by.
            rule_status (RuleStatus): Status of rules to filter.

        Returns:
            List[RuleEntity]: A list of rule entities.
        """
        self.check_health()
        # Convert the business object (Enum) to raw data (str)
        purpose_name = purpose.name
        rule_status_name = rule_status.name

        # Get list of raw data
        list_of_rule_data = self.crud.get_rules_by_purpose(
            purpose_name, rule_status_name
        )

        # "Assemble" each dictionary into a Rule object
        return [RuleEntity(**row) for row in list_of_rule_data]

    def get_all_rules(self, rule_status: RuleStatus) -> List[RuleEntity]:
        """Get all active rules from the database.

        Args:
            rule_status (RuleStatus): Status of rules to filter.

        Returns:
            List[RuleEntity]: A list of all active rule entities.
        """
        self.check_health()
        # Get list of raw data
        list_of_rule_data = self.crud.get_all_rules(rule_status.name)

        # "Assemble" each dictionary into a Rule object
        return [RuleEntity(**row) for row in list_of_rule_data]
