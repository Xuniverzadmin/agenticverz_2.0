# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: sync
# Role: S2 Cost smoothing envelope implementation
# Callers: optimization/coordinator
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: M10 S2 Envelope

# C3-S2: Cost Smoothing Optimization Envelope
# Reference: PIN-225, C3_ENVELOPE_ABSTRACTION.md
#
# Scenario: Spend Spike prediction exists.
# System adjusts max_concurrent_jobs within a TIGHTER envelope.
#
# Why this scenario:
# - Economic parameter (affects throughput)
# - Gradual effect (not spiky)
# - Rollback must be immediate (not amortized)
# - Catches envelope leaks that S1 can't
#
# Constraints (TIGHTER than S1):
# - Decrease only (-10% max), increase FORBIDDEN
# - Absolute floor = 1 (never zero concurrency)
# - Timebox ≤ 15 minutes
# - Confidence ≥ 0.75
#
# If any backlog survives revert → C3 FAILS

from app.optimization.envelope import (
    BaselineSource,
    DeltaType,
    Envelope,
    EnvelopeBaseline,
    EnvelopeBounds,
    EnvelopeClass,
    EnvelopeScope,
    EnvelopeTimebox,
    EnvelopeTrigger,
    EnvelopeValidationError,
    RevertReason,
)

# S2 Envelope Declaration (from C3-S2 spec)
# C4: Classified as COST (reduces spend)
S2_COST_SMOOTHING_ENVELOPE = Envelope(
    # Identity
    envelope_id="cost_smoothing_s2",
    envelope_version="1.0.0",
    # Trigger
    trigger=EnvelopeTrigger(
        prediction_type="spend_spike",
        min_confidence=0.75,  # Higher than S1 (0.70)
    ),
    # Scope (single parameter only)
    scope=EnvelopeScope(
        target_subsystem="scheduler",
        target_parameter="max_concurrent_jobs",
    ),
    # Bounds (TIGHTER than S1)
    bounds=EnvelopeBounds(
        delta_type=DeltaType.PCT,
        max_increase=0.0,  # FORBIDDEN - increase not allowed
        max_decrease=10.0,  # -10% max
        absolute_ceiling=None,  # Not applicable for decrease
    ),
    # Timebox (SHORTER than S1)
    timebox=EnvelopeTimebox(
        max_duration_seconds=900,  # 15 minutes max (vs 10 for S1)
        hard_expiry=True,
    ),
    # Baseline
    baseline=EnvelopeBaseline(
        source=BaselineSource.CONFIG_DEFAULT,
        reference_id="scheduler_v2",
        value=10.0,  # Default max_concurrent_jobs
    ),
    # C4: Envelope classification
    envelope_class=EnvelopeClass.COST,
    # Revert policy (mandatory per V5)
    revert_on=[
        RevertReason.PREDICTION_EXPIRED,
        RevertReason.PREDICTION_DELETED,
        RevertReason.KILL_SWITCH,
        RevertReason.VALIDATION_ERROR,
        RevertReason.SYSTEM_RESTART,
    ],
    # Audit
    audit_enabled=True,
)

# S2 absolute floor - concurrency must never go below this
S2_ABSOLUTE_FLOOR = 1


def create_s2_envelope(
    baseline_value: float = 10.0,
    reference_id: str = "scheduler_v2",
) -> Envelope:
    """
    Create a fresh S2 envelope instance with specified baseline.

    Args:
        baseline_value: The baseline max_concurrent_jobs value
        reference_id: Version/hash of the baseline config

    Returns:
        New Envelope instance ready for validation
    """
    return Envelope(
        envelope_id="cost_smoothing_s2",
        envelope_version="1.0.0",
        trigger=EnvelopeTrigger(
            prediction_type="spend_spike",
            min_confidence=0.75,
        ),
        scope=EnvelopeScope(
            target_subsystem="scheduler",
            target_parameter="max_concurrent_jobs",
        ),
        bounds=EnvelopeBounds(
            delta_type=DeltaType.PCT,
            max_increase=0.0,  # FORBIDDEN
            max_decrease=10.0,
            absolute_ceiling=None,
        ),
        timebox=EnvelopeTimebox(
            max_duration_seconds=900,
            hard_expiry=True,
        ),
        baseline=EnvelopeBaseline(
            source=BaselineSource.CONFIG_DEFAULT,
            reference_id=reference_id,
            value=baseline_value,
        ),
        envelope_class=EnvelopeClass.COST,
        revert_on=[
            RevertReason.PREDICTION_EXPIRED,
            RevertReason.PREDICTION_DELETED,
            RevertReason.KILL_SWITCH,
            RevertReason.VALIDATION_ERROR,
            RevertReason.SYSTEM_RESTART,
        ],
        audit_enabled=True,
    )


def validate_s2_envelope(envelope: Envelope) -> None:
    """
    Validate S2-specific rules (additive to V1-V5).

    S2 Rules:
    - S2-V1: Increase forbidden (max_increase = 0)
    - S2-V2: Absolute floor required (value >= 1)
    - S2-V3: Timebox ≤ 15 minutes
    - S2-V4: Confidence ≥ 0.75
    - S2-V5: Baseline must be concurrency-safe (>= absolute floor)

    Raises:
        EnvelopeValidationError: If S2 validation fails
    """
    # S2-V1: Increase forbidden
    if envelope.bounds.max_increase != 0.0:
        raise EnvelopeValidationError("S2-V1", "max_increase must be 0 (increase forbidden for cost smoothing)")

    # S2-V2: Check baseline is above absolute floor
    if envelope.baseline.value is not None and envelope.baseline.value < S2_ABSOLUTE_FLOOR:
        raise EnvelopeValidationError("S2-V2", f"baseline value must be >= {S2_ABSOLUTE_FLOOR} (absolute floor)")

    # S2-V3: Timebox ≤ 15 minutes (900 seconds)
    if envelope.timebox.max_duration_seconds > 900:
        raise EnvelopeValidationError("S2-V3", "max_duration_seconds must be <= 900 (15 minutes) for S2")

    # S2-V4: Confidence ≥ 0.75
    if envelope.trigger.min_confidence < 0.75:
        raise EnvelopeValidationError("S2-V4", "min_confidence must be >= 0.75 for cost smoothing")

    # S2-V5: Baseline must be concurrency-safe
    if envelope.scope.target_parameter != "max_concurrent_jobs":
        raise EnvelopeValidationError("S2-V5", "S2 envelope must target max_concurrent_jobs only")


def calculate_s2_bounded_value(
    baseline: float,
    max_decrease_pct: float,
    prediction_confidence: float,
) -> float:
    """
    Calculate the bounded value for S2 (decrease only).

    S2 can only DECREASE concurrency, never increase.
    Result is floored at S2_ABSOLUTE_FLOOR.

    Args:
        baseline: The baseline max_concurrent_jobs value
        max_decrease_pct: Maximum decrease percentage (e.g., 10.0 for -10%)
        prediction_confidence: The prediction confidence (0.0-1.0)

    Returns:
        The bounded decreased value (never below S2_ABSOLUTE_FLOOR)
    """
    # Calculate decrease (scaled by confidence)
    max_delta = baseline * (max_decrease_pct / 100.0)
    delta = max_delta * prediction_confidence

    # Apply decrease
    new_value = baseline - delta

    # Apply absolute floor
    new_value = max(new_value, S2_ABSOLUTE_FLOOR)

    return new_value
