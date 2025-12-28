# C4-S1 Multi-Envelope Coordination Tests
# Reference: C4_S1_COORDINATION_SCENARIO.md, PIN-230, C4_ENVELOPE_COORDINATION_CONTRACT.md
#
# These tests validate C4 safe coexistence scenarios:
# - T0: Both envelopes apply (different subsystems)
# - T1-T2: Same-parameter rejection
# - T3: Priority preemption
# - T4: Kill-switch reverts all
# - T5: Independent rollback


import pytest

from app.optimization.coordinator import CoordinationManager
from app.optimization.envelope import (
    BaselineSource,
    CoordinationAuditRecord,
    CoordinationDecisionType,
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
    validate_envelope,
)


def create_test_envelope(
    envelope_id: str,
    envelope_class: EnvelopeClass,
    subsystem: str,
    parameter: str,
    prediction_type: str = "test_prediction",
) -> Envelope:
    """Helper to create test envelopes with required fields."""
    envelope = Envelope(
        envelope_id=envelope_id,
        envelope_version="1.0.0",
        envelope_class=envelope_class,
        trigger=EnvelopeTrigger(
            prediction_type=prediction_type,
            min_confidence=0.7,
        ),
        scope=EnvelopeScope(
            target_subsystem=subsystem,
            target_parameter=parameter,
        ),
        bounds=EnvelopeBounds(
            delta_type=DeltaType.PCT,
            max_increase=50.0,
            max_decrease=0.0,
        ),
        timebox=EnvelopeTimebox(
            max_duration_seconds=300,
            hard_expiry=True,
        ),
        baseline=EnvelopeBaseline(
            source=BaselineSource.CONFIG_DEFAULT,
            reference_id="test-baseline-v1",
            value=100.0,
        ),
        revert_on=[
            RevertReason.PREDICTION_EXPIRED,
            RevertReason.PREDICTION_DELETED,
            RevertReason.KILL_SWITCH,
        ],
    )
    # Validate the envelope
    validate_envelope(envelope)
    return envelope


@pytest.fixture
def coordinator():
    """Create a fresh CoordinationManager for each test."""
    return CoordinationManager()


class TestC4_S1_SafeCoexistence:
    """
    C4-S1: Safe Coexistence Scenario

    Reference: C4_S1_COORDINATION_SCENARIO.md

    Two envelopes in different subsystems should both apply successfully.
    """

    def test_t0_both_envelopes_apply_different_subsystems(self, coordinator):
        """
        T0: Both E-SAFETY and E-COST apply to different subsystems.

        Expected:
        - Both check_allowed() return True
        - Both envelopes become ACTIVE
        - No preemption occurs
        """
        # Create E-SAFETY (retry_policy.backoff_multiplier)
        e_safety = create_test_envelope(
            envelope_id="e-safety-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="retry_policy",
            parameter="backoff_multiplier",
        )

        # Create E-COST (scheduler.batch_size)
        e_cost = create_test_envelope(
            envelope_id="e-cost-001",
            envelope_class=EnvelopeClass.COST,
            subsystem="scheduler",
            parameter="batch_size",
        )

        # Apply E-SAFETY first
        success_safety, preempted_safety = coordinator.apply(e_safety)
        assert success_safety is True
        assert preempted_safety is None
        assert e_safety.lifecycle == EnvelopeLifecycle.ACTIVE

        # Apply E-COST second
        success_cost, preempted_cost = coordinator.apply(e_cost)
        assert success_cost is True
        assert preempted_cost is None
        assert e_cost.lifecycle == EnvelopeLifecycle.ACTIVE

        # Both should be active
        assert coordinator.active_envelope_count == 2

        # Audit trail should have 2 APPLIED decisions
        audit_trail = coordinator.get_audit_trail()
        applied_decisions = [r for r in audit_trail if r.decision == CoordinationDecisionType.APPLIED]
        assert len(applied_decisions) == 2


class TestC4_R1_SameParameterRejection:
    """
    C4-R1: Same-Parameter Conflict

    Reference: C4_ENVELOPE_COORDINATION_CONTRACT.md Section 5.1

    When two envelopes target the same parameter, the second is REJECTED.
    """

    def test_t1_t2_same_parameter_rejected(self, coordinator):
        """
        T1-T2: Second envelope targeting same parameter is rejected.

        Expected:
        - First envelope applies successfully
        - Second envelope is REJECTED
        - First envelope remains ACTIVE
        """
        # Create first envelope
        e1 = create_test_envelope(
            envelope_id="e-first-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="retry_policy",
            parameter="backoff_multiplier",
        )

        # Create second envelope targeting SAME parameter
        e2 = create_test_envelope(
            envelope_id="e-second-001",
            envelope_class=EnvelopeClass.RELIABILITY,  # Different class
            subsystem="retry_policy",
            parameter="backoff_multiplier",  # SAME parameter
        )

        # Apply first envelope
        success1, _ = coordinator.apply(e1)
        assert success1 is True
        assert e1.lifecycle == EnvelopeLifecycle.ACTIVE

        # Check if second envelope is allowed
        decision = coordinator.check_allowed(e2)
        assert decision.allowed is False
        assert decision.decision == CoordinationDecisionType.REJECTED
        assert decision.conflicting_envelope_id == "e-first-001"
        assert "Same-parameter" in decision.reason

        # First envelope should still be active
        assert coordinator.active_envelope_count == 1
        assert e1.lifecycle == EnvelopeLifecycle.ACTIVE

    def test_same_parameter_different_classes_still_rejected(self, coordinator):
        """
        Same-parameter rejection applies regardless of envelope class.

        Higher priority does NOT allow taking over a parameter.
        """
        # Create PERFORMANCE envelope first
        e_perf = create_test_envelope(
            envelope_id="e-perf-001",
            envelope_class=EnvelopeClass.PERFORMANCE,  # Lowest priority
            subsystem="scheduler",
            parameter="thread_count",
        )

        # Create SAFETY envelope for SAME parameter
        e_safety = create_test_envelope(
            envelope_id="e-safety-001",
            envelope_class=EnvelopeClass.SAFETY,  # Highest priority
            subsystem="scheduler",
            parameter="thread_count",  # SAME parameter
        )

        # Apply PERFORMANCE first
        success_perf, _ = coordinator.apply(e_perf)
        assert success_perf is True

        # SAFETY targeting same parameter should be REJECTED (not preempt)
        decision = coordinator.check_allowed(e_safety)
        assert decision.allowed is False
        assert decision.decision == CoordinationDecisionType.REJECTED
        assert decision.conflicting_envelope_id == "e-perf-001"


class TestC4_R4_PriorityPreemption:
    """
    C4-R4: Priority Preemption

    Reference: C4_ENVELOPE_COORDINATION_CONTRACT.md Section 5.4

    Higher-priority envelope preempts lower-priority envelope in same subsystem
    (different parameters).
    """

    def test_t3_higher_priority_preempts_lower(self, coordinator):
        """
        T3: SAFETY envelope preempts PERFORMANCE envelope in same subsystem.

        Expected:
        - PERFORMANCE envelope is reverted with PREEMPTED reason
        - SAFETY envelope becomes ACTIVE
        """
        # Create PERFORMANCE envelope
        e_perf = create_test_envelope(
            envelope_id="e-perf-001",
            envelope_class=EnvelopeClass.PERFORMANCE,
            subsystem="scheduler",
            parameter="thread_count",
        )

        # Create SAFETY envelope (different parameter, same subsystem)
        e_safety = create_test_envelope(
            envelope_id="e-safety-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="scheduler",
            parameter="max_concurrent",  # Different parameter
        )

        # Apply PERFORMANCE first
        success_perf, _ = coordinator.apply(e_perf)
        assert success_perf is True
        assert e_perf.lifecycle == EnvelopeLifecycle.ACTIVE
        assert coordinator.active_envelope_count == 1

        # Apply SAFETY (should preempt PERFORMANCE)
        success_safety, preempted_ids = coordinator.apply(e_safety)
        assert success_safety is True
        assert preempted_ids == ["e-perf-001"]
        assert e_safety.lifecycle == EnvelopeLifecycle.ACTIVE
        assert e_perf.lifecycle == EnvelopeLifecycle.REVERTED
        assert e_perf.revert_reason == RevertReason.PREEMPTED

        # Only SAFETY should be active now
        assert coordinator.active_envelope_count == 1

    def test_lower_priority_does_not_preempt_higher(self, coordinator):
        """
        Lower-priority envelope does NOT preempt higher-priority envelope.

        Expected:
        - Both envelopes remain active (different parameters)
        - No preemption occurs
        """
        # Create SAFETY envelope first
        e_safety = create_test_envelope(
            envelope_id="e-safety-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="scheduler",
            parameter="max_concurrent",
        )

        # Create PERFORMANCE envelope (different parameter, same subsystem)
        e_perf = create_test_envelope(
            envelope_id="e-perf-001",
            envelope_class=EnvelopeClass.PERFORMANCE,
            subsystem="scheduler",
            parameter="thread_count",
        )

        # Apply SAFETY first
        success_safety, _ = coordinator.apply(e_safety)
        assert success_safety is True

        # Apply PERFORMANCE (should NOT preempt SAFETY)
        success_perf, preempted_ids = coordinator.apply(e_perf)
        assert success_perf is True
        assert preempted_ids is None  # No preemption

        # Both should be active
        assert coordinator.active_envelope_count == 2
        assert e_safety.lifecycle == EnvelopeLifecycle.ACTIVE
        assert e_perf.lifecycle == EnvelopeLifecycle.ACTIVE


class TestC4_KillSwitch:
    """
    C4 Kill-Switch Tests

    Reference: C4_ENVELOPE_COORDINATION_CONTRACT.md Section 6, I-C4-6

    Kill-switch MUST revert ALL active envelopes atomically.
    """

    def test_t4_killswitch_reverts_all_envelopes(self, coordinator):
        """
        T4: Kill-switch reverts all active envelopes.

        Expected:
        - All envelopes reverted with KILL_SWITCH reason
        - No envelopes remain active
        - All envelopes show REVERTED lifecycle
        """
        # Create and apply multiple envelopes
        e1 = create_test_envelope(
            envelope_id="e1-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="retry_policy",
            parameter="backoff_multiplier",
        )
        e2 = create_test_envelope(
            envelope_id="e2-001",
            envelope_class=EnvelopeClass.COST,
            subsystem="scheduler",
            parameter="batch_size",
        )
        e3 = create_test_envelope(
            envelope_id="e3-001",
            envelope_class=EnvelopeClass.PERFORMANCE,
            subsystem="cache",
            parameter="ttl_seconds",
        )

        coordinator.apply(e1)
        coordinator.apply(e2)
        coordinator.apply(e3)

        assert coordinator.active_envelope_count == 3

        # Activate kill-switch
        reverted_ids = coordinator.kill_switch()

        # All should be reverted
        assert len(reverted_ids) == 3
        assert "e1-001" in reverted_ids
        assert "e2-001" in reverted_ids
        assert "e3-001" in reverted_ids

        # No active envelopes
        assert coordinator.active_envelope_count == 0

        # All envelopes show REVERTED with KILL_SWITCH reason
        for e in [e1, e2, e3]:
            assert e.lifecycle == EnvelopeLifecycle.REVERTED
            assert e.revert_reason == RevertReason.KILL_SWITCH

    def test_killswitch_blocks_new_envelopes(self, coordinator):
        """
        After kill-switch, no new envelopes may apply.

        Expected:
        - New envelope is REJECTED
        - Kill-switch remains active
        """
        # Activate kill-switch
        coordinator.kill_switch()
        assert coordinator.is_kill_switch_active is True

        # Try to apply new envelope
        e_new = create_test_envelope(
            envelope_id="e-new-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="retry_policy",
            parameter="max_retries",
        )

        decision = coordinator.check_allowed(e_new)
        assert decision.allowed is False
        assert decision.decision == CoordinationDecisionType.REJECTED
        assert "Kill-switch" in decision.reason


class TestC4_IndependentRollback:
    """
    C4 Independent Rollback Tests

    Reference: C4_ENVELOPE_COORDINATION_CONTRACT.md Section 7

    Envelopes in different subsystems should rollback independently.
    """

    def test_t5_independent_rollback(self, coordinator):
        """
        T5: Reverting one envelope does not affect another.

        Expected:
        - Reverting E1 leaves E2 active
        - E2 can still be reverted independently
        """
        # Create and apply two envelopes in different subsystems
        e1 = create_test_envelope(
            envelope_id="e1-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="retry_policy",
            parameter="backoff_multiplier",
        )
        e2 = create_test_envelope(
            envelope_id="e2-001",
            envelope_class=EnvelopeClass.COST,
            subsystem="scheduler",
            parameter="batch_size",
        )

        coordinator.apply(e1)
        coordinator.apply(e2)

        assert coordinator.active_envelope_count == 2

        # Revert e1 only
        success = coordinator.revert("e1-001", RevertReason.PREDICTION_EXPIRED)
        assert success is True
        assert e1.lifecycle == EnvelopeLifecycle.REVERTED
        assert e1.revert_reason == RevertReason.PREDICTION_EXPIRED

        # e2 should still be active
        assert e2.lifecycle == EnvelopeLifecycle.ACTIVE
        assert coordinator.active_envelope_count == 1

        # Revert e2 independently
        success2 = coordinator.revert("e2-001", RevertReason.PREDICTION_DELETED)
        assert success2 is True
        assert e2.lifecycle == EnvelopeLifecycle.REVERTED
        assert e2.revert_reason == RevertReason.PREDICTION_DELETED

        assert coordinator.active_envelope_count == 0

    def test_timebox_expiry_independent(self, coordinator):
        """
        Timebox expiry of one envelope does not affect another.

        Expected:
        - Expiring E1 leaves E2 active
        - E2's timebox remains independent
        """
        e1 = create_test_envelope(
            envelope_id="e1-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="retry_policy",
            parameter="backoff_multiplier",
        )
        e2 = create_test_envelope(
            envelope_id="e2-001",
            envelope_class=EnvelopeClass.COST,
            subsystem="scheduler",
            parameter="batch_size",
        )

        coordinator.apply(e1)
        coordinator.apply(e2)

        # Expire e1
        success = coordinator.expire_envelope("e1-001")
        assert success is True
        assert e1.lifecycle == EnvelopeLifecycle.EXPIRED
        assert e1.revert_reason == RevertReason.TIMEBOX_EXPIRED

        # e2 still active
        assert e2.lifecycle == EnvelopeLifecycle.ACTIVE
        assert coordinator.active_envelope_count == 1


class TestC4_AuditTrail:
    """
    C4 Audit Trail Tests (I-C4-7)

    Every coordination decision MUST be audited.
    """

    def test_all_decisions_audited(self, coordinator):
        """
        All coordination decisions (APPLIED, REJECTED, PREEMPTED) are audited.
        """
        # Create envelopes
        e1 = create_test_envelope(
            envelope_id="e1-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="retry_policy",
            parameter="backoff_multiplier",
        )
        e2 = create_test_envelope(
            envelope_id="e2-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="retry_policy",
            parameter="backoff_multiplier",  # Same parameter - will be rejected
        )

        # Apply e1 (should produce APPLIED audit)
        coordinator.apply(e1)

        # Try e2 (should produce REJECTED audit)
        coordinator.check_allowed(e2)

        audit_trail = coordinator.get_audit_trail()

        # Should have at least 2 audit records
        assert len(audit_trail) >= 2

        # Verify audit record structure
        for record in audit_trail:
            assert isinstance(record, CoordinationAuditRecord)
            assert record.audit_id is not None
            assert record.envelope_id is not None
            assert record.envelope_class is not None
            assert record.decision in CoordinationDecisionType
            assert record.reason is not None
            assert record.timestamp is not None

    def test_preemption_audited(self, coordinator):
        """
        Preemption events are audited with preempting_envelope_id.
        """
        e_perf = create_test_envelope(
            envelope_id="e-perf-001",
            envelope_class=EnvelopeClass.PERFORMANCE,
            subsystem="scheduler",
            parameter="thread_count",
        )
        e_safety = create_test_envelope(
            envelope_id="e-safety-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="scheduler",
            parameter="max_concurrent",
        )

        coordinator.apply(e_perf)
        coordinator.apply(e_safety)  # Should preempt e_perf

        audit_trail = coordinator.get_audit_trail()
        preempt_records = [r for r in audit_trail if r.decision == CoordinationDecisionType.PREEMPTED]

        assert len(preempt_records) == 1
        assert preempt_records[0].envelope_id == "e-perf-001"
        assert preempt_records[0].preempting_envelope_id == "e-safety-001"


class TestC4_EnvelopeClassValidation:
    """
    C4 Envelope Class Validation (CI-C4-1)

    Every envelope MUST declare exactly one class.
    """

    def test_envelope_without_class_rejected(self, coordinator):
        """
        Envelope without envelope_class is rejected by coordinator.
        """
        # Create envelope without class (bypassing validation)
        envelope = Envelope(
            envelope_id="e-no-class-001",
            envelope_version="1.0.0",
            envelope_class=None,  # No class
            trigger=EnvelopeTrigger(
                prediction_type="test",
                min_confidence=0.7,
            ),
            scope=EnvelopeScope(
                target_subsystem="test",
                target_parameter="param",
            ),
            bounds=EnvelopeBounds(
                delta_type=DeltaType.PCT,
                max_increase=50.0,
                max_decrease=0.0,
            ),
            timebox=EnvelopeTimebox(
                max_duration_seconds=300,
                hard_expiry=True,
            ),
            baseline=EnvelopeBaseline(
                source=BaselineSource.CONFIG_DEFAULT,
                reference_id="test-v1",
            ),
            revert_on=[
                RevertReason.PREDICTION_EXPIRED,
                RevertReason.PREDICTION_DELETED,
                RevertReason.KILL_SWITCH,
            ],
            # Skip validation by setting lifecycle directly
            lifecycle=EnvelopeLifecycle.VALIDATED,
        )

        # Coordinator should reject
        decision = coordinator.check_allowed(envelope)
        assert decision.allowed is False
        assert decision.decision == CoordinationDecisionType.REJECTED
        assert "I-C4-2" in decision.reason or "class" in decision.reason.lower()


class TestC4_CoordinationStats:
    """
    C4 Coordination Statistics.

    Helper methods for monitoring and debugging.
    """

    def test_coordination_stats(self, coordinator):
        """
        get_coordination_stats() returns accurate statistics.
        """
        e1 = create_test_envelope(
            envelope_id="e1-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="retry_policy",
            parameter="backoff_multiplier",
        )
        e2 = create_test_envelope(
            envelope_id="e2-001",
            envelope_class=EnvelopeClass.COST,
            subsystem="scheduler",
            parameter="batch_size",
        )

        coordinator.apply(e1)
        coordinator.apply(e2)

        stats = coordinator.get_coordination_stats()

        assert stats["active_envelopes"] == 2
        assert stats["kill_switch_active"] is False
        assert stats["envelopes_by_class"]["safety"] == 1
        assert stats["envelopes_by_class"]["cost"] == 1
        assert stats["envelopes_by_class"]["reliability"] == 0
        assert stats["envelopes_by_class"]["performance"] == 0
        assert len(stats["controlled_parameters"]) == 2

    def test_get_envelopes_by_class(self, coordinator):
        """
        get_envelopes_by_class() returns correct envelopes.
        """
        e1 = create_test_envelope(
            envelope_id="e1-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="retry_policy",
            parameter="backoff_multiplier",
        )
        e2 = create_test_envelope(
            envelope_id="e2-001",
            envelope_class=EnvelopeClass.SAFETY,
            subsystem="scheduler",
            parameter="batch_size",
        )
        e3 = create_test_envelope(
            envelope_id="e3-001",
            envelope_class=EnvelopeClass.COST,
            subsystem="cache",
            parameter="ttl_seconds",
        )

        coordinator.apply(e1)
        coordinator.apply(e2)
        coordinator.apply(e3)

        safety_envelopes = coordinator.get_envelopes_by_class(EnvelopeClass.SAFETY)
        assert len(safety_envelopes) == 2

        cost_envelopes = coordinator.get_envelopes_by_class(EnvelopeClass.COST)
        assert len(cost_envelopes) == 1

        reliability_envelopes = coordinator.get_envelopes_by_class(EnvelopeClass.RELIABILITY)
        assert len(reliability_envelopes) == 0
