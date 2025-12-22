# M20 Policy Optimizer
# Governance-aware IR optimization
#
# Optimizer v2.0 features:
# - Constant folding
# - Dead code elimination
# - Conflict resolution
# - DAG-based execution ordering
# - Category priority propagation

from app.policy.optimizer.conflict_resolver import (
    ConflictResolver,
    ConflictType,
    PolicyConflict,
)
from app.policy.optimizer.dag_sorter import (
    DAGSorter,
    ExecutionDAG,
    ExecutionNode,
)
from app.policy.optimizer.folds import (
    ConstantFolder,
    DeadCodeEliminator,
    PolicySimplifier,
)

__all__ = [
    # Folds
    "ConstantFolder",
    "DeadCodeEliminator",
    "PolicySimplifier",
    # Conflict resolution
    "ConflictType",
    "PolicyConflict",
    "ConflictResolver",
    # DAG sorting
    "ExecutionNode",
    "ExecutionDAG",
    "DAGSorter",
]
