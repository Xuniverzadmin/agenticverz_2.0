# C3-S1: Bounded Retry Optimization Envelope
# Reference: PIN-225, C3_ENVELOPE_ABSTRACTION.md
#
# Scenario: Prediction suggests elevated incident risk.
# System adjusts retry backoff parameters within a small envelope.
#
# Why this scenario:
# - Non-critical
# - Common
# - Reversible
# - No policy or enforcement semantics
#
# Allowed influence:
# - Retry delay +20% max (increase only, no decrease)
# - Max retries unchanged
# - Duration capped (600 seconds)
#
# Canary scope: One envelope, one parameter, one subsystem

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
    RevertReason,
)

# S1 Envelope Declaration (from user's C3-S1 guidance)
# C4: Classified as RELIABILITY (improves stability via backoff)
S1_RETRY_BACKOFF_ENVELOPE = Envelope(
    # Identity
    envelope_id="retry_backoff_s1",
    envelope_version="1.0.0",
    # Trigger
    trigger=EnvelopeTrigger(
        prediction_type="incident_risk",
        min_confidence=0.70,  # Advisory threshold only
    ),
    # Scope (single parameter only)
    scope=EnvelopeScope(
        target_subsystem="retry_policy",
        target_parameter="initial_backoff_ms",
    ),
    # Bounds
    bounds=EnvelopeBounds(
        delta_type=DeltaType.PCT,
        max_increase=20.0,  # +20% max
        max_decrease=0.0,  # No decrease allowed
        absolute_ceiling=5000.0,  # Hard stop at 5000ms
    ),
    # Timebox
    timebox=EnvelopeTimebox(
        max_duration_seconds=600,  # 10 minutes max
        hard_expiry=True,  # Must revert automatically
    ),
    # Baseline
    baseline=EnvelopeBaseline(
        source=BaselineSource.CONFIG_DEFAULT,
        reference_id="retry_policy_v3",
        value=100.0,  # Default initial_backoff_ms from RetryConfig
    ),
    # C4: Envelope classification
    envelope_class=EnvelopeClass.RELIABILITY,
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


def create_s1_envelope(
    baseline_value: float = 100.0,
    reference_id: str = "retry_policy_v3",
) -> Envelope:
    """
    Create a fresh S1 envelope instance with specified baseline.

    Args:
        baseline_value: The baseline initial_backoff_ms value
        reference_id: Version/hash of the baseline config

    Returns:
        New Envelope instance ready for validation
    """
    return Envelope(
        envelope_id="retry_backoff_s1",
        envelope_version="1.0.0",
        trigger=EnvelopeTrigger(
            prediction_type="incident_risk",
            min_confidence=0.70,
        ),
        scope=EnvelopeScope(
            target_subsystem="retry_policy",
            target_parameter="initial_backoff_ms",
        ),
        bounds=EnvelopeBounds(
            delta_type=DeltaType.PCT,
            max_increase=20.0,
            max_decrease=0.0,
            absolute_ceiling=5000.0,
        ),
        timebox=EnvelopeTimebox(
            max_duration_seconds=600,
            hard_expiry=True,
        ),
        baseline=EnvelopeBaseline(
            source=BaselineSource.CONFIG_DEFAULT,
            reference_id=reference_id,
            value=baseline_value,
        ),
        envelope_class=EnvelopeClass.RELIABILITY,
        revert_on=[
            RevertReason.PREDICTION_EXPIRED,
            RevertReason.PREDICTION_DELETED,
            RevertReason.KILL_SWITCH,
            RevertReason.VALIDATION_ERROR,
            RevertReason.SYSTEM_RESTART,
        ],
        audit_enabled=True,
    )
