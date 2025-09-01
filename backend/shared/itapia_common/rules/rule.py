# itapia_common/rules/rule.py

import uuid
from datetime import datetime, timezone
from copy import deepcopy
from typing import Dict, Any, Self
from hashlib import sha1

# Assuming these modules exist and contain the corresponding functions
# In practice, you would import them correctly
from .nodes import OperatorNode, _TreeNode
from itapia_common.schemas.entities.rules import RuleEntity, SemanticType, RuleStatus
from .parser import parse_tree, serialize_tree

# Assuming the existence of the report schema
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport


class Rule:
    """Represents a complete business rule.
    
    A rule consists of metadata (for management) and a logic tree (root)
    for execution. The root of the logic tree must always be an OperatorNode.
    """
    
    def __init__(self,
                 root: OperatorNode,
                 rule_id: str | None = None,
                 name: str = "Untitled Rule",
                 description: str = "",
                 rule_status: RuleStatus = RuleStatus.READY,
                 created_at: datetime | None = None,
                 updated_at: datetime | None = None):
        """Initialize a Rule object.

        Args:
            root (OperatorNode): The root of the logic expression tree. Must be an OperatorNode.
            rule_id (str, optional): Unique ID of the rule. If None, a UUID will be auto-generated.
            name (str, optional): Human-readable name of the rule.
            description (str, optional): Detailed description of the rule.
            status (RuleStatus, optional): Status of Rule
            created_at (datetime, optional): Creation time.
            updated_at (datetime, optional): Last update time.
            
        Raises:
            TypeError: If root is not an OperatorNode instance.
        """
        if not isinstance(root, OperatorNode):
            raise TypeError("The root of a rule must be an instance of OperatorNode.")
            
        self.rule_id = rule_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.root = root
        self.rule_status = rule_status
        # Always use timezone-aware datetimes
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        
    @property
    def purpose(self) -> SemanticType:
        """Get the purpose of the rule based on the root node's return type.
        
        Returns:
            SemanticType: The semantic type of the rule's output.
        """
        return self.root.return_type

    def __repr__(self) -> str:
        return f"Rule(rule_id='{self.rule_id}', name='{self.name}', status='{self.rule_status}')"

    def execute(self, report: QuickCheckAnalysisReport) -> float:
        """Execute the rule based on an analysis report and return the result.

        This is a facade that hides the recursive logic of tree `evaluate`.
        
        Args:
            report (QuickCheckAnalysisReport): The analysis report to execute against.
            
        Returns:
            float: The result of the rule execution.
        """
        if self.rule_status == RuleStatus.DEPRECATED:
            # Can return a neutral value or raise an error depending on design
            return 0.0 
        return self.root.evaluate(report)

    def to_entity(self) -> RuleEntity:
        """Serialize the entire Rule object into a dictionary.
        
        This dictionary structure is suitable for storage as JSON in a database
        or transmission via API.
        
        Returns:
            RuleEntity: A dictionary representing the rule.
        """
        return RuleEntity(
            rule_id=self.rule_id,
            name=self.name,
            description=self.description,
            purpose=self.purpose,
            rule_status=self.rule_status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            root=serialize_tree(self.root)
        )

    @classmethod
    def from_entity(cls, data: RuleEntity) -> Self:
        """Create (deserialize) a Rule object from a dictionary.

        This is a factory method, typically used after reading data
        from a database or API request.
        
        Args:
            data (RuleEntity): Dictionary representing a rule.
            
        Returns:
            Rule: The reconstructed Rule object.
            
        Raises:
            ValueError: If the rule data is missing the logic tree or if there's an error parsing it.
            TypeError: If the purpose in metadata doesn't match the root node's return type.
        """
        root_json = data.root
        if not root_json:
            raise ValueError("Rule data is missing the logic tree 'root'.")
        
        # Use the parser to reconstruct the logic tree from the JSON structure
        try:
            root_node = parse_tree(root_json)
        except Exception as e:
            # Wrap the original error to provide additional context
            raise ValueError(f"Cannot parse logic tree for rule_id '{data.rule_id}'. Error: {e}") from e
            
        # created_at and updated_at may not be present in old data
        
        purpose_from_data = data.purpose
        if purpose_from_data:
            # Convert string from JSON to Enum
            if purpose_from_data != root_node.return_type:
                raise TypeError(
                    f"Purpose in metadata ('{purpose_from_data.name}') "
                    f"does not match the return_type of the root node ('{root_node.return_type.name}')."
                )

        return cls(
            rule_id=data.rule_id,
            name=data.name,
            description=data.description,
            rule_status=data.rule_status,
            created_at=data.created_at,
            updated_at=data.updated_at,
            # Pass the reconstructed logic tree
            root=root_node
        )
        
    def copy(self):
        return deepcopy(self)
    
    def get_hash(self) -> str:
        """
        Use SHA-1 to hash entity of rule (what can be serialized)

        Returns:
            str: Hex digest result of SHA-1
        """
        return sha1(self.to_entity()).hexdigest()
    
    def auto_id_name(self, prefix: str) -> None:
        """
        Auto fill rule id and name, match with prefix. 
        
        Rule id: `{prefix}_{SHA-1 Hash of entity}`
        
        Rule name: `{prefix.upper()} {SHA-1 Hash of entity}`

        Args:
            prefix (str): Prefix string
            
        """
        self.rule_id = f'{prefix}_{self.get_hash()}'
        self.name = f'{prefix.upper()} {self.get_hash()[:10]}....'