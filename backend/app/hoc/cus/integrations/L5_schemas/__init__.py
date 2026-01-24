# Layer: L5 — Domain Schemas
# AUDIENCE: CUSTOMER
# Role: integrations domain - schemas (dataclasses, Pydantic models)
# Reference: HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md

"""
integrations / schemas

L5 Schema exports for the integrations domain.
"""

from .audit_schemas import PolicyActivationAudit
from .cost_snapshot_schemas import (
    SEVERITY_THRESHOLDS,
    AnomalyEvaluation,
    CostSnapshot,
    EntityType,
    SnapshotAggregate,
    SnapshotBaseline,
    SnapshotStatus,
    SnapshotType,
)
from .loop_events import (
    LOOP_MECHANICS_FROZEN_AT,
    LOOP_MECHANICS_VERSION,
    ConfidenceBand,
    ConfidenceCalculator,
    HumanCheckpoint,
    HumanCheckpointType,
    LoopEvent,
    LoopFailureState,
    LoopStage,
    LoopStatus,
    PatternMatchResult,
    PolicyMode,
    PolicyRule,
    RecoverySuggestion,
    RoutingAdjustment,
    ensure_json_serializable,
)

__all__ = [
    # audit_schemas
    "PolicyActivationAudit",
    # cost_snapshot_schemas
    "SEVERITY_THRESHOLDS",
    "AnomalyEvaluation",
    "CostSnapshot",
    "EntityType",
    "SnapshotAggregate",
    "SnapshotBaseline",
    "SnapshotStatus",
    "SnapshotType",
    # loop_events
    "LOOP_MECHANICS_FROZEN_AT",
    "LOOP_MECHANICS_VERSION",
    "ConfidenceBand",
    "ConfidenceCalculator",
    "HumanCheckpoint",
    "HumanCheckpointType",
    "LoopEvent",
    "LoopFailureState",
    "LoopStage",
    "LoopStatus",
    "PatternMatchResult",
    "PolicyMode",
    "PolicyRule",
    "RecoverySuggestion",
    "RoutingAdjustment",
    "ensure_json_serializable",
]
