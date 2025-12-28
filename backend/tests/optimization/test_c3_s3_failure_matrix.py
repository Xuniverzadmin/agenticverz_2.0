# C3-S3: Failure Matrix — Catastrophic Safety Proof
# Reference: PIN-225, C3_ENVELOPE_ABSTRACTION.md, C3_KILLSWITCH_ROLLBACK_MODEL.md
#
# STATUS: CRITICAL — NON-OPTIONAL
#
# C3-S3 Design Principle:
# > If C3-S3 fails, C3 is invalid, regardless of S1/S2 success.
#
# This scenario exists to destroy optimism.
#
# C3-S3 proves that optimization cannot hurt the system
# even when everything goes wrong.


import pytest

from app.optimization.envelope import (
    RevertReason,
)
from app.optimization.envelopes.s1_retry_backoff import create_s1_envelope
from app.optimization.envelopes.s2_cost_smoothing import create_s2_envelope
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


class TestFS31_PredictionDeletedMidEnvelope:
    """
    F-S3-1: Prediction deleted mid-envelope.

    Expected Outcome: Immediate revert, baseline restored.
    """

    def test_prediction_deleted_triggers_immediate_revert(self):
        """When prediction is deleted, envelope reverts immediately."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        baseline = 100.0
        restored_value = None

        def on_revert(v):
            nonlocal restored_value
            restored_value = v

        envelope = create_s1_envelope(baseline_value=baseline)
        applied = manager.apply(envelope, baseline, "pred-will-be-deleted", 0.85, on_revert)

        assert applied is not None
        assert manager.active_envelope_count == 1

        # Simulate prediction deletion
        result = manager.revert(envelope.envelope_id, RevertReason.PREDICTION_DELETED)

        assert result == baseline
        assert restored_value == baseline
        assert manager.active_envelope_count == 0
        assert envelope.revert_reason == RevertReason.PREDICTION_DELETED


class TestFS32_PredictionExpiresEarly:
    """
    F-S3-2: Prediction expires early.

    Expected Outcome: Immediate revert.
    """

    def test_prediction_expiry_triggers_revert(self):
        """When prediction expires, envelope reverts immediately."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()
        manager.apply(envelope, 100.0, "pred-expires-early", 0.85)

        # Simulate early expiry
        baseline = manager.revert(envelope.envelope_id, RevertReason.PREDICTION_EXPIRED)

        assert baseline == 100.0
        assert manager.active_envelope_count == 0


class TestFS33_KillswitchToggledRepeatedly:
    """
    F-S3-3: Kill-switch toggled repeatedly.

    Expected Outcome: Idempotent revert, no residue.
    """

    def test_repeated_killswitch_is_idempotent(self):
        """Multiple kill-switch activations don't cause issues."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()
        manager.apply(envelope, 100.0, "pred-001", 0.85)

        # First kill
        killswitch.activate("First kill", KillSwitchTrigger.HUMAN)
        assert manager.active_envelope_count == 0

        # Rearm
        killswitch.rearm("Rearm for test")
        assert killswitch.is_enabled

        # Apply new envelope
        envelope2 = create_s1_envelope()
        envelope2.envelope_id = "retry_backoff_s1_v2"
        manager.apply(envelope2, 100.0, "pred-002", 0.85)

        # Second kill
        killswitch.activate("Second kill", KillSwitchTrigger.HUMAN)
        assert manager.active_envelope_count == 0

        # Third kill (no active envelopes)
        killswitch.rearm("Rearm again")
        killswitch.activate("Third kill (empty)", KillSwitchTrigger.HUMAN)

        # No errors, no residue
        assert manager.active_envelope_count == 0
        assert len(killswitch.get_events()) == 3

    def test_no_residue_after_repeated_toggling(self):
        """No state residue after repeated kill-switch toggling."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # Toggle 10 times
        for i in range(10):
            envelope = create_s1_envelope()
            envelope.envelope_id = f"retry_backoff_s1_v{i}"

            if killswitch.is_enabled:
                manager.apply(envelope, 100.0, f"pred-{i}", 0.85)
                killswitch.activate(f"Kill {i}", KillSwitchTrigger.HUMAN)
            else:
                killswitch.rearm(f"Rearm {i}")

        # Final state: no active envelopes
        killswitch.activate("Final kill", KillSwitchTrigger.HUMAN)
        assert manager.active_envelope_count == 0


class TestFS34_RestartDuringActiveEnvelope:
    """
    F-S3-4: System restart during active envelope.

    Expected Outcome: Baseline restored on boot.

    Note: In a real system, this would be tested with actual restart.
    Here we simulate by resetting state.
    """

    def test_restart_clears_active_envelopes(self):
        """System restart clears all active envelopes (baseline restored)."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # Apply envelope
        envelope = create_s1_envelope()
        manager.apply(envelope, 100.0, "pred-before-restart", 0.85)
        assert manager.active_envelope_count == 1

        # Simulate restart by resetting state
        reset_killswitch_for_testing()
        reset_manager_for_testing()

        # Create new manager (simulates boot)
        new_killswitch = KillSwitch()
        new_manager = EnvelopeManager(new_killswitch)

        # No active envelopes after restart
        assert new_manager.active_envelope_count == 0
        assert new_killswitch.is_enabled  # Default state

    def test_system_restart_revert_reason_supported(self):
        """SYSTEM_RESTART is a valid revert reason."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()
        manager.apply(envelope, 100.0, "pred-001", 0.85)

        # Revert with system_restart reason
        baseline = manager.revert(envelope.envelope_id, RevertReason.SYSTEM_RESTART)

        assert baseline == 100.0
        assert envelope.revert_reason == RevertReason.SYSTEM_RESTART


class TestFS35_EnvelopeValidationCorruption:
    """
    F-S3-5: Corrupt / invalid envelope input.

    Expected Outcome: Envelope rejected, no effect.
    """

    def test_invalid_envelope_rejected(self):
        """Invalid envelope is rejected before application."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # Create envelope with invalid timebox
        envelope = create_s1_envelope()
        envelope.timebox.max_duration_seconds = 0  # Invalid

        result = manager.apply(envelope, 100.0, "pred-001", 0.85)

        assert result is None
        assert manager.active_envelope_count == 0

    def test_missing_revert_policy_rejected(self):
        """Envelope without revert policy is rejected."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()
        envelope.revert_on = []  # Invalid - no revert policy

        result = manager.apply(envelope, 100.0, "pred-001", 0.85)

        assert result is None
        assert manager.active_envelope_count == 0

    def test_corrupt_bounds_rejected(self):
        """Envelope with corrupt bounds is rejected."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()
        envelope.bounds.max_increase = None  # Corrupt

        result = manager.apply(envelope, 100.0, "pred-001", 0.85)

        assert result is None
        assert manager.active_envelope_count == 0


class TestFS36_EnvelopeStoreUnavailable:
    """
    F-S3-6: Envelope store unavailable.

    Expected Outcome: Optimization disabled, baseline intact.

    Note: Our in-memory implementation doesn't have a separate store,
    but we test that manager gracefully handles edge cases.
    """

    def test_manager_handles_missing_envelope_gracefully(self):
        """Manager returns None for non-existent envelope revert."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # Try to revert non-existent envelope
        result = manager.revert("non_existent_envelope", RevertReason.KILL_SWITCH)

        assert result is None  # No error, just returns None

    def test_optimization_disabled_when_killswitch_active(self):
        """When kill-switch active, no optimization possible."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # Disable optimization
        killswitch.activate("Store unavailable simulation", KillSwitchTrigger.SYSTEM)

        # Try to apply envelope
        envelope = create_s1_envelope()
        result = manager.apply(envelope, 100.0, "pred-001", 0.85)

        # Optimization disabled, baseline intact
        assert result is None
        assert manager.active_envelope_count == 0


class TestFS37_MultipleEnvelopesRequested:
    """
    F-S3-7: Multiple envelopes requested.

    Expected Outcome: All rejected except one (same envelope_id).

    Note: Our implementation allows one envelope per envelope_id.
    """

    def test_duplicate_envelope_rejected(self):
        """Second envelope with same ID is rejected."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope1 = create_s1_envelope()
        envelope2 = create_s1_envelope()  # Same envelope_id

        # First applies
        result1 = manager.apply(envelope1, 100.0, "pred-001", 0.85)
        assert result1 is not None
        assert manager.active_envelope_count == 1

        # Second rejected (same ID)
        result2 = manager.apply(envelope2, 100.0, "pred-002", 0.85)
        assert result2 is None
        assert manager.active_envelope_count == 1  # Still only one

    def test_different_envelopes_can_coexist(self):
        """Different envelope IDs can be active simultaneously."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope1 = create_s1_envelope()
        envelope2 = create_s2_envelope()

        result1 = manager.apply(envelope1, 100.0, "pred-001", 0.85)
        result2 = manager.apply(envelope2, 10.0, "pred-002", 0.85)

        assert result1 is not None
        assert result2 is not None
        assert manager.active_envelope_count == 2


class TestFS38_ReplayWithoutPredictions:
    """
    F-S3-8: Replay without predictions.

    Expected Outcome: Baseline behavior identical.

    Note: This is a conceptual test - replay uses baseline when
    no predictions are available.
    """

    def test_no_prediction_means_baseline_behavior(self):
        """Without prediction (confidence 0), behavior is baseline."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope(baseline_value=100.0)

        # Apply with no confidence (simulates missing prediction in replay)
        result = manager.apply(envelope, 100.0, "", 0.0)

        # No envelope applied, baseline unchanged
        assert result is None
        assert manager.active_envelope_count == 0

    def test_low_confidence_preserves_baseline(self):
        """Low confidence preserves baseline behavior."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()  # min_confidence = 0.70

        # Below threshold
        result = manager.apply(envelope, 100.0, "pred-weak", 0.50)

        assert result is None  # Baseline preserved


class TestFS39_ReplayWithFailures:
    """
    F-S3-9: Replay with failures.

    Expected Outcome: Deterministic, explainable sequence.
    """

    def test_failure_sequence_is_deterministic(self):
        """Same failure sequence produces same results."""
        results_run1 = []
        results_run2 = []

        for results in [results_run1, results_run2]:
            reset_killswitch_for_testing()
            reset_manager_for_testing()

            killswitch = KillSwitch()
            manager = EnvelopeManager(killswitch)

            # Sequence: apply, fail validation, apply, kill, apply (blocked)
            envelope1 = create_s1_envelope()
            results.append(manager.apply(envelope1, 100.0, "pred-1", 0.85))

            envelope2 = create_s1_envelope()
            envelope2.timebox.max_duration_seconds = 0  # Invalid
            results.append(manager.apply(envelope2, 100.0, "pred-2", 0.85))

            envelope3 = create_s1_envelope()
            envelope3.envelope_id = "retry_backoff_s1_v3"
            results.append(manager.apply(envelope3, 100.0, "pred-3", 0.85))

            killswitch.activate("Replay kill", KillSwitchTrigger.HUMAN)
            results.append(manager.active_envelope_count)

            envelope4 = create_s1_envelope()
            envelope4.envelope_id = "retry_backoff_s1_v4"
            results.append(manager.apply(envelope4, 100.0, "pred-4", 0.85))

        # Deterministic: same sequence, same results
        assert results_run1 == results_run2

    def test_audit_records_complete_for_failures(self):
        """Audit records capture failure sequence."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # Apply, then force revert
        envelope = create_s1_envelope()
        manager.apply(envelope, 100.0, "pred-001", 0.85)
        manager.revert(envelope.envelope_id, RevertReason.VALIDATION_ERROR)

        # Check audit records
        records = manager.get_audit_records()
        assert len(records) >= 1

        record = records[0]
        assert record.envelope_id == envelope.envelope_id
        assert record.reverted_at is not None
        assert record.revert_reason == RevertReason.VALIDATION_ERROR


class TestS3AcceptanceCriteria:
    """
    C3-S3 Acceptance Criteria (Absolute).

    C3-S3 passes only if:
    - System ALWAYS returns to baseline
    - No partial envelope survives
    - Kill-switch dominates every path
    - No incident is caused by optimization
    - Replay is deterministic
    - Audit trail complete for every failure

    If ONE test leaves residue → C3 fails entirely.
    """

    def test_system_always_returns_to_baseline(self):
        """System always returns to baseline after any failure."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        baselines_restored = []

        for reason in [
            RevertReason.PREDICTION_EXPIRED,
            RevertReason.PREDICTION_DELETED,
            RevertReason.KILL_SWITCH,
            RevertReason.SYSTEM_RESTART,
            RevertReason.VALIDATION_ERROR,
        ]:
            reset_killswitch_for_testing()
            reset_manager_for_testing()

            ks = KillSwitch()
            mgr = EnvelopeManager(ks)

            envelope = create_s1_envelope()
            mgr.apply(envelope, 100.0, "pred-001", 0.85)

            baseline = mgr.revert(envelope.envelope_id, reason)
            baselines_restored.append(baseline)

        # All returned to baseline
        assert all(b == 100.0 for b in baselines_restored)

    def test_no_partial_envelope_survives(self):
        """No partial envelope state survives after revert."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        envelope = create_s1_envelope()
        manager.apply(envelope, 100.0, "pred-001", 0.85)

        # Revert
        manager.revert(envelope.envelope_id, RevertReason.KILL_SWITCH)

        # No active envelopes
        assert manager.active_envelope_count == 0
        assert not manager.is_envelope_active(envelope.envelope_id)

    def test_killswitch_dominates_every_path(self):
        """Kill-switch dominates regardless of envelope state."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # Apply multiple envelopes
        for i in range(5):
            envelope = create_s1_envelope()
            envelope.envelope_id = f"envelope_{i}"
            manager.apply(envelope, 100.0, f"pred-{i}", 0.85)

        assert manager.active_envelope_count == 5

        # Kill-switch dominates all
        killswitch.activate("Domination test", KillSwitchTrigger.HUMAN)

        assert manager.active_envelope_count == 0

    def test_optimization_never_causes_incident(self):
        """Optimization failures never raise unhandled exceptions."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # These should all return None, not raise
        invalid_envelopes = [
            create_s1_envelope(),  # Valid but modify to make invalid
        ]

        for envelope in invalid_envelopes:
            envelope.timebox.max_duration_seconds = -1  # Invalid

            # Should not raise
            try:
                result = manager.apply(envelope, 100.0, "pred", 0.85)
                assert result is None
            except Exception as e:
                pytest.fail(f"Optimization caused exception: {e}")

    def test_audit_trail_complete(self):
        """Audit trail complete for every failure scenario."""
        killswitch = KillSwitch()
        manager = EnvelopeManager(killswitch)

        # Apply and revert
        envelope = create_s1_envelope()
        manager.apply(envelope, 100.0, "pred-001", 0.85)
        manager.revert(envelope.envelope_id, RevertReason.PREDICTION_DELETED)

        # Audit complete
        records = manager.get_audit_records()
        assert len(records) == 1

        record = records[0]
        assert record.envelope_id is not None
        assert record.baseline_value is not None
        assert record.applied_value is not None
        assert record.applied_at is not None
        assert record.reverted_at is not None
        assert record.revert_reason is not None
