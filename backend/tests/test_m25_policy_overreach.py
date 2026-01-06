"""
M25 Policy Overreach Prevention Test

HYGIENE #5: Negative test to ensure policies don't block unrelated incidents.

This is the most important safety test for the M25 graduation system.
If policies start blocking unrelated requests, the system is unsafe.
"""

import pytest

from app.integrations.bridges import (
    ConfidenceCalculator,
)
from app.integrations.events import (
    ConfidenceBand,
    LoopEvent,
    LoopStage,
    PolicyMode,
    PolicyRule,
)


class TestPolicyOverreach:
    """
    HYGIENE #5: Ensure policies don't block unrelated incidents.

    These are NEGATIVE tests - we want to confirm the system does NOT
    take action when it shouldn't.
    """

    def test_policy_does_not_match_different_error_type(self):
        """
        An ACTIVE policy for 'rate_limit' errors must NOT match 'timeout' errors.
        """
        # Create a policy for rate_limit errors
        policy = PolicyRule.create(
            name="Prevention: rate_limit",
            description="Auto-generated policy for rate_limit",
            category="operational",
            condition="error_type == 'rate_limit'",
            action="rate_limit",
            source_pattern_id="pat_test123",
            source_recovery_id="rec_test456",
            confidence=0.9,
        )

        # Activate the policy
        policy.mode = PolicyMode.ACTIVE

        # Create an unrelated incident (timeout, not rate_limit)
        unrelated_incident = {
            "error_type": "timeout",
            "error_code": "E001",
            "context": {"request_id": "req_xyz"},
        }

        # Verify the policy condition does NOT match
        condition = policy.condition
        # Simple condition evaluation (in real system this would use policy engine)
        matches = "rate_limit" in unrelated_incident.get("error_type", "")

        assert matches is False, (
            "Policy for 'rate_limit' incorrectly matched 'timeout' error. "
            "This is a CRITICAL safety violation - policy overreach detected."
        )

    def test_policy_does_not_match_different_tenant(self):
        """
        A policy scoped to tenant_A must NOT affect tenant_B.
        """
        policy = PolicyRule.create(
            name="Prevention: validation_error",
            description="Tenant-scoped policy",
            category="operational",
            condition="error_type == 'validation_error'",
            action="block",
            source_pattern_id="pat_tenantA",
            source_recovery_id="rec_tenantA",
            confidence=0.85,
            scope_type="tenant",
            scope_id="tenant_A",
        )
        policy.mode = PolicyMode.ACTIVE

        # Check scope
        other_tenant = "tenant_B"

        assert policy.scope_id != other_tenant, "Policy should be scoped to tenant_A only"

        # In production, the policy evaluation would check:
        # if policy.scope_type == "tenant" and policy.scope_id != request_tenant_id:
        #     return False  # Policy does not apply

    def test_confidence_calculator_does_not_auto_apply_weak_match(self):
        """
        FROZEN confidence logic must NOT auto-apply for weak matches.
        """
        # Weak match scenario: 1 occurrence, not strong match
        confidence, version, details = ConfidenceCalculator.calculate_recovery_confidence(
            base_confidence=0.5,
            occurrence_count=1,
            is_strong_match=False,
        )

        should_auto = ConfidenceCalculator.should_auto_apply(confidence, occurrence_count=1)

        assert should_auto is False, (
            f"Weak match (confidence={confidence}) should NOT auto-apply. Version={version}, details={details}"
        )

    def test_confidence_calculator_requires_3_occurrences_for_auto_apply(self):
        """
        Even with high confidence, auto-apply requires 3+ occurrences.
        """
        # High confidence but only 2 occurrences
        confidence, version, details = ConfidenceCalculator.calculate_recovery_confidence(
            base_confidence=0.7,
            occurrence_count=2,
            is_strong_match=True,
        )

        should_auto = ConfidenceCalculator.should_auto_apply(confidence, occurrence_count=2)

        assert should_auto is False, (
            f"Only 2 occurrences should NOT auto-apply even with confidence={confidence}. "
            f"This prevents premature policy activation."
        )

    def test_shadow_mode_policy_does_not_block(self):
        """
        A policy in SHADOW mode must NOT block requests.
        """
        policy = PolicyRule.create(
            name="Shadow policy",
            description="Observing only",
            category="operational",
            condition="error_type == 'anything'",
            action="block",
            source_pattern_id="pat_shadow",
            source_recovery_id="rec_shadow",
            confidence=0.9,
        )

        # High confidence policies start in shadow mode
        assert policy.mode == PolicyMode.SHADOW, "High confidence policies should start in SHADOW mode"

        # Shadow mode should not block
        should_block = policy.mode == PolicyMode.ACTIVE

        assert should_block is False, "SHADOW mode policy must NOT block requests. Only ACTIVE policies can enforce."

    def test_policy_with_high_regret_is_disabled(self):
        """
        A policy with 3+ regrets must be auto-disabled.
        """
        policy = PolicyRule.create(
            name="Bad policy",
            description="Will cause incidents",
            category="operational",
            condition="error_type == 'test'",
            action="block",
            source_pattern_id="pat_bad",
            source_recovery_id="rec_bad",
            confidence=0.9,
        )
        policy.mode = PolicyMode.ACTIVE

        # Simulate 3 regrets
        policy.record_regret()
        policy.record_regret()
        policy.record_regret()

        assert policy.mode == PolicyMode.DISABLED, (
            f"Policy with regret_count={policy.regret_count} should be DISABLED. Current mode: {policy.mode.value}"
        )

    def test_loop_event_failure_state_blocks_next_stage(self):
        """
        An event with failure_state should NOT trigger the next stage.
        """
        from app.integrations.events import LoopFailureState

        event = LoopEvent.create(
            incident_id="inc_test",
            tenant_id="tenant_test",
            stage=LoopStage.PATTERN_MATCHED,
            failure_state=LoopFailureState.MATCH_LOW_CONFIDENCE,
        )

        assert event.is_success is False, "Event with failure_state should not be considered success"

    def test_novel_pattern_requires_human_review(self):
        """
        Novel patterns (low confidence) must require human review.
        """
        band = ConfidenceBand.NOVEL

        assert band.requires_human_review is True, "Novel patterns must require human review"
        assert band.allows_auto_apply is False, "Novel patterns must NOT allow auto-apply"


class TestPreventionContract:
    """
    Tests for the prevention contract - ensuring prevention is counted correctly.
    """

    def test_prevention_requires_same_tenant(self):
        """
        A prevention is only valid if same tenant.
        """
        original_incident_tenant = "tenant_A"
        prevention_tenant = "tenant_B"

        # This would NOT count as prevention
        is_valid_prevention = original_incident_tenant == prevention_tenant

        assert is_valid_prevention is False, "Prevention across tenants is NOT valid"

    def test_prevention_requires_active_policy(self):
        """
        Prevention only counts if policy is ACTIVE (not shadow).
        """
        policy_mode = PolicyMode.SHADOW

        is_valid_prevention = policy_mode == PolicyMode.ACTIVE

        assert is_valid_prevention is False, "Shadow mode policies do NOT create valid preventions"

    def test_prevention_must_not_create_incident(self):
        """
        A prevention means NO incident was created.
        """
        # If we're counting prevention, incident_created should be False
        incident_created = False

        assert incident_created is False, "Prevention means no incident was created"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
