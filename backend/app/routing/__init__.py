# M17 - Cascade-Aware Routing Engine (CARE)
# Strategic router that routes based on agent Strategy Cascade

from .care import (
    CAREEngine,
    get_care_engine,
    FairnessTracker,
    get_fairness_tracker,
    PerformanceStore,
    get_performance_store,
)
from .models import (
    AgentPerformanceVector,
    CapabilityCheckResult,
    CapabilityHardness,
    CapabilityProbeResult,
    CONFIDENCE_BLOCK_THRESHOLD,
    CONFIDENCE_FALLBACK_THRESHOLD,
    DifficultyLevel,
    FAIRNESS_WINDOW,
    OrchestratorMode,
    RiskPolicy,
    RouteEvaluationResult,
    RoutingDecision,
    RoutingOutcome,
    RoutingRequest,
    RoutingStage,
    STAGE_CONFIDENCE_WEIGHTS,
    SuccessMetric,
)
from .probes import CapabilityProber, get_capability_prober

__all__ = [
    # Engine
    "CAREEngine",
    "get_care_engine",
    # M17.2 - Fairness & Performance
    "FairnessTracker",
    "get_fairness_tracker",
    "PerformanceStore",
    "get_performance_store",
    "AgentPerformanceVector",
    "RoutingOutcome",
    # M17.2 - Confidence
    "STAGE_CONFIDENCE_WEIGHTS",
    "CONFIDENCE_BLOCK_THRESHOLD",
    "CONFIDENCE_FALLBACK_THRESHOLD",
    "FAIRNESS_WINDOW",
    # Core models
    "RoutingDecision",
    "RoutingRequest",
    "RoutingStage",
    "SuccessMetric",
    "OrchestratorMode",
    "RiskPolicy",
    "DifficultyLevel",
    # Capability probes
    "CapabilityProbeResult",
    "CapabilityHardness",
    "CapabilityCheckResult",
    "RouteEvaluationResult",
    "CapabilityProber",
    "get_capability_prober",
]
