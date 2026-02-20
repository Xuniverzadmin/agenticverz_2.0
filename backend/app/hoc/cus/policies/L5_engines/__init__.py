# capability_id: CAP-009
# Layer: L5 — Domain Engines
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: import
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: policies domain - engines
# Callers: L2 APIs, L3 adapters
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, DIRECTORY_REORGANIZATION_PLAN.md

"""
policies / engines

M20 Policy Runtime exports (PIN-514):
- IntentEmitter, Intent, IntentPayload, IntentType
- DeterministicEngine, ExecutionContext, ExecutionResult
- DAGExecutor, StageResult, ExecutionTrace
"""

from app.hoc.cus.policies.L5_engines.intent import (
    Intent,
    IntentEmitter,
    IntentPayload,
    IntentType,
)
from app.hoc.cus.policies.L5_engines.deterministic_engine import (
    DeterministicEngine,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
)
from app.hoc.cus.policies.L5_engines.dag_executor import (
    DAGExecutor,
    ExecutionTrace,
    StageResult,
)

__all__ = [
    # Intent system
    "IntentType",
    "Intent",
    "IntentPayload",
    "IntentEmitter",
    # Deterministic engine
    "ExecutionStatus",
    "ExecutionContext",
    "ExecutionResult",
    "DeterministicEngine",
    # DAG executor
    "DAGExecutor",
    "StageResult",
    "ExecutionTrace",
]
