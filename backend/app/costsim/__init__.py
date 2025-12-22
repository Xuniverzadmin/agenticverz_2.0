# CostSim V2 Package (M6)
"""
Cost Simulation V2 with sandbox evaluation path.

Components:
- v2_adapter: CostSimV2Adapter for enhanced simulation
- provenance: Full provenance logging
- canary: Daily canary runner
- sandbox: Sandbox routing via feature flag
- circuit_breaker: Auto-disable on drift
- metrics: Drift detection metrics
- divergence: Divergence reporting
- datasets: Reference dataset validation
"""

from app.costsim.canary import CanaryRunConfig, CanaryRunner, run_canary
from app.costsim.cb_sync_wrapper import (
    get_state_sync,
    is_v2_disabled_sync,
)
from app.costsim.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    Incident,
    disable_v2,
    enable_v2,
    get_circuit_breaker,
    is_v2_disabled,
)
from app.costsim.circuit_breaker_async import (
    AsyncCircuitBreaker,
    get_async_circuit_breaker,
)
from app.costsim.circuit_breaker_async import (
    disable_v2 as disable_v2_async,
)
from app.costsim.circuit_breaker_async import (
    enable_v2 as enable_v2_async,
)
from app.costsim.circuit_breaker_async import (
    is_v2_disabled as is_v2_disabled_async,
)
from app.costsim.circuit_breaker_async import (
    report_drift as report_drift_async,
)
from app.costsim.config import CostSimConfig, is_v2_disabled_by_drift, is_v2_sandbox_enabled
from app.costsim.divergence import DivergenceAnalyzer, generate_divergence_report
from app.costsim.leader import (
    LOCK_ALERT_WORKER,
    LOCK_CANARY_RUNNER,
    leader_election,
    with_alert_worker_lock,
    with_canary_lock,
)
from app.costsim.metrics import CostSimMetrics, get_alert_rules, get_metrics
from app.costsim.models import (
    CanaryReport,
    ComparisonResult,
    ComparisonVerdict,
    DiffResult,
    DivergenceReport,
    V2SimulationResult,
    V2SimulationStatus,
    ValidationResult,
)
from app.costsim.provenance import ProvenanceLog, ProvenanceLogger, get_provenance_logger
from app.costsim.sandbox import CostSimSandbox, SandboxResult, simulate_with_sandbox
from app.costsim.v2_adapter import CostSimV2Adapter, simulate_v2, simulate_v2_with_comparison

__all__ = [
    # Config
    "CostSimConfig",
    "is_v2_sandbox_enabled",
    "is_v2_disabled_by_drift",
    # V2 Adapter
    "CostSimV2Adapter",
    "simulate_v2",
    "simulate_v2_with_comparison",
    # Provenance
    "ProvenanceLogger",
    "ProvenanceLog",
    "get_provenance_logger",
    # Sandbox
    "CostSimSandbox",
    "SandboxResult",
    "simulate_with_sandbox",
    # Circuit Breaker (sync - legacy)
    "CircuitBreaker",
    "CircuitBreakerState",
    "Incident",
    "get_circuit_breaker",
    "is_v2_disabled",
    "disable_v2",
    "enable_v2",
    # Circuit Breaker (async - preferred)
    "is_v2_disabled_async",
    "disable_v2_async",
    "enable_v2_async",
    "report_drift_async",
    "get_async_circuit_breaker",
    "AsyncCircuitBreaker",
    # Circuit Breaker (sync wrapper - safe from any context)
    "is_v2_disabled_sync",
    "get_state_sync",
    # Leader Election
    "leader_election",
    "LOCK_CANARY_RUNNER",
    "LOCK_ALERT_WORKER",
    "with_canary_lock",
    "with_alert_worker_lock",
    # Canary
    "CanaryRunner",
    "CanaryRunConfig",
    "run_canary",
    # Divergence
    "DivergenceAnalyzer",
    "generate_divergence_report",
    # Metrics
    "CostSimMetrics",
    "get_metrics",
    "get_alert_rules",
    # Models
    "V2SimulationResult",
    "V2SimulationStatus",
    "ComparisonResult",
    "ComparisonVerdict",
    "DiffResult",
    "CanaryReport",
    "DivergenceReport",
    "ValidationResult",
]
