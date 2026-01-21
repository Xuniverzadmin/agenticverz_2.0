# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Trace data models
# Callers: traces/*
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Trace System

"""
Trace Models for AOS
M6 Deliverable: Run traces with correlation IDs

These models define the structure of execution traces used for:
- Debugging and inspection
- Replay verification
- Determinism testing

Determinism Invariant (PIN-126):
- Given the same trace input, replay must produce identical output hash
- Or fail loudly with a classified reason
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar


def _normalize_for_determinism(value: Any) -> Any:
    """
    Normalize a value for deterministic hashing.

    Handles:
    - Floats: Round to 6 decimal places to avoid precision drift
    - Dicts: Recursively normalize values
    - Lists: Recursively normalize elements
    - Other types: Pass through unchanged
    """
    if isinstance(value, float):
        return round(value, 6)
    elif isinstance(value, dict):
        return {k: _normalize_for_determinism(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_normalize_for_determinism(v) for v in value]
    return value


class TraceStatus(str, Enum):
    """Status of a trace step."""

    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    SKIPPED = "skipped"


@dataclass
class TraceStep:
    """
    A single step in an execution trace.

    Captures everything needed to replay and verify determinism.
    """

    step_index: int
    skill_name: str
    params: dict[str, Any]
    status: TraceStatus
    outcome_category: str  # SUCCESS, TRANSIENT, PERMANENT, etc.
    outcome_code: str | None  # Error code if failure
    outcome_data: dict[str, Any] | None  # Actual result data
    cost_cents: float
    duration_ms: float
    retry_count: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Determinism fields (excluded from content hash)
    _determinism_fields = {
        "step_index",
        "skill_name",
        "params",
        "status",
        "outcome_category",
        "outcome_code",
        "retry_count",
    }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "step_index": self.step_index,
            "skill_name": self.skill_name,
            "params": self.params,
            "status": self.status.value,
            "outcome_category": self.outcome_category,
            "outcome_code": self.outcome_code,
            "outcome_data": self.outcome_data,
            "cost_cents": self.cost_cents,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceStep":
        """Create from dictionary."""
        return cls(
            step_index=data["step_index"],
            skill_name=data["skill_name"],
            params=data["params"],
            status=TraceStatus(data["status"]),
            outcome_category=data["outcome_category"],
            outcome_code=data.get("outcome_code"),
            outcome_data=data.get("outcome_data"),
            cost_cents=data["cost_cents"],
            duration_ms=data["duration_ms"],
            retry_count=data["retry_count"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )

    def determinism_hash(self) -> str:
        """
        Compute hash of determinism-relevant fields only.

        This hash should be identical for replayed runs with same inputs.
        Floats are normalized to 6 decimal places to avoid precision drift.
        """
        relevant = {k: getattr(self, k) for k in self._determinism_fields}
        # Normalize all values for deterministic hashing (handles floats, nested dicts)
        relevant = _normalize_for_determinism(relevant)
        # Normalize params for consistent hashing
        if "params" in relevant:
            relevant["params"] = json.dumps(relevant["params"], sort_keys=True)
        canonical = json.dumps(relevant, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@dataclass
class TraceSummary:
    """
    Summary of a trace for listing purposes.

    Inflection Fields (BACKEND_REMEDIATION_PLAN GAP-003):
    - violation_step_index: Step where policy violation occurred
    - violation_timestamp: When the violation was detected
    - violation_policy_id: ID of the violated policy
    - violation_reason: Human-readable violation description
    """

    run_id: str
    correlation_id: str
    tenant_id: str
    agent_id: str | None
    total_steps: int
    success_count: int
    failure_count: int
    total_cost_cents: float
    total_duration_ms: float
    started_at: datetime
    completed_at: datetime | None
    status: str  # "running", "completed", "failed"

    # Inflection point fields (GAP-003: mark exact step/timestamp of violation)
    violation_step_index: int | None = None
    violation_timestamp: datetime | None = None
    violation_policy_id: str | None = None
    violation_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "tenant_id": self.tenant_id,
            "agent_id": self.agent_id,
            "total_steps": self.total_steps,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_cost_cents": self.total_cost_cents,
            "total_duration_ms": self.total_duration_ms,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            # Inflection point fields
            "violation_step_index": self.violation_step_index,
            "violation_timestamp": self.violation_timestamp.isoformat() if self.violation_timestamp else None,
            "violation_policy_id": self.violation_policy_id,
            "violation_reason": self.violation_reason,
        }


@dataclass
class TraceRecord:
    """
    Complete trace record with all steps.

    Used for replay verification and debugging.

    v1.1 Determinism fields:
    - seed: Random seed for deterministic simulation
    - frozen_timestamp: Frozen time for deterministic context
    - root_hash: Merkle root of deterministic fields (for replay verification)

    v1.2 Schema versioning (PIN-126):
    - SCHEMA_VERSION: Version of trace format for compatibility checks
    - schema_version in to_dict(): Included in serialization
    - checksum: determinism_signature() for integrity verification
    """

    # Schema version for trace format compatibility (PIN-126)
    SCHEMA_VERSION: ClassVar[str] = "1.0.0"

    run_id: str
    correlation_id: str
    tenant_id: str
    agent_id: str | None
    plan: list[dict[str, Any]]  # Original plan
    steps: list[TraceStep]
    started_at: datetime
    completed_at: datetime | None
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)
    # Determinism fields (v1.1)
    seed: int = 42
    frozen_timestamp: str | None = None
    root_hash: str | None = None

    @property
    def total_cost_cents(self) -> float:
        """Sum of all step costs."""
        return sum(s.cost_cents for s in self.steps)

    @property
    def total_duration_ms(self) -> float:
        """Sum of all step durations."""
        return sum(s.duration_ms for s in self.steps)

    @property
    def success_count(self) -> int:
        """Count of successful steps."""
        return sum(1 for s in self.steps if s.status == TraceStatus.SUCCESS)

    @property
    def failure_count(self) -> int:
        """Count of failed steps."""
        return sum(1 for s in self.steps if s.status == TraceStatus.FAILURE)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            # Schema version for compatibility (PIN-126)
            "schema_version": self.SCHEMA_VERSION,
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "tenant_id": self.tenant_id,
            "agent_id": self.agent_id,
            "plan": self.plan,
            "steps": [s.to_dict() for s in self.steps],
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "metadata": self.metadata,
            # Determinism fields (v1.1)
            "seed": self.seed,
            "frozen_timestamp": self.frozen_timestamp,
            "root_hash": self.root_hash,
            # Integrity checksum (PIN-126)
            "checksum": self.determinism_signature(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceRecord":
        """Create from dictionary."""
        return cls(
            run_id=data["run_id"],
            correlation_id=data["correlation_id"],
            tenant_id=data["tenant_id"],
            agent_id=data.get("agent_id"),
            plan=data["plan"],
            steps=[TraceStep.from_dict(s) for s in data["steps"]],
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            status=data["status"],
            metadata=data.get("metadata", {}),
            # Determinism fields (v1.1)
            seed=data.get("seed", 42),
            frozen_timestamp=data.get("frozen_timestamp"),
            root_hash=data.get("root_hash"),
        )

    def to_summary(self) -> TraceSummary:
        """Create a summary from this record."""
        return TraceSummary(
            run_id=self.run_id,
            correlation_id=self.correlation_id,
            tenant_id=self.tenant_id,
            agent_id=self.agent_id,
            total_steps=len(self.steps),
            success_count=self.success_count,
            failure_count=self.failure_count,
            total_cost_cents=self.total_cost_cents,
            total_duration_ms=self.total_duration_ms,
            started_at=self.started_at,
            completed_at=self.completed_at,
            status=self.status,
        )

    def determinism_signature(self) -> str:
        """
        Compute signature of all determinism-relevant fields.

        Two replayed runs should have identical signatures if determinism holds.
        """
        step_hashes = [s.determinism_hash() for s in self.steps]
        combined = ":".join(step_hashes)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]


@dataclass
class ParityResult:
    """Result of comparing two traces for replay parity."""

    is_parity: bool
    original_signature: str
    replay_signature: str
    divergence_step: int | None  # First step that diverged
    divergence_reason: str | None  # Why it diverged

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_parity": self.is_parity,
            "original_signature": self.original_signature,
            "replay_signature": self.replay_signature,
            "divergence_step": self.divergence_step,
            "divergence_reason": self.divergence_reason,
        }


def compare_traces(original: TraceRecord, replay: TraceRecord) -> ParityResult:
    """
    Compare two traces to verify replay parity.

    Checks:
    - Same number of steps
    - Same skill calls in same order
    - Same parameters
    - Same status (success/failure)
    - Same retry counts

    Does NOT check:
    - outcome_data (external responses vary)
    - timestamps (always different)
    - duration_ms (timing varies)
    - cost_cents (may vary with pricing changes)
    """
    original_sig = original.determinism_signature()
    replay_sig = replay.determinism_signature()

    if original_sig == replay_sig:
        return ParityResult(
            is_parity=True,
            original_signature=original_sig,
            replay_signature=replay_sig,
            divergence_step=None,
            divergence_reason=None,
        )

    # Find divergence point
    for i, (orig_step, replay_step) in enumerate(zip(original.steps, replay.steps)):
        if orig_step.determinism_hash() != replay_step.determinism_hash():
            reasons = []
            if orig_step.skill_name != replay_step.skill_name:
                reasons.append(f"skill: {orig_step.skill_name} vs {replay_step.skill_name}")
            if orig_step.status != replay_step.status:
                reasons.append(f"status: {orig_step.status} vs {replay_step.status}")
            if orig_step.retry_count != replay_step.retry_count:
                reasons.append(f"retries: {orig_step.retry_count} vs {replay_step.retry_count}")
            if json.dumps(orig_step.params, sort_keys=True) != json.dumps(replay_step.params, sort_keys=True):
                reasons.append("params differ")

            return ParityResult(
                is_parity=False,
                original_signature=original_sig,
                replay_signature=replay_sig,
                divergence_step=i,
                divergence_reason="; ".join(reasons) if reasons else "hash mismatch",
            )

    # Different number of steps
    if len(original.steps) != len(replay.steps):
        return ParityResult(
            is_parity=False,
            original_signature=original_sig,
            replay_signature=replay_sig,
            divergence_step=min(len(original.steps), len(replay.steps)),
            divergence_reason=f"step count: {len(original.steps)} vs {len(replay.steps)}",
        )

    # Shouldn't reach here if signatures differ
    return ParityResult(
        is_parity=False,
        original_signature=original_sig,
        replay_signature=replay_sig,
        divergence_step=None,
        divergence_reason="unknown divergence",
    )
