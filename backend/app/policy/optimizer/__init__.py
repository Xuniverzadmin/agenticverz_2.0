# M20 Policy Optimizer
# Governance-aware IR optimization
#
# Optimizer v2.0 features:
# - Constant folding
# - Dead code elimination
# - Conflict resolution
# - DAG-based execution ordering
# - Category priority propagation

from app.policy.optimizer.folds import (
    ConstantFolder,
    DeadCodeEliminator,
    PolicySimplifier,
)
from app.policy.optimizer.conflict_resolver import (
    ConflictType,
    PolicyConflict,
    ConflictResolver,
)
from app.policy.optimizer.dag_sorter import (
    ExecutionNode,
    ExecutionDAG,
    DAGSorter,
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
