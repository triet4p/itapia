# itapia_common/rules/nodes/_constant_nodes_builtin.py

"""
This module defines and registers all built-in ConstantNode instances in the system.
Includes both general arithmetic constants and special financial domain constants.
"""

from typing import Set
import numpy as np
from itapia_common.rules.nodes.registry import register_node_by_spec, NodeSpec
from itapia_common.rules.nodes import ConstantNode
from itapia_common.schemas.entities.rules import SemanticType, NodeType, SemanticLevel
from itapia_common.rules import names as nms

# ===================================================================
# == A. General Arithmetic Constants (Ephemeral Random Constants - ERCs)
# == Purpose: Provide raw "building materials" for the Evo-worker.
# == Type: NUMERICAL, no specific semantics.
# ===================================================================

# Create a series of arithmetic constants from -1.0 to 1.0
const_values: Set[float] = set()
# Add detailed values in the range [-1, 1]
for value in np.round(np.arange(-1.0, 1.1, 0.1), 2):
    const_values.add(float(value))
# Add larger integer values
for value in np.round(np.arange(-5.0, 5.0, 1.0), 2):
    const_values.add(float(value))

for value in sorted(list(const_values)):
    node_name = nms.CONST_NUM(value)
    description = f"Generic numerical constant with value {value}."
    
    register_node_by_spec(
        node_name=node_name,
        spec=NodeSpec(
            node_class=ConstantNode,
            description=description,
            return_type=SemanticType.NUMERICAL,
            params={'value': float(value), 'use_normalize': False},
            node_type=NodeType.CONSTANT
        )
    )
    
SEMANTIC_THRESHOLDS = {
    SemanticLevel.HIGH: 0.55,
    SemanticLevel.MODERATE: 0.05,
    SemanticLevel.LOW: -0.4
}

CONST_SEMANTIC_TYPE_LST = SemanticType.ANY_NUMERIC.concreates

for semantic_type in CONST_SEMANTIC_TYPE_LST:
    for level in SEMANTIC_THRESHOLDS.keys():
        node_name = nms.CONST_SEMANTIC(semantic_type, level)
        value = SEMANTIC_THRESHOLDS[level]
        description = f"Semantic numerical constant with value {value} and level {level}."
        
        register_node_by_spec(
            node_name=node_name,
            spec=NodeSpec(
                node_class=ConstantNode,
                description=description,
                node_type=NodeType.CONSTANT,
                return_type=semantic_type,
                params={'value': round(value, 2), 'use_normalize': False}
            )
        )


# ===================================================================
# == B. Special Domain-Specific Constants Registration
# == These constants are technical thresholds that need normalization.
# ===================================================================

# --- Thresholds for Momentum Indicators ---

register_node_by_spec(
    node_name=nms.CONST_RSI_OVERBOUGHT,
    spec=NodeSpec(
        node_class=ConstantNode,
        description='RSI Overbought Threshold (70)',
        return_type=SemanticType.MOMENTUM,
        params={
            'value': 70.0,
            'use_normalize': True,
            'source_range': (0, 100),
            'target_range': (-1, 1),
        },
        node_type=NodeType.CONSTANT
    )
)

register_node_by_spec(
    node_name=nms.CONST_RSI_OVERSOLD,
    spec=NodeSpec(
        node_class=ConstantNode,
        description='RSI Oversold Threshold (30)',
        return_type=SemanticType.MOMENTUM,
        params={
            'value': 30.0,
            'use_normalize': True,
            'source_range': (0, 100),
            'target_range': (-1, 1)
        },
        node_type=NodeType.CONSTANT
    )
)

register_node_by_spec(
    node_name=nms.CONST_STOCH_OVERBOUGHT,
    spec=NodeSpec(
        node_class=ConstantNode,
        description='Stochastic Overbought Threshold (80)',
        return_type=SemanticType.MOMENTUM,
        params={
            'value': 80.0,
            'use_normalize': True,
            'source_range': (0, 100),
            'target_range': (-1, 1)
        },
        node_type=NodeType.CONSTANT
    )
)

register_node_by_spec(
    node_name=nms.CONST_STOCH_OVERSOLD,
    spec=NodeSpec(
        node_class=ConstantNode,
        description='Stochastic Oversold Threshold (20)',
        return_type=SemanticType.MOMENTUM,
        params={
            'value': 20.0,
            'use_normalize': True,
            'source_range': (0, 100),
            'target_range': (-1, 1)
        },
        node_type=NodeType.CONSTANT
    )
)

# --- Thresholds for Trend Indicators ---

register_node_by_spec(
    node_name=nms.CONST_ADX_STRONG_TREND,
    spec=NodeSpec(
        node_class=ConstantNode,
        description='ADX Strong Trend Threshold (25)',
        return_type=SemanticType.TREND,
        params={
            'value': 25.0,
            'use_normalize': True,
            'source_range': (0, 100),  # ADX is also in the range 0-100
            'target_range': (-1, 1)
        },
        node_type=NodeType.CONSTANT
    )
)

register_node_by_spec(
    node_name=nms.CONST_ATR_STRONG_TREND,
    spec=NodeSpec(
        node_class=ConstantNode,
        description='ATR Strong Trend Threshold (25)',
        return_type=SemanticType.TREND,
        params={
            'value': 0.9,
            'use_normalize': True,
            'source_range': (0, 1),  # ATR is also in the range 0-100
            'target_range': (-1, 1)
        },
        node_type=NodeType.CONSTANT
    )
)

