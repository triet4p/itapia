from typing import List

from itapia_common.dblib.services.rules import RuleService
from itapia_common.dblib.session import get_rdbms_session
from itapia_common.logger import ITAPIALogger
from itapia_common.rules.builtin import (
    builtin_decision_rules,
    builtin_opportunity_rules,
    builtin_risk_rules,
)
from itapia_common.rules.rule import Rule
from itapia_common.schemas.entities.rules import RuleEntity

logger = ITAPIALogger("Rules Seeding")


def seed_rules(rule_service: RuleService, rules: List[Rule]):
    for rule in rules:
        rule_dict = rule.to_entity()
        rule_entity = RuleEntity.model_validate(rule_dict)
        rule_service.save_rule(rule_entity)


def seed_all():
    rdbms_session = next(get_rdbms_session())
    rule_service = RuleService(rdbms_session)

    logger.info("Seeding built in decision rules")
    seed_rules(rule_service, builtin_decision_rules())

    logger.info("Seeding built in risk rules")
    seed_rules(rule_service, builtin_risk_rules())

    logger.info("Seeding built in opportunity rules")
    seed_rules(rule_service, builtin_opportunity_rules())


if __name__ == "__main__":
    seed_all()
