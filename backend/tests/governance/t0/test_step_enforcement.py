# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-016 (Step Enforcement)
"""
Unit tests for GAP-016: Step Enforcement.

Tests the centralized step enforcement function that evaluates
policies after each step completion.
"""

import pytest
from app.hoc.int.worker.enforcement.step_enforcement import (
    enforce_before_step_completion,
    EnforcementResult,
    EnforcementHaltReason,
    StepEnforcementError,
)


class MockRunContext:
    """Mock run context for testing."""
    def __init__(self, run_id="run-123", tenant_id="tenant-001", step_index=0):
        self.run_id = run_id
        self.tenant_id = tenant_id
        self.step_index = step_index


class TestStepEnforcement:
    """Test suite for step enforcement."""

    def test_enforce_before_step_completion_returns_result(self):
        """enforce_before_step_completion should return an EnforcementResult."""
        run_ctx = MockRunContext()
        step_result = {"status": "success"}

        result = enforce_before_step_completion(
            run_context=run_ctx,
            step_result=step_result,
            prevention_engine=None,
        )

        assert isinstance(result, EnforcementResult)

    def test_enforcement_result_has_required_fields(self):
        """EnforcementResult should have all required fields."""
        run_ctx = MockRunContext()
        step_result = {"status": "success"}

        result = enforce_before_step_completion(
            run_context=run_ctx,
            step_result=step_result,
        )

        assert hasattr(result, "should_halt")
        assert hasattr(result, "halt_reason")
        assert hasattr(result, "policy_id")
        assert hasattr(result, "message")
        assert hasattr(result, "checked_at")

    def test_enforcement_result_should_halt_boolean(self):
        """should_halt should be a boolean."""
        run_ctx = MockRunContext()
        step_result = {"status": "success"}

        result = enforce_before_step_completion(
            run_context=run_ctx,
            step_result=step_result,
        )

        assert isinstance(result.should_halt, bool)

    def test_enforcement_result_checked_at_timestamp(self):
        """checked_at should be an ISO timestamp string."""
        run_ctx = MockRunContext()
        step_result = {"status": "success"}

        result = enforce_before_step_completion(
            run_context=run_ctx,
            step_result=step_result,
        )

        assert isinstance(result.checked_at, str)
        # Should be ISO format
        assert "T" in result.checked_at


class TestEnforcementResult:
    """Test EnforcementResult dataclass."""

    def test_allow_result(self):
        """Non-halt result should have should_halt=False."""
        result = EnforcementResult(
            should_halt=False,
            halt_reason=None,
            policy_id=None,
            message="Within limits",
            checked_at="2026-01-21T00:00:00Z",
        )

        assert result.should_halt is False
        assert result.halt_reason is None

    def test_halt_result(self):
        """Halt result should have policy details."""
        result = EnforcementResult(
            should_halt=True,
            halt_reason=EnforcementHaltReason.POLICY_STOP,
            policy_id="pol-001",
            message="Token limit exceeded",
            checked_at="2026-01-21T00:00:00Z",
        )

        assert result.should_halt is True
        assert result.halt_reason == EnforcementHaltReason.POLICY_STOP
        assert result.policy_id == "pol-001"

    def test_halt_reason_enum_values(self):
        """EnforcementHaltReason should have expected values."""
        assert EnforcementHaltReason.POLICY_STOP.value == "policy_stop"
        assert EnforcementHaltReason.POLICY_KILL.value == "policy_kill"
        assert EnforcementHaltReason.BUDGET_EXCEEDED.value == "budget_exceeded"
        assert EnforcementHaltReason.RATE_LIMITED.value == "rate_limited"


class TestStepEnforcementError:
    """Test StepEnforcementError exception."""

    def test_exception_has_result(self):
        """Exception should contain EnforcementResult."""
        result = EnforcementResult(
            should_halt=True,
            halt_reason=EnforcementHaltReason.POLICY_STOP,
            policy_id="pol-001",
            message="Test halt",
            checked_at="2026-01-21T00:00:00Z",
        )

        error = StepEnforcementError(result)

        assert error.result == result
        assert "Test halt" in str(error)

    def test_exception_message_includes_reason(self):
        """Exception message should include halt reason."""
        result = EnforcementResult(
            should_halt=True,
            halt_reason=EnforcementHaltReason.BUDGET_EXCEEDED,
            policy_id="budget-001",
            message="Budget exceeded",
            checked_at="2026-01-21T00:00:00Z",
        )

        error = StepEnforcementError(result)

        # Error message includes halt reason (enum name or value)
        assert "BUDGET_EXCEEDED" in str(error) or "budget_exceeded" in str(error)
