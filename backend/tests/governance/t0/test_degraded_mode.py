# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-070 (Degraded Mode)
"""
Unit tests for GAP-070: Degraded Mode.

Tests that the system can enter degraded mode (block new runs,
complete existing with WARN).
"""

import pytest
from app.policy.degraded_mode import (
    enter_degraded_mode,
    exit_degraded_mode,
    is_degraded_mode_active,
    get_degraded_mode_status,
    should_allow_new_run,
    DegradedModeStatus,
)


class TestDegradedMode:
    """Test suite for degraded mode."""

    def test_degraded_mode_starts_inactive(self):
        """Degraded mode should be inactive by default."""
        exit_degraded_mode()  # Reset state

        assert is_degraded_mode_active() is False

    def test_enter_degraded_mode(self):
        """Should be able to enter degraded mode."""
        result = enter_degraded_mode(
            reason="Policy service unavailable",
            entered_by="system",
        )

        assert result.success is True
        assert is_degraded_mode_active() is True

    def test_exit_degraded_mode(self):
        """Should be able to exit degraded mode."""
        enter_degraded_mode(reason="Test", entered_by="admin")
        result = exit_degraded_mode(exited_by="admin")

        assert result.success is True
        assert is_degraded_mode_active() is False

    def test_new_runs_blocked_in_degraded_mode(self):
        """New runs should be blocked in degraded mode."""
        enter_degraded_mode(reason="Test", entered_by="admin")

        allowed = should_allow_new_run(run_id="new-run-123")

        assert allowed is False

        exit_degraded_mode()

    def test_new_runs_allowed_in_normal_mode(self):
        """New runs should be allowed in normal mode."""
        exit_degraded_mode()  # Ensure normal mode

        allowed = should_allow_new_run(run_id="new-run-123")

        assert allowed is True

    def test_status_includes_reason(self):
        """Degraded mode status should include reason."""
        enter_degraded_mode(
            reason="Database connection issues",
            entered_by="health-check",
        )

        status = get_degraded_mode_status()

        assert status.is_active is True
        assert status.reason == "Database connection issues"
        assert status.entered_by == "health-check"

        exit_degraded_mode()

    def test_status_includes_timestamp(self):
        """Degraded mode status should include entry timestamp."""
        enter_degraded_mode(reason="Test", entered_by="admin")

        status = get_degraded_mode_status()

        assert status.entered_at is not None

        exit_degraded_mode()

    def test_idempotent_entry(self):
        """Multiple entries should be idempotent."""
        enter_degraded_mode(reason="First", entered_by="admin1")
        enter_degraded_mode(reason="Second", entered_by="admin2")

        assert is_degraded_mode_active() is True

        status = get_degraded_mode_status()
        # Latest entry should be reflected
        assert status.entered_by == "admin2"

        exit_degraded_mode()

    def test_idempotent_exit(self):
        """Exiting when not active should be safe."""
        exit_degraded_mode()  # Ensure inactive

        result = exit_degraded_mode()
        assert result.success is True

    def test_existing_runs_continue_with_warn(self):
        """Existing runs should continue with WARN in degraded mode."""
        # This tests the policy behavior for in-flight runs
        enter_degraded_mode(reason="Test", entered_by="admin")

        status = get_degraded_mode_status()

        # In degraded mode, existing runs continue but with warnings
        assert status.existing_runs_action == "WARN"

        exit_degraded_mode()


class TestDegradedModeStatus:
    """Test DegradedModeStatus dataclass."""

    def test_inactive_status(self):
        """Inactive status should have correct fields."""
        status = DegradedModeStatus(
            is_active=False,
            reason=None,
            entered_by=None,
            entered_at=None,
        )

        assert status.is_active is False
        assert status.reason is None

    def test_active_status(self):
        """Active status should have all required fields."""
        status = DegradedModeStatus(
            is_active=True,
            reason="Test reason",
            entered_by="admin",
            entered_at="2024-01-01T00:00:00Z",
            existing_runs_action="WARN",
        )

        assert status.is_active is True
        assert status.reason == "Test reason"
        assert status.existing_runs_action == "WARN"
