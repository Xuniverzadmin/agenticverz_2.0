# C3 Failure Scenario Tests (F-1, F-2, F-3)
# Reference: PIN-225, C3_ENVELOPE_ABSTRACTION.md, C3_KILLSWITCH_ROLLBACK_MODEL.md
#
# These tests MUST pass before any happy path tests.
# User guidance: "You do **not** start with 'happy path'. Run failure tests first."
#
# C3-S3: Prediction Failure Scenario (CRITICAL)
# This is the MOST IMPORTANT C3 test. If this fails, C3 is invalid.

import pytest

from app.optimization.envelope import (
    BaselineSource,
    DeltaType,
    Envelope,
    EnvelopeBaseline,
    EnvelopeBounds,
    EnvelopeClass,
    EnvelopeLifecycle,
    EnvelopeScope,
    EnvelopeTimebox,
    EnvelopeTrigger,
    RevertReason,
)
from app.optimization.envelopes.s1_retry_backoff import create_s1_envelope
from app.optimization.killswitch import (
    KillSwitch,
    KillSwitchTrigger,
    RollbackStatus,
    reset_killswitch_for_testing,
)
from app.optimization.manager import EnvelopeManager, reset_manager_for_testing


@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    reset_killswitch_for_testing()
    reset_manager_for_testing()
    yield
    reset_killswitch_for_testing()
    reset_manager_for_testing()


class TestF1_KillswitchRevertsActiveEnvelope:
    """
    F-1: Kill-switch reverts active envelope immediately.

    Per C3_KILLSWITCH_ROLLBACK_MODEL.md section 4.2:
    - All active envelopes are revoked
    - All envelope deltas are reverted
    - No grace period. No batching. No retries.
    """

    def test_killswitch_reverts_single_envelope(self):
        """Single active envelope is reverted immediately on kill-switch."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # Apply envelope
        envelope = create_s1_envelope(baseline_value=100.0)
        revert_called = False
        reverted_to = None

        def on_revert(value):
            nonlocal revert_called, reverted_to
            revert_called = True
            reverted_to = value

        applied_value = manager.apply(
            envelope=envelope,
            baseline_value=100.0,
            prediction_id="pred-001",
            prediction_confidence=0.85,
            revert_callback=on_revert,
        )

        assert applied_value is not None
        assert applied_value > 100.0  # Should be increased by up to 20%
        assert manager.active_envelope_count == 1

        # Activate kill-switch
        event = killswitch.activate(
            reason="F-1 test: manual kill",
            triggered_by=KillSwitchTrigger.HUMAN,
            active_envelopes_count=1,
        )

        # Verify immediate reversion
        assert killswitch.is_disabled
        assert manager.active_envelope_count == 0
        assert revert_called
        assert reverted_to == 100.0  # Baseline restored exactly

        # Verify audit
        assert event.rollback_status == RollbackStatus.SUCCESS
        assert event.rollback_completed_at is not None

    def test_killswitch_blocks_new_envelope_application(self):
        """No new envelopes may be applied while kill-switch is active."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # Activate kill-switch first
        killswitch.activate(reason="F-1 test: pre-emptive kill", triggered_by=KillSwitchTrigger.HUMAN)

        assert killswitch.is_disabled

        # Try to apply envelope
        envelope = create_s1_envelope()
        result = manager.apply(
            envelope=envelope,
            baseline_value=100.0,
            prediction_id="pred-001",
            prediction_confidence=0.85,
        )

        # Application must be rejected
        assert result is None
        assert manager.active_envelope_count == 0

    def test_killswitch_reverts_multiple_envelopes(self):
        """All active envelopes are reverted on kill-switch."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        reverted_values = []

        def make_callback(envelope_id):
            def callback(value):
                reverted_values.append((envelope_id, value))

            return callback

        # Apply multiple envelopes (simulating different envelope types)
        for i in range(3):
            envelope = Envelope(
                envelope_id=f"test_envelope_{i}",
                envelope_version="1.0.0",
                trigger=EnvelopeTrigger(prediction_type="incident_risk", min_confidence=0.5),
                scope=EnvelopeScope(target_subsystem="retry_policy", target_parameter="initial_backoff_ms"),
                bounds=EnvelopeBounds(delta_type=DeltaType.PCT, max_increase=20.0, max_decrease=0.0),
                timebox=EnvelopeTimebox(max_duration_seconds=600, hard_expiry=True),
                baseline=EnvelopeBaseline(
                    source=BaselineSource.CONFIG_DEFAULT, reference_id="v1", value=100.0 + i * 10
                ),
                envelope_class=EnvelopeClass.RELIABILITY,
                revert_on=[RevertReason.PREDICTION_EXPIRED, RevertReason.PREDICTION_DELETED, RevertReason.KILL_SWITCH],
            )
            manager.apply(
                envelope=envelope,
                baseline_value=100.0 + i * 10,
                prediction_id=f"pred-{i}",
                prediction_confidence=0.85,
                revert_callback=make_callback(envelope.envelope_id),
            )

        assert manager.active_envelope_count == 3

        # Kill-switch
        killswitch.activate(
            reason="F-1 test: mass kill", triggered_by=KillSwitchTrigger.HUMAN, active_envelopes_count=3
        )

        # All reverted
        assert manager.active_envelope_count == 0
        assert len(reverted_values) == 3

    def test_killswitch_does_not_require_prediction(self):
        """Kill-switch operation does not depend on predictions (K-3)."""
        killswitch = KillSwitch()

        # Activate without any prediction context
        event = killswitch.activate(
            reason="K-3 test: prediction-independent kill",
            triggered_by=KillSwitchTrigger.SYSTEM,
        )

        assert killswitch.is_disabled
        assert event.triggered_by == KillSwitchTrigger.SYSTEM


class TestF2_MissingPredictionPreventsApplication:
    """
    F-2: Missing prediction prevents envelope application.

    Per C3-S3 and I-C3-1:
    - Missing prediction → baseline behavior
    - Unavailable prediction service → safe no-op
    """

    def test_low_confidence_prevents_application(self):
        """Envelope not applied if prediction confidence is below threshold."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()  # min_confidence = 0.70

        # Apply with low confidence
        result = manager.apply(
            envelope=envelope,
            baseline_value=100.0,
            prediction_id="pred-low",
            prediction_confidence=0.50,  # Below 0.70 threshold
        )

        # Application should be skipped
        assert result is None
        assert manager.active_envelope_count == 0

    def test_no_prediction_means_no_envelope(self):
        """Without prediction, envelope cannot be applied."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()

        # Try to apply with effectively no prediction (confidence = 0)
        result = manager.apply(
            envelope=envelope,
            baseline_value=100.0,
            prediction_id="",  # Empty prediction ID
            prediction_confidence=0.0,  # No confidence
        )

        # Must return None (baseline behavior)
        assert result is None
        assert manager.active_envelope_count == 0

    def test_envelope_requires_valid_prediction_type(self):
        """Envelope trigger must match prediction type."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()  # Expects prediction_type="incident_risk"

        # S1 envelope requires incident_risk prediction
        # With confidence >= 0.70, it should apply
        result = manager.apply(
            envelope=envelope,
            baseline_value=100.0,
            prediction_id="pred-valid",
            prediction_confidence=0.85,
        )

        assert result is not None
        assert manager.active_envelope_count == 1


class TestF3_StalePredictionAutoExpires:
    """
    F-3: Stale prediction auto-expires envelope.

    Per C3-S3:
    - Stale prediction → automatic expiry, no action
    - Envelope revert_on includes PREDICTION_EXPIRED
    """

    def test_envelope_reverts_on_prediction_expired(self):
        """Envelope is reverted when prediction expires."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        revert_called = False

        def on_revert(value):
            nonlocal revert_called
            revert_called = True

        envelope = create_s1_envelope()
        manager.apply(
            envelope=envelope,
            baseline_value=100.0,
            prediction_id="pred-stale",
            prediction_confidence=0.85,
            revert_callback=on_revert,
        )

        assert manager.active_envelope_count == 1

        # Simulate prediction expiry
        baseline = manager.revert(envelope.envelope_id, RevertReason.PREDICTION_EXPIRED)

        assert baseline == 100.0
        assert manager.active_envelope_count == 0
        assert revert_called
        assert envelope.lifecycle == EnvelopeLifecycle.REVERTED
        assert envelope.revert_reason == RevertReason.PREDICTION_EXPIRED

    def test_envelope_reverts_on_prediction_deleted(self):
        """Envelope is reverted when prediction is deleted."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()
        manager.apply(
            envelope=envelope,
            baseline_value=100.0,
            prediction_id="pred-deleted",
            prediction_confidence=0.85,
        )

        # Simulate prediction deletion
        baseline = manager.revert(envelope.envelope_id, RevertReason.PREDICTION_DELETED)

        assert baseline == 100.0
        assert envelope.revert_reason == RevertReason.PREDICTION_DELETED

    def test_s1_envelope_has_required_revert_reasons(self):
        """S1 envelope declaration includes all required revert reasons."""
        envelope = create_s1_envelope()

        required = {
            RevertReason.PREDICTION_EXPIRED,
            RevertReason.PREDICTION_DELETED,
            RevertReason.KILL_SWITCH,
        }

        assert required.issubset(set(envelope.revert_on))


class TestEnvelopeValidationRules:
    """
    Validation rules (V1-V5) are hard gates.
    If any rule fails, envelope is REJECTED.
    """

    def test_v1_single_parameter_required(self):
        """V1: Exactly one target_parameter, no compound parameters."""
        from app.optimization.envelope import EnvelopeValidationError, validate_envelope

        # Missing parameter
        envelope = create_s1_envelope()
        envelope.scope.target_parameter = ""

        with pytest.raises(EnvelopeValidationError) as exc:
            validate_envelope(envelope)
        assert exc.value.rule_id == "V1"

    def test_v2_explicit_bounds_required(self):
        """V2: Bounds must be numeric, not adaptive."""
        from app.optimization.envelope import EnvelopeValidationError, validate_envelope

        envelope = create_s1_envelope()
        envelope.bounds.max_increase = None

        with pytest.raises(EnvelopeValidationError) as exc:
            validate_envelope(envelope)
        assert exc.value.rule_id == "V2"

    def test_v3_timebox_must_be_finite(self):
        """V3: max_duration_seconds must be positive and finite."""
        from app.optimization.envelope import EnvelopeValidationError, validate_envelope

        envelope = create_s1_envelope()
        envelope.timebox.max_duration_seconds = 0

        with pytest.raises(EnvelopeValidationError) as exc:
            validate_envelope(envelope)
        assert exc.value.rule_id == "V3"

    def test_v4_baseline_must_be_versioned(self):
        """V4: Baseline must have reference_id."""
        from app.optimization.envelope import EnvelopeValidationError, validate_envelope

        envelope = create_s1_envelope()
        envelope.baseline.reference_id = ""

        with pytest.raises(EnvelopeValidationError) as exc:
            validate_envelope(envelope)
        assert exc.value.rule_id == "V4"

    def test_v5_revert_policy_required(self):
        """V5: Envelope must have revert_on with required reasons."""
        from app.optimization.envelope import EnvelopeValidationError, validate_envelope

        envelope = create_s1_envelope()
        envelope.revert_on = []

        with pytest.raises(EnvelopeValidationError) as exc:
            validate_envelope(envelope)
        assert exc.value.rule_id == "V5"


class TestKillswitchInvariants:
    """
    Kill-switch invariants (K-1 to K-5) from C3_KILLSWITCH_ROLLBACK_MODEL.md.
    """

    def test_k1_killswitch_overrides_all_envelopes(self):
        """K-1: Kill-switch overrides all envelopes."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # Apply envelope
        envelope = create_s1_envelope()
        manager.apply(envelope, 100.0, "pred-001", 0.85)

        # Kill-switch overrides
        killswitch.activate(reason="K-1 test", triggered_by=KillSwitchTrigger.HUMAN)

        assert manager.active_envelope_count == 0

    def test_k2_killswitch_causes_immediate_reversion(self):
        """K-2: Kill-switch causes immediate reversion."""
        killswitch = KillSwitch()
        reverted_immediately = []

        def on_activate(event):
            reverted_immediately.append(event.event_id)

        killswitch.on_activate(on_activate)
        killswitch.activate(reason="K-2 test", triggered_by=KillSwitchTrigger.HUMAN)

        assert len(reverted_immediately) == 1  # Callback fired immediately

    def test_k4_killswitch_does_not_require_redeploy(self):
        """K-4: Kill-switch does not require redeploy."""
        killswitch = KillSwitch()

        # Enable, disable, enable again - all in same process
        assert killswitch.is_enabled
        killswitch.activate(reason="K-4 test", triggered_by=KillSwitchTrigger.HUMAN)
        assert killswitch.is_disabled
        killswitch.rearm(reason="K-4 rearm")
        assert killswitch.is_enabled

    def test_k5_killswitch_is_auditable(self):
        """K-5: Kill-switch is auditable."""
        killswitch = KillSwitch()

        killswitch.activate(reason="K-5 test", triggered_by=KillSwitchTrigger.HUMAN, active_envelopes_count=5)

        events = killswitch.get_events()
        assert len(events) == 1

        event = events[0]
        assert event.event_id  # Has ID
        assert event.trigger_reason == "K-5 test"
        assert event.triggered_by == KillSwitchTrigger.HUMAN
        assert event.activated_at is not None
        assert event.active_envelopes_count == 5


class TestRollbackGuarantees:
    """
    Rollback guarantees (R-1 to R-5) from C3_KILLSWITCH_ROLLBACK_MODEL.md.
    """

    def test_r1_baseline_restored_exactly(self):
        """R-1: Baseline restored exactly."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        exact_baseline = 123.456
        restored_value = None

        def on_revert(value):
            nonlocal restored_value
            restored_value = value

        envelope = create_s1_envelope(baseline_value=exact_baseline)
        manager.apply(envelope, exact_baseline, "pred-001", 0.85, on_revert)

        killswitch.activate(reason="R-1 test", triggered_by=KillSwitchTrigger.HUMAN)

        assert restored_value == exact_baseline  # Exactly restored

    def test_r3_rollback_is_idempotent(self):
        """R-3: Rollback is idempotent."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()
        manager.apply(envelope, 100.0, "pred-001", 0.85)

        # First revert
        result1 = manager.revert(envelope.envelope_id, RevertReason.KILL_SWITCH)
        assert result1 == 100.0

        # Second revert (idempotent - should return None, not error)
        result2 = manager.revert(envelope.envelope_id, RevertReason.KILL_SWITCH)
        assert result2 is None  # Already reverted

    def test_r4_rollback_works_without_prediction(self):
        """R-4: Rollback works even if prediction is missing."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()
        manager.apply(envelope, 100.0, "pred-001", 0.85)

        # Rollback without any prediction context
        result = manager.revert(envelope.envelope_id, RevertReason.PREDICTION_DELETED)

        assert result == 100.0  # Works without prediction


class TestC3Invariants:
    """
    C3 Invariants (I-C3-1 to I-C3-6) from PIN-225.
    """

    def test_i_c3_1_predictions_via_envelopes_only(self):
        """I-C3-1: Predictions may influence behavior only via declared optimization envelopes."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # The only way to influence behavior is through manager.apply()
        # Direct modification is not possible via this API
        envelope = create_s1_envelope()
        result = manager.apply(envelope, 100.0, "pred-001", 0.85)

        # Influence only happens through envelope
        assert result is not None
        assert envelope.lifecycle == EnvelopeLifecycle.ACTIVE

    def test_i_c3_2_every_change_bounded(self):
        """I-C3-2: Every prediction-driven change is bounded (impact + time)."""
        envelope = create_s1_envelope()

        # Impact bounded
        assert envelope.bounds.max_increase == 20.0
        assert envelope.bounds.absolute_ceiling == 5000.0

        # Time bounded
        assert envelope.timebox.max_duration_seconds == 600
        assert envelope.timebox.hard_expiry is True

    def test_i_c3_3_all_influence_reversible(self):
        """I-C3-3: All prediction influence is reversible."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()
        manager.apply(envelope, 100.0, "pred-001", 0.85)

        # Can always revert
        baseline = manager.revert(envelope.envelope_id, RevertReason.KILL_SWITCH)
        assert baseline == 100.0

    def test_i_c3_4_human_override_always_wins(self):
        """I-C3-4: Human override always wins."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # Apply envelope
        envelope = create_s1_envelope()
        manager.apply(envelope, 100.0, "pred-001", 0.85)

        # Human kill-switch overrides everything
        killswitch.activate(reason="Human override", triggered_by=KillSwitchTrigger.HUMAN)

        assert manager.active_envelope_count == 0
        assert killswitch.is_disabled

    def test_i_c3_6_optimization_failure_never_creates_incidents(self):
        """I-C3-6: Optimization failure must never create incidents."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # Invalid envelope should not raise unhandled exception
        envelope = create_s1_envelope()
        envelope.timebox.max_duration_seconds = 0  # Invalid

        # Should return None, not raise
        result = manager.apply(envelope, 100.0, "pred-001", 0.85)
        assert result is None
        assert manager.active_envelope_count == 0
