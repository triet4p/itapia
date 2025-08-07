from typing import List
from sqlalchemy.orm import Session
from itapia_common.schemas.enums import SemanticType
from itapia_common.dblib.crud.rules import RuleCRUD
from itapia_common.schemas.entities.rules import RuleEntity

class RuleService:
    def __init__(self, db_session: Session):
        # Service sẽ chứa một instance của lớp CRUD
        self.crud = RuleCRUD(db_session)

    def save_rule(self, rule_entity: RuleEntity) -> str:
        """
        Nhận một đối tượng Rule, chuyển nó thành dict,
        lưu vào DB thông qua CRUD, và trả về đối tượng Rule đã được lưu.
        """
        # Chuyển đối tượng nghiệp vụ thành dữ liệu thô
        rule_dict = rule_entity.model_dump()
        
        # Gọi CRUD để thực hiện thao tác với DB
        res_uuid = self.crud.create_or_update_rule(rule_entity.rule_id, rule_dict)
        
        # Trả về đối tượng Rule ban đầu để có thể tiếp tục sử dụng
        return res_uuid

    def get_rule_by_id(self, rule_id: str) -> RuleEntity | None:
        """
        Nhận một rule_id (str), lấy dữ liệu thô từ CRUD,
        và "lắp ráp" nó thành một đối tượng Rule.
        """

        # Lấy dữ liệu thô
        rule_data = self.crud.get_rule_by_id(rule_id)
        
        if rule_data:
            # "Lắp ráp" dữ liệu thô thành đối tượng nghiệp vụ
            return RuleEntity(**rule_data)
        return None

    def get_active_rules_by_purpose(self, purpose: SemanticType) -> List[RuleEntity]:
        """
        Nhận một SemanticType, lấy danh sách dữ liệu thô từ CRUD,
        và "lắp ráp" chúng thành một danh sách các đối tượng Rule.
        """
        # Chuyển đối tượng nghiệp vụ (Enum) thành dữ liệu thô (str)
        purpose_name = purpose.name
        
        # Lấy danh sách dữ liệu thô
        list_of_rule_data = self.crud.get_active_rules_by_purpose(purpose_name)
        
        # "Lắp ráp" từng dictionary thành đối tượng Rule
        return [RuleEntity(**row) for row in list_of_rule_data]
    
    def get_all_active_rules(self) -> List[RuleEntity]:
        # Lấy danh sách dữ liệu thô
        list_of_rule_data = self.crud.get_all_active_rules()
        
        # "Lắp ráp" từng dictionary thành đối tượng Rule
        return [RuleEntity(**row) for row in list_of_rule_data]