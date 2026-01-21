# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-035 (Governance Failure Mode)
"""
Unit tests for GAP-035: Governance Failure Mode Handling.

Tests that the system handles governance evaluation failures correctly
with configurable fail-closed vs fail-open behavior.
"""

import pytest
from app.policy.failure_mode_handler import (
    handle_evaluation_error,
    handle_policy_failure,
    FailureDecision,
    FailureMode,
    FailureType,
)


class TestFailureModeHandler:
    """Test suite for failure mode handling."""

    def test_default_is_fail_closed(self):
        """Default failure mode should be fail-closed (block on error)."""
        error = ValueError("Test evaluation error")
        context = {"run_id": "test-run", "tenant_id": "test-tenant"}

        decision = handle_evaluation_error(error, context)

        assert decision.should_block is True
        assert decision.failure_mode == FailureMode.FAIL_CLOSED

    def test_handle_policy_failure_with_fail_closed(self):
        """FAIL_CLOSED mode should block execution on error."""
        error = RuntimeError("Policy evaluation crashed")
        context = {"run_id": "test-run", "tenant_id": "test-tenant"}

        decision = handle_policy_failure(
            error=error,
            context=context,
            failure_type=FailureType.EVALUATION_ERROR,
        )

        assert decision.should_block is True
        assert decision.action == "STOP"

    def test_decision_includes_failure_type(self):
        """FailureDecision should include the failure type."""
        error = TimeoutError("Policy evaluation timeout")
        context = {"run_id": "test-run"}

        decision = handle_evaluation_error(error, context)

        assert decision.failure_type is not None
        assert decision.failure_type == FailureType.EVALUATION_ERROR

    def test_decision_includes_reason(self):
        """FailureDecision should include a reason."""
        error = ValueError("Test error")
        context = {"run_id": "run-123", "tenant_id": "tenant-456"}

        decision = handle_evaluation_error(error, context)

        assert decision.reason is not None
        assert len(decision.reason) > 0

    def test_decision_includes_timestamp(self):
        """FailureDecision should include a timestamp."""
        error = ValueError("Test error")
        context = {"run_id": "test-run"}

        decision = handle_evaluation_error(error, context)

        assert decision.timestamp is not None

    def test_audit_required_on_failure(self):
        """FailureDecision should require audit."""
        error = RuntimeError("Test error")
        context = {"run_id": "test-run"}

        decision = handle_evaluation_error(error, context)

        assert decision.audit_required is True


class TestFailureMode:
    """Test FailureMode enum."""

    def test_all_failure_modes_exist(self):
        """All expected failure modes should exist."""
        assert FailureMode.FAIL_CLOSED
        assert FailureMode.FAIL_WARN
        assert FailureMode.FAIL_OPEN


class TestFailureType:
    """Test FailureType enum."""

    def test_all_failure_types_exist(self):
        """All expected failure types should exist."""
        assert FailureType.MISSING_POLICY
        assert FailureType.EVALUATION_ERROR
        assert FailureType.TIMEOUT
        assert FailureType.INVALID_CONTEXT
        assert FailureType.ENGINE_UNAVAILABLE
        assert FailureType.UNKNOWN
