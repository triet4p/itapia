"""Initialization operators for evolutionary algorithms."""

import random
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Self, Type, Generic

from app.state import SingletonNameable, Stateful

from ..pop import DominanceIndividual, Individual, IndividualType
import app.core.config as cfg

from itapia_common.rules.rule import Rule
from itapia_common.rules.nodes import _TreeNode
from itapia_common.rules.nodes.registry import get_spec_ent, create_node
from itapia_common.schemas.entities.rules import RuleStatus, SemanticType

from ..tree import grow_tree


class InitOperator(Stateful, SingletonNameable, Generic[IndividualType]):
    """Abstract base class for initialization operators in evolutionary algorithms.
    
    Provides a framework for creating new individuals in the population.
    """
    
    def __init__(self, purpose: SemanticType, ind_cls: Type[IndividualType],
                 new_rule_name_prefix: Optional[str] = None):
        """Initialize the initialization operator.
        
        Args:
            purpose (SemanticType): Semantic purpose of the individuals to create
            ind_cls (Type[IndividualType]): Class of individuals to create
            new_rule_name_prefix (Optional[str], optional): Prefix for new rule names. 
                Defaults to None, which generates a UUID.
        """
        # More strict checking
        self.purpose = purpose
        self.ind_cls = ind_cls
    
        # Use separate Random instance to ensure reproducibility
        self._random = random.Random(cfg.RANDOM_SEED)
        
        self.new_rule_name_prefix = new_rule_name_prefix if new_rule_name_prefix else uuid.uuid4().hex
        
    @abstractmethod
    def __call__(self) -> IndividualType:
        """Create a new individual.
        
        Returns:
            IndividualType: Newly created individual
        """
        pass
    
    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {
            'random_state': self._random.getstate()
        }
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self._random.setstate(fallback_state['random_state'])
    

class RandomMaxDepthInitOperator(InitOperator[IndividualType]):
    """Random initialization operator with maximum depth constraint.
    
    Creates individuals with random tree structures up to a specified maximum depth.
    """
    
    def __init__(self, purpose: SemanticType, 
                 ind_cls: Type[IndividualType],
                 terminals_by_type: Dict[SemanticType, List[str]],
                 operators_by_type: Dict[SemanticType, List[str]],
                 max_depth: int = 5,
                 new_rule_name_prefix: Optional[str] = None):
        """Initialize random maximum depth initialization operator.
        
        Args:
            purpose (SemanticType): Semantic purpose of the individuals to create
            ind_cls (Type[IndividualType]): Class of individuals to create
            terminals_by_type (Dict[SemanticType, List[str]]): Dictionary mapping semantic types to terminal node names
            operators_by_type (Dict[SemanticType, List[str]]): Dictionary mapping semantic types to operator node names
            max_depth (int, optional): Maximum tree depth. Defaults to 5.
            new_rule_name_prefix (Optional[str], optional): Prefix for new rule names. 
                Defaults to None, which generates a UUID.
                
        Raises:
            ValueError: If max_depth is less than 1
        """
        super().__init__(purpose, ind_cls, new_rule_name_prefix)
        if max_depth < 1:
            raise ValueError("Max depth must be at least 1.")
        self.max_depth = max_depth
                
        # Get list of preprocessed nodes
        self.terminals_by_type: Dict[SemanticType, List[str]] = terminals_by_type
        self.operators_by_type: Dict[SemanticType, List[str]] = operators_by_type
        
    def __call__(self) -> IndividualType:
        """Create a new individual with random tree structure.
        
        Returns:
            IndividualType: Newly created individual with random tree structure
        """
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