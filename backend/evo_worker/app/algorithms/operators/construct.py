import random
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Self, Type, Generic

from app.state import SingletonNameable, Stateful

from ..pop import DominanceIndividual, Individual, IndividualType
import app.core.config as cfg

from itapia_common.rules.rule import Rule
from itapia_common.rules.nodes import _TreeNode
from itapia_common.rules.nodes.registry import get_spec_ent, create_node
from itapia_common.schemas.entities.rules import RuleStatus, SemanticType

from ..utils import grow_tree

class InitOperator(Stateful, SingletonNameable, Generic[IndividualType]):
    
    def __init__(self, purpose: SemanticType, ind_cls: Type[IndividualType],
                 new_rule_name_prefix: Optional[str] = None):
        # Kiểm tra chặt chẽ hơn
        self.purpose = purpose
        self.ind_cls = ind_cls
    
        # Sử dụng instance Random riêng để đảm bảo khả năng tái tạo
        self._random = random.Random(cfg.RANDOM_SEED)
        
        self.new_rule_name_prefix = new_rule_name_prefix if new_rule_name_prefix else uuid.uuid4().hex
        
    @abstractmethod
    def __call__(self) -> IndividualType:
        pass
    
    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {
            'random_state': self._random.getstate()
        }
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self._random.setstate(fallback_state['random_state'])
    
class RandomMaxDepthInitOperator(InitOperator[IndividualType]):
    def __init__(self, purpose: SemanticType, 
                 ind_cls: Type[IndividualType],
                 terminals_by_type: Dict[SemanticType, List[str]],
                 operators_by_type: Dict[SemanticType, List[str]],
                 max_depth: int = 5,
                 new_rule_name_prefix: Optional[str] = None):
        super().__init__(purpose, ind_cls, new_rule_name_prefix)
        if max_depth < 1:
            raise ValueError("Max depth must be at least 1.")
        self.max_depth = max_depth
                
        # Lấy danh sách các node đã được tiền xử lý
        self.terminals_by_type: Dict[SemanticType, List[str]] = terminals_by_type
        self.operators_by_type: Dict[SemanticType, List[str]] = operators_by_type
        
    def __call__(self) -> IndividualType:
        root = grow_tree(current_depth=1, 
                         max_depth=self.max_depth,
                         operators_by_type=self.operators_by_type,
                         terminals_by_type=self.terminals_by_type,
                         required_type=self.purpose,
                         random_ins=self._random)
        
        new_rule = Rule(
            root=root,
            description='An automatically generated rule by the evolution algorithm.',
            rule_status=RuleStatus.EVOLVING
        )
        new_rule.auto_id_name(self.new_rule_name_prefix)
        
        ind = self.ind_cls.from_rule(rule=new_rule)
        
        return ind