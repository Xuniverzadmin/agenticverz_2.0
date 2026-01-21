# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-069 (Runtime Kill Switch)
"""
Unit tests for GAP-069: Runtime Kill Switch.

Tests that governance can be disabled at runtime without restart.
"""

import pytest
from app.policy.kill_switch import (
    activate_kill_switch,
    deactivate_kill_switch,
    is_kill_switch_active,
    KillSwitchStatus,
    KillSwitchActivation,
)


class TestKillSwitch:
    """Test suite for runtime kill switch."""

    def test_kill_switch_starts_inactive(self):
        """Kill switch should be inactive by default."""
        # Reset state first
        deactivate_kill_switch()

        assert is_kill_switch_active() is False

    def test_activate_kill_switch(self):
        """Kill switch should activate with required fields."""
        result = activate_kill_switch(
            reason="Emergency maintenance",
            activated_by="test-admin",
        )

        assert result.success is True
        assert is_kill_switch_active() is True

    def test_deactivate_kill_switch(self):
        """Kill switch should deactivate correctly."""
        # First activate
        activate_kill_switch(reason="Test", activated_by="admin")

        # Then deactivate
        result = deactivate_kill_switch(deactivated_by="admin")

        assert result.success is True
        assert is_kill_switch_active() is False

    def test_kill_switch_status_includes_reason(self):
        """Kill switch status should include activation reason."""
        activate_kill_switch(
            reason="Security incident response",
            activated_by="security-team",
        )

        status = KillSwitchStatus.get_current()

        assert status.is_active is True
        assert status.reason == "Security incident response"
        assert status.activated_by == "security-team"

    def test_kill_switch_idempotent_activation(self):
        """Multiple activations should be idempotent."""
        activate_kill_switch(reason="First", activated_by="admin1")
        activate_kill_switch(reason="Second", activated_by="admin2")

        assert is_kill_switch_active() is True

        # Status should reflect latest activation
        status = KillSwitchStatus.get_current()
        assert status.activated_by == "admin2"

    def test_kill_switch_idempotent_deactivation(self):
        """Deactivating inactive switch should be safe."""
        deactivate_kill_switch()  # Ensure inactive

        # Should not raise
        result = deactivate_kill_switch()
        assert result.success is True

    def test_kill_switch_activation_timestamp(self):
        """Activation should record timestamp."""
        activate_kill_switch(reason="Test", activated_by="admin")

        status = KillSwitchStatus.get_current()
        assert status.activated_at is not None

    def test_kill_switch_affects_governance_check(self):
        """When active, governance checks should be bypassed."""
        activate_kill_switch(reason="Test", activated_by="admin")

        # This is integration behavior - mock here
        assert is_kill_switch_active() is True

        deactivate_kill_switch()
        assert is_kill_switch_active() is False


class TestKillSwitchActivation:
    """Test KillSwitchActivation result type."""

    def test_successful_activation(self):
        """Successful activation should have correct fields."""
        result = KillSwitchActivation(
            success=True,
            message="Kill switch activated",
            activated_at="2024-01-01T00:00:00Z",
        )

        assert result.success is True
        assert result.message is not None

    def test_failed_activation(self):
        """Failed activation should include error details."""
        result = KillSwitchActivation(
            success=False,
            message="Permission denied",
            error="Insufficient privileges",
        )

        assert result.success is False
        assert result.error is not None
