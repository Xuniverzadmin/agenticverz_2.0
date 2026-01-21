# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-031 (Policy Binding Moments)
"""
Unit tests for GAP-031: Policy Binding Moment Enforcement.

Tests that policies are evaluated at correct points in execution lifecycle.
"""

import pytest
from app.policy.binding_moment_enforcer import (
    should_evaluate_policy,
    EvaluationPoint,
    BindingMoment,
    BindingDecision,
)


class MockPolicy:
    """Mock policy for testing."""
    def __init__(self, id: str, bind_at: str = None, monitored_fields: list = None):
        self.id = id
        self.bind_at = bind_at
        self.monitored_fields = monitored_fields or []


class TestBindingMomentEnforcer:
    """Test suite for binding moment enforcement."""

    def test_always_binding_evaluates_at_all_points(self):
        """ALWAYS binding should evaluate at every point."""
        policy = MockPolicy(id="pol-001", bind_at="ALWAYS")
        context = {"run_id": "test-run", "step_index": 0}

        for point in EvaluationPoint:
            decision = should_evaluate_policy(policy, context, point)
            assert decision.should_evaluate is True

    def test_run_start_binding_only_at_run_init(self):
        """RUN_START binding should evaluate at RUN_INIT."""
        policy = MockPolicy(id="pol-001", bind_at="RUN_START")
        context = {"run_id": "test-run", "step_index": 0}

        # Should evaluate at RUN_INIT
        decision = should_evaluate_policy(policy, context, EvaluationPoint.RUN_INIT)
        assert decision.should_evaluate is True

        # After first evaluation, should NOT evaluate again (cached)
        decision = should_evaluate_policy(policy, context, EvaluationPoint.STEP_PRE)
        assert decision.should_evaluate is False

        decision = should_evaluate_policy(policy, context, EvaluationPoint.STEP_POST)
        assert decision.should_evaluate is False

    def test_step_start_binding_at_step_pre(self):
        """STEP_START binding should evaluate at STEP_PRE point."""
        policy = MockPolicy(id="pol-001", bind_at="STEP_START")
        context = {"run_id": "test-run", "step_index": 0}

        decision = should_evaluate_policy(policy, context, EvaluationPoint.STEP_PRE)
        assert decision.should_evaluate is True

        decision = should_evaluate_policy(policy, context, EvaluationPoint.STEP_POST)
        assert decision.should_evaluate is False

    def test_step_end_binding_at_step_post(self):
        """STEP_END binding should evaluate at STEP_POST point."""
        policy = MockPolicy(id="pol-001", bind_at="STEP_END")
        context = {"run_id": "test-run", "step_index": 0}

        decision = should_evaluate_policy(policy, context, EvaluationPoint.STEP_POST)
        assert decision.should_evaluate is True

        decision = should_evaluate_policy(policy, context, EvaluationPoint.STEP_PRE)
        assert decision.should_evaluate is False

    def test_none_binding_defaults_to_always(self):
        """Missing bind_at should default to ALWAYS behavior."""
        policy = MockPolicy(id="pol-001", bind_at=None)
        context = {"run_id": "test-run", "step_index": 0}

        # Should evaluate at all points by default
        decision = should_evaluate_policy(policy, context, EvaluationPoint.STEP_POST)
        assert decision.should_evaluate is True

    def test_on_change_binding_skips_unchanged(self):
        """ON_CHANGE binding should only evaluate when monitored fields change."""
        policy = MockPolicy(id="pol-001", bind_at="ON_CHANGE", monitored_fields=["status"])

        # No changes - should not evaluate
        context = {
            "run_id": "test-run",
            "step_index": 0,
            "prev_field_values": {"status": "running"},
            "curr_field_values": {"status": "running"},
        }
        decision = should_evaluate_policy(policy, context, EvaluationPoint.STEP_POST)
        assert decision.should_evaluate is False

        # With field change - should evaluate
        context["curr_field_values"] = {"status": "completed"}
        decision = should_evaluate_policy(policy, context, EvaluationPoint.STEP_POST)
        assert decision.should_evaluate is True

    def test_decision_includes_reason(self):
        """BindingDecision should include reason for skip."""
        policy = MockPolicy(id="pol-001", bind_at="RUN_START")
        context = {"run_id": "test-run", "step_index": 0}

        decision = should_evaluate_policy(policy, context, EvaluationPoint.STEP_POST)
        assert decision.should_evaluate is False
        assert decision.reason is not None
        assert len(decision.reason) > 0


class TestEvaluationPoint:
    """Test EvaluationPoint enum."""

    def test_all_evaluation_points_exist(self):
        """All expected evaluation points should exist."""
        assert EvaluationPoint.RUN_INIT
        assert EvaluationPoint.STEP_PRE
        assert EvaluationPoint.STEP_POST
        assert EvaluationPoint.MID_RUN
