# Layer: L5 — Domain Engines
# AUDIENCE: CUSTOMER
# Role: integrations domain - engines (business logic, decisions)
# Reference: HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md

"""
integrations / engines

L5 Engine exports for the integrations domain.
"""

from .prevention_contract import (
    PREVENTION_CONTRACT_FROZEN_AT,
    PREVENTION_CONTRACT_VERSION,
    PreventionCandidate,
    PreventionContractViolation,
    assert_no_deletion,
    assert_prevention_immutable,
    validate_prevention_candidate,
    validate_prevention_for_graduation,
)
from .learning_proof_engine import (
    AdaptiveConfidenceSystem,
    CheckpointConfig,
    CheckpointPriority,
    GlobalRegretTracker,
    M25GraduationStatus,
    PatternCalibration,
    PolicyRegretTracker,
    PreventionOutcome,
    PreventionRecord,
    PreventionTimeline,
    PreventionTracker,
    PrioritizedCheckpoint,
    RegretEvent,
    RegretType,
)
from .cost_bridges_engine import (
    AnomalySeverity,
    AnomalyType,
    CostAnomaly,
    CostEstimationProbe,
    CostLoopBridge,
    CostLoopOrchestrator,
    CostPatternMatcher,
    CostPolicyGenerator,
    CostRecoveryGenerator,
    CostRoutingAdjuster,
)

__all__ = [
    # prevention_contract
    "PREVENTION_CONTRACT_FROZEN_AT",
    "PREVENTION_CONTRACT_VERSION",
    "PreventionCandidate",
    "PreventionContractViolation",
    "assert_no_deletion",
    "assert_prevention_immutable",
    "validate_prevention_candidate",
    "validate_prevention_for_graduation",
    # learning_proof_engine
    "AdaptiveConfidenceSystem",
    "CheckpointConfig",
    "CheckpointPriority",
    "GlobalRegretTracker",
    "M25GraduationStatus",
    "PatternCalibration",
    "PolicyRegretTracker",
    "PreventionOutcome",
    "PreventionRecord",
    "PreventionTimeline",
    "PreventionTracker",
    "PrioritizedCheckpoint",
    "RegretEvent",
    "RegretType",
    # cost_bridges_engine
    "AnomalySeverity",
    "AnomalyType",
    "CostAnomaly",
    "CostEstimationProbe",
    "CostLoopBridge",
    "CostLoopOrchestrator",
    "CostPatternMatcher",
    "CostPolicyGenerator",
    "CostRecoveryGenerator",
    "CostRoutingAdjuster",
]
