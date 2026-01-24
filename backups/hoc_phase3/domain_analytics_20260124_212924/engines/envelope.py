# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: sync
# Role: Base optimization envelope definition
# Callers: optimization/*
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: M10 Optimization

# C3/C4 Optimization Envelope
# Reference: C3_ENVELOPE_ABSTRACTION.md (FROZEN), C4_ENVELOPE_COORDINATION_CONTRACT.md (FROZEN)
#
# The envelope is the ONLY legal interface through which predictions
# may influence system behavior. Predictions never modify behavior directly.
#
# Envelope guarantees:
# - Bounded impact
# - Bounded time
# - Reversibility
# - Auditability
#
# C4 additions:
# - Envelope class (SAFETY, RELIABILITY, COST, PERFORMANCE)
# - Priority order (SAFETY > RELIABILITY > COST > PERFORMANCE)
# - Coordination rules enforcement
#
# If any are missing, C3/C4 is invalid.

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger("nova.optimization.envelope")


class DeltaType(str, Enum):
    """How bounds are expressed."""

    PCT = "pct"  # Percentage change
    ABSOLUTE = "absolute"  # Absolute value change


class EnvelopeClass(str, Enum):
    """
    C4 Envelope Class (FROZEN priority order).

    Reference: C4_ENVELOPE_COORDINATION_CONTRACT.md Section 4

    Priority order (immutable):
        SAFETY > RELIABILITY > COST > PERFORMANCE

    Higher priority always dominates lower priority.
    No dynamic reprioritization. No confidence-based overrides.
    """

    SAFETY = "safety"  # Reduces risk / blast radius (priority 1)
    RELIABILITY = "reliability"  # Improves stability / retries (priority 2)
    COST = "cost"  # Reduces spend / throughput (priority 3)
    PERFORMANCE = "performance"  # Improves latency / speed (priority 4)


# C4 Priority Order (FROZEN - DO NOT MODIFY)
# Reference: C4_ENVELOPE_COORDINATION_CONTRACT.md Section 4
ENVELOPE_CLASS_PRIORITY: Dict[EnvelopeClass, int] = {
    EnvelopeClass.SAFETY: 1,  # Highest priority
    EnvelopeClass.RELIABILITY: 2,
    EnvelopeClass.COST: 3,
    EnvelopeClass.PERFORMANCE: 4,  # Lowest priority
}


def get_envelope_priority(envelope_class: EnvelopeClass) -> int:
    """Get the priority of an envelope class (lower number = higher priority)."""
    return ENVELOPE_CLASS_PRIORITY[envelope_class]


def has_higher_priority(class_a: EnvelopeClass, class_b: EnvelopeClass) -> bool:
    """Check if class_a has higher priority than class_b."""
    return get_envelope_priority(class_a) < get_envelope_priority(class_b)


class BaselineSource(str, Enum):
    """Where baseline value comes from."""

    CONFIG_DEFAULT = "config_default"  # From configuration
    LAST_KNOWN_GOOD = "last_known_good"  # From last successful state


class EnvelopeLifecycle(str, Enum):
    """
    Fixed envelope lifecycle states.

    Lifecycle invariants:
    - Envelope may only be Applied once
    - Envelope may only be Active within timebox
    - Envelope must always end in Reverted or Expired
    - No terminal "active" state
    """

    DECLARED = "declared"  # Created but not validated
    VALIDATED = "validated"  # Passed validation rules
    APPLIED = "applied"  # Being applied
    ACTIVE = "active"  # Currently influencing behavior
    EXPIRED = "expired"  # Timebox ended naturally
    REVERTED = "reverted"  # Explicitly reverted (kill-switch, error, etc.)


class RevertReason(str, Enum):
    """Why an envelope was reverted."""

    PREDICTION_EXPIRED = "prediction_expired"
    PREDICTION_DELETED = "prediction_deleted"
    KILL_SWITCH = "kill_switch"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_RESTART = "system_restart"
    TIMEBOX_EXPIRED = "timebox_expired"
    # C4 additions
    PREEMPTED = "preempted"  # Higher priority envelope took precedence
    COORDINATION_CONFLICT = "coordination_conflict"  # Same-parameter conflict


@dataclass
class EnvelopeTrigger:
    """What prediction triggers this envelope."""

    prediction_type: str  # C2 prediction type (e.g., "incident_risk")
    min_confidence: float  # Advisory threshold only (0.0-1.0)


@dataclass
class EnvelopeScope:
    """What this envelope affects."""

    target_subsystem: str  # e.g., "retry_policy", "scheduler"
    target_parameter: str  # Single parameter ONLY


@dataclass
class EnvelopeBounds:
    """Numerical bounds for the envelope."""

    delta_type: DeltaType  # pct or absolute
    max_increase: float  # Upper bound
    max_decrease: float  # Lower bound
    absolute_ceiling: Optional[float] = None  # Hard stop (optional)


@dataclass
class EnvelopeTimebox:
    """Time constraints for the envelope."""

    max_duration_seconds: int  # REQUIRED, must be finite
    hard_expiry: bool = True  # Must revert automatically


@dataclass
class EnvelopeBaseline:
    """Baseline value reference."""

    source: BaselineSource  # Where value comes from
    reference_id: str  # Version or hash
    value: Optional[float] = None  # Cached baseline value


@dataclass
class EnvelopeAuditRecord:
    """
    Immutable audit record for envelope lifecycle.

    Required by C3_ENVELOPE_ABSTRACTION.md section 7.
    """

    envelope_id: str
    envelope_version: str
    prediction_id: str
    target_subsystem: str
    target_parameter: str
    baseline_value: float
    applied_value: float
    applied_at: datetime
    reverted_at: Optional[datetime] = None
    revert_reason: Optional[RevertReason] = None


class CoordinationDecisionType(str, Enum):
    """C4 coordination decision types."""

    APPLIED = "applied"  # Envelope was allowed to apply
    REJECTED = "rejected"  # Envelope was rejected (conflict)
    PREEMPTED = "preempted"  # Envelope was preempted by higher priority


@dataclass
class CoordinationAuditRecord:
    """
    C4 Coordination audit record.

    Required by C4_ENVELOPE_COORDINATION_CONTRACT.md Section 7.
    Every coordination decision must emit this record.
    """

    audit_id: str
    envelope_id: str
    envelope_class: EnvelopeClass
    decision: CoordinationDecisionType
    reason: str
    timestamp: datetime
    conflicting_envelope_id: Optional[str] = None
    preempting_envelope_id: Optional[str] = None
    active_envelopes_count: int = 0


@dataclass
class CoordinationDecision:
    """
    Result of a coordination check.

    Used by CoordinationManager.check_allowed() to communicate
    whether an envelope may apply.
    """

    allowed: bool
    decision: CoordinationDecisionType
    reason: str
    conflicting_envelope_id: Optional[str] = None
    preempting_envelope_id: Optional[str] = None


@dataclass
class Envelope:
    """
    Declarative optimization envelope.

    Nothing implicit. Nothing inferred.
    If any required field is missing, the envelope is INVALID.

    C4 additions:
    - envelope_class: Required classification (SAFETY/RELIABILITY/COST/PERFORMANCE)
    """

    # Identity (immutable, versioned)
    envelope_id: str
    envelope_version: str  # semver (e.g., "1.0.0")

    # What triggers this envelope
    trigger: EnvelopeTrigger

    # What it affects (single parameter only)
    scope: EnvelopeScope

    # Numerical bounds
    bounds: EnvelopeBounds

    # Time constraints
    timebox: EnvelopeTimebox

    # Baseline reference
    baseline: EnvelopeBaseline

    # C4: Envelope classification (REQUIRED by CI-C4-1, validated at runtime)
    # Optional in dataclass to maintain backwards compatibility with C3
    envelope_class: Optional[EnvelopeClass] = None

    # Revert policy
    revert_on: List[RevertReason] = field(default_factory=list)

    # Audit settings
    audit_enabled: bool = True

    # Runtime state (not part of declaration)
    lifecycle: EnvelopeLifecycle = EnvelopeLifecycle.DECLARED
    applied_at: Optional[datetime] = None
    reverted_at: Optional[datetime] = None
    revert_reason: Optional[RevertReason] = None
    prediction_id: Optional[str] = None
    applied_value: Optional[float] = None


class EnvelopeValidationError(Exception):
    """Raised when envelope fails validation."""

    def __init__(self, rule_id: str, message: str):
        self.rule_id = rule_id
        self.message = message
        super().__init__(f"{rule_id}: {message}")


def validate_envelope(envelope: Envelope) -> None:
    """
    Validate envelope against hard gate rules (V1-V5 + CI-C4-1).

    These rules are evaluated BEFORE an envelope can ever apply.
    If any rule fails, the envelope is REJECTED.

    Raises:
        EnvelopeValidationError: If validation fails
    """
    # CI-C4-1: Envelope Class Declaration (C4 requirement)
    # Every envelope MUST declare exactly one class
    if envelope.envelope_class is None:
        raise EnvelopeValidationError(
            "CI-C4-1", "envelope_class is required (must be SAFETY, RELIABILITY, COST, or PERFORMANCE)"
        )
    if envelope.envelope_class not in EnvelopeClass:
        raise EnvelopeValidationError("CI-C4-1", f"envelope_class must be one of: {[e.value for e in EnvelopeClass]}")

    # V1: Single-Parameter Rule
    # Exactly one target_parameter, no compound or derived parameters
    if not envelope.scope.target_parameter:
        raise EnvelopeValidationError("V1", "target_parameter is required (single parameter only)")
    if "," in envelope.scope.target_parameter:
        raise EnvelopeValidationError("V1", "target_parameter must be single (no compound parameters)")

    # V2: Explicit Bounds Rule
    # Bounds must be numeric, no adaptive/dynamic/computed bounds
    if envelope.bounds.max_increase is None or envelope.bounds.max_decrease is None:
        raise EnvelopeValidationError("V2", "bounds must be explicit (max_increase, max_decrease required)")

    # V3: Timebox Rule
    # max_duration_seconds must be finite, no rolling extensions
    if envelope.timebox.max_duration_seconds <= 0:
        raise EnvelopeValidationError("V3", "max_duration_seconds must be positive and finite")
    if not envelope.timebox.hard_expiry:
        raise EnvelopeValidationError("V3", "hard_expiry must be true (no rolling extensions)")

    # V4: Baseline Integrity Rule
    # Baseline must be explicit, versioned, restorable without computation
    if not envelope.baseline.reference_id:
        raise EnvelopeValidationError("V4", "baseline.reference_id is required (must be versioned)")
    if envelope.baseline.source not in (
        BaselineSource.CONFIG_DEFAULT,
        BaselineSource.LAST_KNOWN_GOOD,
    ):
        raise EnvelopeValidationError("V4", "baseline.source must be config_default or last_known_good")

    # V5: Prediction Dependency Rule
    # Envelope validity depends on prediction existence
    if not envelope.revert_on:
        raise EnvelopeValidationError("V5", "revert_on is required (prediction dependency)")
    required_revert_reasons = {
        RevertReason.PREDICTION_EXPIRED,
        RevertReason.PREDICTION_DELETED,
        RevertReason.KILL_SWITCH,
    }
    if not required_revert_reasons.issubset(set(envelope.revert_on)):
        raise EnvelopeValidationError(
            "V5",
            "revert_on must include prediction_expired, prediction_deleted, kill_switch",
        )

    # Mark as validated
    envelope.lifecycle = EnvelopeLifecycle.VALIDATED

    logger.info(
        "envelope_validated",
        extra={
            "envelope_id": envelope.envelope_id,
            "envelope_version": envelope.envelope_version,
            "target": f"{envelope.scope.target_subsystem}.{envelope.scope.target_parameter}",
        },
    )


def calculate_bounded_value(
    baseline: float,
    bounds: EnvelopeBounds,
    prediction_confidence: float,
) -> float:
    """
    Calculate the bounded value based on prediction confidence.

    The value is scaled linearly with confidence within bounds.
    Handles both increase (S1) and decrease (S2) scenarios.

    Args:
        baseline: The baseline value
        bounds: The envelope bounds
        prediction_confidence: The prediction confidence (0.0-1.0)

    Returns:
        The bounded adjusted value
    """
    new_value = baseline

    if bounds.delta_type == DeltaType.PCT:
        # Percentage-based adjustment
        if bounds.max_increase > 0:
            # Increase scenario (S1: retry backoff)
            max_delta = baseline * (bounds.max_increase / 100.0)
            delta = max_delta * prediction_confidence
            new_value = baseline + delta
        elif bounds.max_decrease > 0:
            # Decrease scenario (S2: cost smoothing)
            max_delta = baseline * (bounds.max_decrease / 100.0)
            delta = max_delta * prediction_confidence
            new_value = baseline - delta
    else:
        # Absolute adjustment
        if bounds.max_increase > 0:
            delta = bounds.max_increase * prediction_confidence
            new_value = baseline + delta
        elif bounds.max_decrease > 0:
            delta = bounds.max_decrease * prediction_confidence
            new_value = baseline - delta

    # Apply ceiling if set (for increase scenarios)
    if bounds.absolute_ceiling is not None:
        new_value = min(new_value, bounds.absolute_ceiling)

    return new_value


def create_audit_record(envelope: Envelope, baseline_value: float) -> EnvelopeAuditRecord:
    """Create an audit record for envelope application."""
    return EnvelopeAuditRecord(
        envelope_id=envelope.envelope_id,
        envelope_version=envelope.envelope_version,
        prediction_id=envelope.prediction_id or "",
        target_subsystem=envelope.scope.target_subsystem,
        target_parameter=envelope.scope.target_parameter,
        baseline_value=baseline_value,
        applied_value=envelope.applied_value or baseline_value,
        applied_at=envelope.applied_at or datetime.now(timezone.utc),
        reverted_at=envelope.reverted_at,
        revert_reason=envelope.revert_reason,
    )
