# Layer: L4 — HOC Spine (Schemas)
# AUDIENCE: CUSTOMER
# Role: Protocol interfaces for run introspection — dependency inversion contracts
# Reference: PIN-519 System Run Introspection
# artifact_class: CODE

"""
Run Introspection Protocol Interfaces (PIN-519)

These Protocols define the behavioral contracts for run introspection:
- RunEvidenceProvider: Cross-domain impact for a run
- RunProofProvider: Integrity verification for a run
- SignalFeedbackProvider: Signal feedback status queries

Each Protocol is implemented by L4 coordinators and consumed by L5 facades.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Protocol, runtime_checkable


# =============================================================================
# Integrity Configuration (System-Wide Declaration)
# =============================================================================

INTEGRITY_CONFIG = {
    "model": "HASH_CHAIN",  # NONE | HASH_CHAIN | MERKLE_TREE
    "trust_boundary": "SYSTEM",  # LOCAL | SYSTEM
    "storage": "POSTGRES",  # SQLITE | POSTGRES
}


# =============================================================================
# Result Dataclasses
# =============================================================================


@dataclass(frozen=True)
class IncidentSummary:
    """Summary of an incident caused by a run."""

    incident_id: str
    severity: str
    title: str
    created_at: datetime


@dataclass(frozen=True)
class PolicyEvaluationSummary:
    """Summary of a policy evaluation for a run."""

    policy_id: str
    policy_name: str
    outcome: str
    evaluated_at: datetime


@dataclass(frozen=True)
class LimitHitSummary:
    """Summary of a limit breach for a run."""

    limit_id: str
    limit_name: str
    breached_value: float
    threshold_value: float
    breached_at: datetime


@dataclass(frozen=True)
class DecisionSummary:
    """Summary of a decision made during a run."""

    decision_id: str
    decision_type: str
    outcome: str
    decided_at: datetime


@dataclass(frozen=True)
class RunEvidenceResult:
    """
    Cross-domain impact evidence for a run.

    Aggregates incidents, policy evaluations, limit breaches,
    and decisions related to a specific run.
    """

    run_id: str
    incidents_caused: list[IncidentSummary] = field(default_factory=list)
    policies_evaluated: list[PolicyEvaluationSummary] = field(default_factory=list)
    limits_hit: list[LimitHitSummary] = field(default_factory=list)
    decisions_made: list[DecisionSummary] = field(default_factory=list)
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class IntegrityVerificationResult:
    """
    Integrity verification status for a run's trace chain.

    Supports HASH_CHAIN (Phase 1) and MERKLE_TREE (future).
    """

    model: Literal["HASH_CHAIN", "MERKLE_TREE", "NONE"]
    root_hash: str | None
    chain_length: int
    verification_status: Literal["VERIFIED", "FAILED", "UNSUPPORTED"]
    failure_reason: str | None = None


@dataclass(frozen=True)
class TraceSummary:
    """Summary of a trace record."""

    trace_id: str
    run_id: str
    status: str
    step_count: int
    started_at: datetime
    completed_at: datetime | None


@dataclass(frozen=True)
class TraceStepSummary:
    """Summary of a trace step."""

    step_index: int
    skill_name: str
    status: str
    duration_ms: float
    cost_cents: float


@dataclass(frozen=True)
class RunProofResult:
    """
    Integrity proof for a run.

    Contains trace data and integrity verification results.
    """

    run_id: str
    integrity: IntegrityVerificationResult
    aos_traces: list[TraceSummary] = field(default_factory=list)
    aos_trace_steps: list[TraceStepSummary] = field(default_factory=list)
    raw_logs: list[str] | None = None
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class SignalFeedbackResult:
    """
    Feedback status for a signal from audit ledger.

    Tracks acknowledgment and suppression state.
    """

    acknowledged: bool = False
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    suppressed: bool = False
    suppressed_until: datetime | None = None
    escalated: bool = False
    escalated_at: datetime | None = None


# =============================================================================
# Protocol Definitions
# =============================================================================


@runtime_checkable
class RunEvidenceProvider(Protocol):
    """
    Behavioral contract for run evidence queries.

    Implemented by: RunEvidenceCoordinator (L4)
    Consumed by: ActivityFacade (L5)
    Wired by: L4 orchestrator context
    """

    async def get_run_evidence(
        self,
        *,
        session: Any,
        tenant_id: str,
        run_id: str,
    ) -> RunEvidenceResult:
        """Get cross-domain impact evidence for a run."""
        ...


@runtime_checkable
class RunProofProvider(Protocol):
    """
    Behavioral contract for run integrity proof queries.

    Implemented by: RunProofCoordinator (L4)
    Consumed by: ActivityFacade (L5)
    Wired by: L4 orchestrator context
    """

    async def get_run_proof(
        self,
        *,
        session: Any,
        tenant_id: str,
        run_id: str,
        include_payloads: bool = False,
    ) -> RunProofResult:
        """Get integrity proof for a run."""
        ...


@runtime_checkable
class SignalFeedbackProvider(Protocol):
    """
    Behavioral contract for signal feedback queries.

    Implemented by: SignalFeedbackCoordinator (L4)
    Consumed by: ActivityFacade (L5)
    Wired by: L4 orchestrator context
    """

    async def get_signal_feedback(
        self,
        *,
        session: Any,
        tenant_id: str,
        signal_fingerprint: str,
    ) -> SignalFeedbackResult | None:
        """Get feedback status for a signal from audit ledger."""
        ...


__all__ = [
    # Config
    "INTEGRITY_CONFIG",
    # Result types
    "IncidentSummary",
    "PolicyEvaluationSummary",
    "LimitHitSummary",
    "DecisionSummary",
    "RunEvidenceResult",
    "IntegrityVerificationResult",
    "TraceSummary",
    "TraceStepSummary",
    "RunProofResult",
    "SignalFeedbackResult",
    # Protocols
    "RunEvidenceProvider",
    "RunProofProvider",
    "SignalFeedbackProvider",
]
