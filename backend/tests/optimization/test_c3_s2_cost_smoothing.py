# C3-S2 Cost Smoothing Tests
# Reference: PIN-225, C3_ENVELOPE_ABSTRACTION.md
#
# C3-S2 proves envelopes work when:
# - the parameter is economic
# - the effect is gradual
# - rollback must still be instant
#
# This catches envelope leaks that S1 can't.

import pytest

from app.optimization.envelope import (
    EnvelopeValidationError,
    RevertReason,
)
from app.optimization.envelopes.s2_cost_smoothing import (
    S2_ABSOLUTE_FLOOR,
    calculate_s2_bounded_value,
    create_s2_envelope,
    validate_s2_envelope,
)
from app.optimization.killswitch import (
    KillSwitch,
    KillSwitchTrigger,
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


class TestS2EnvelopeDeclaration:
    """Test S2 envelope declaration is correct per spec."""

    def test_s2_envelope_has_correct_trigger(self):
        """S2 triggers on spend_spike with confidence >= 0.75."""
        envelope = create_s2_envelope()
        assert envelope.trigger.prediction_type == "spend_spike"
        assert envelope.trigger.min_confidence == 0.75

    def test_s2_envelope_targets_max_concurrent_jobs(self):
        """S2 targets scheduler.max_concurrent_jobs only."""
        envelope = create_s2_envelope()
        assert envelope.scope.target_subsystem == "scheduler"
        assert envelope.scope.target_parameter == "max_concurrent_jobs"

    def test_s2_envelope_forbids_increase(self):
        """S2 max_increase must be 0 (increase forbidden)."""
        envelope = create_s2_envelope()
        assert envelope.bounds.max_increase == 0.0

    def test_s2_envelope_has_tighter_timebox(self):
        """S2 timebox is <= 15 minutes (900 seconds)."""
        envelope = create_s2_envelope()
        assert envelope.timebox.max_duration_seconds <= 900

    def test_s2_envelope_has_required_revert_reasons(self):
        """S2 envelope includes all required revert reasons."""
        envelope = create_s2_envelope()
        required = {
            RevertReason.PREDICTION_EXPIRED,
            RevertReason.PREDICTION_DELETED,
            RevertReason.KILL_SWITCH,
        }
        assert required.issubset(set(envelope.revert_on))


class TestS2ValidationRules:
    """Test S2-specific validation rules (S2-V1 to S2-V5)."""

    def test_s2_v1_increase_forbidden(self):
        """S2-V1: max_increase must be 0."""
        envelope = create_s2_envelope()
        envelope.bounds.max_increase = 5.0  # Invalid

        with pytest.raises(EnvelopeValidationError) as exc:
            validate_s2_envelope(envelope)
        assert exc.value.rule_id == "S2-V1"

    def test_s2_v2_absolute_floor_enforced(self):
        """S2-V2: baseline must be >= absolute floor."""
        envelope = create_s2_envelope(baseline_value=0.5)  # Below floor

        with pytest.raises(EnvelopeValidationError) as exc:
            validate_s2_envelope(envelope)
        assert exc.value.rule_id == "S2-V2"

    def test_s2_v3_timebox_limit(self):
        """S2-V3: timebox must be <= 15 minutes."""
        envelope = create_s2_envelope()
        envelope.timebox.max_duration_seconds = 1000  # Too long

        with pytest.raises(EnvelopeValidationError) as exc:
            validate_s2_envelope(envelope)
        assert exc.value.rule_id == "S2-V3"

    def test_s2_v4_confidence_threshold(self):
        """S2-V4: min_confidence must be >= 0.75."""
        envelope = create_s2_envelope()
        envelope.trigger.min_confidence = 0.60  # Too low

        with pytest.raises(EnvelopeValidationError) as exc:
            validate_s2_envelope(envelope)
        assert exc.value.rule_id == "S2-V4"

    def test_s2_v5_parameter_restriction(self):
        """S2-V5: must target max_concurrent_jobs."""
        envelope = create_s2_envelope()
        envelope.scope.target_parameter = "something_else"

        with pytest.raises(EnvelopeValidationError) as exc:
            validate_s2_envelope(envelope)
        assert exc.value.rule_id == "S2-V5"


class TestS2BoundedValueCalculation:
    """Test S2 bounded value calculation (decrease only)."""

    def test_s2_decrease_scales_with_confidence(self):
        """Decrease is scaled by prediction confidence."""
        baseline = 10.0
        max_decrease = 10.0  # -10%

        # Low confidence = smaller decrease
        value_low = calculate_s2_bounded_value(baseline, max_decrease, 0.5)
        assert value_low == 9.5  # 10 - (10 * 0.10 * 0.5)

        # High confidence = larger decrease
        value_high = calculate_s2_bounded_value(baseline, max_decrease, 1.0)
        assert value_high == 9.0  # 10 - (10 * 0.10 * 1.0)

    def test_s2_never_below_absolute_floor(self):
        """Result never goes below S2_ABSOLUTE_FLOOR."""
        baseline = 2.0
        max_decrease = 100.0  # -100% (would be 0)

        value = calculate_s2_bounded_value(baseline, max_decrease, 1.0)
        assert value == S2_ABSOLUTE_FLOOR  # Floored at 1

    def test_s2_no_increase_possible(self):
        """S2 calculation only decreases, never increases."""
        baseline = 10.0

        # Even with 0% decrease, value stays at baseline
        value = calculate_s2_bounded_value(baseline, 0.0, 1.0)
        assert value == baseline


class TestS2EnvelopeApplication:
    """Test S2 envelope application and reversion."""

    def test_s2_applies_with_valid_prediction(self):
        """S2 applies when spend_spike prediction has confidence >= 0.75."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s2_envelope(baseline_value=10.0)
        # First validate S2-specific rules
        validate_s2_envelope(envelope)

        result = manager.apply(
            envelope=envelope,
            baseline_value=10.0,
            prediction_id="spend-001",
            prediction_confidence=0.80,
        )

        assert result is not None
        assert result < 10.0  # Should be decreased
        assert result >= S2_ABSOLUTE_FLOOR

    def test_s2_rejected_with_low_confidence(self):
        """S2 rejected if confidence < 0.75."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s2_envelope()

        result = manager.apply(
            envelope=envelope,
            baseline_value=10.0,
            prediction_id="spend-001",
            prediction_confidence=0.70,  # Below 0.75 threshold
        )

        assert result is None

    def test_s2_killswitch_restores_immediately(self):
        """Kill-switch restores concurrency immediately."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        restored_value = None

        def on_revert(value):
            nonlocal restored_value
            restored_value = value

        envelope = create_s2_envelope(baseline_value=10.0)
        manager.apply(
            envelope=envelope,
            baseline_value=10.0,
            prediction_id="spend-001",
            prediction_confidence=0.85,
            revert_callback=on_revert,
        )

        # Kill-switch
        killswitch.activate("S2 test", KillSwitchTrigger.HUMAN)

        # Concurrency restored immediately
        assert restored_value == 10.0
        assert manager.active_envelope_count == 0

    def test_s2_expiry_restores_baseline_exactly(self):
        """Expiry restores baseline exactly."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s2_envelope(baseline_value=10.0)
        manager.apply(
            envelope=envelope,
            baseline_value=10.0,
            prediction_id="spend-001",
            prediction_confidence=0.85,
        )

        # Simulate expiry
        baseline = manager.revert(envelope.envelope_id, RevertReason.PREDICTION_EXPIRED)

        assert baseline == 10.0  # Exactly restored


class TestS2AcceptanceCriteria:
    """
    S2 Acceptance Criteria Tests.

    C3-S2 passes only if:
    - Concurrency never drops below absolute_floor
    - No increase is ever applied
    - Kill-switch restores concurrency immediately
    - Expiry restores baseline exactly
    - No backlog persists after revert
    - No incidents created
    """

    def test_concurrency_never_below_floor(self):
        """Concurrency never drops below absolute_floor."""
        # Test with very low baseline
        value = calculate_s2_bounded_value(
            baseline=1.5,
            max_decrease_pct=50.0,  # Would be 0.75
            prediction_confidence=1.0,
        )
        assert value >= S2_ABSOLUTE_FLOOR

    def test_no_increase_ever_applied(self):
        """No increase is ever applied via S2."""
        # Even at 0 confidence, value doesn't increase
        value = calculate_s2_bounded_value(
            baseline=10.0,
            max_decrease_pct=10.0,
            prediction_confidence=0.0,
        )
        assert value == 10.0  # No change, not increase

    def test_revert_is_exact(self):
        """Baseline is restored exactly, not approximately."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        exact_baseline = 7.123456789
        restored = None

        def on_revert(v):
            nonlocal restored
            restored = v

        envelope = create_s2_envelope(baseline_value=exact_baseline)
        manager.apply(envelope, exact_baseline, "pred-001", 0.85, on_revert)

        manager.revert(envelope.envelope_id, RevertReason.KILL_SWITCH)

        assert restored == exact_baseline  # Exact match
