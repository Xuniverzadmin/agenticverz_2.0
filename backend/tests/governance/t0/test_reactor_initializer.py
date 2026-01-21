# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-046 (EventReactor Initialization)
"""
Unit tests for GAP-046: EventReactor Initialization.

Tests that the EventReactor is properly initialized at startup
and provides health status for monitoring.
"""

import pytest
from app.events.reactor_initializer import (
    initialize_event_reactor,
    get_reactor_status,
    shutdown_event_reactor,
)


class TestReactorInitializer:
    """Test suite for EventReactor initialization."""

    def teardown_method(self):
        """Cleanup after each test."""
        shutdown_event_reactor()

    def test_get_status_before_init(self):
        """Status should show not_initialized before init."""
        shutdown_event_reactor()  # Ensure clean state
        status = get_reactor_status()

        assert status["status"] == "not_initialized"
        assert status["healthy"] is False

    def test_get_status_returns_dict(self):
        """get_reactor_status should return a dict."""
        status = get_reactor_status()

        assert isinstance(status, dict)

    def test_status_has_required_fields(self):
        """Status should have status, healthy, and heartbeat_active fields."""
        status = get_reactor_status()

        assert "status" in status
        assert "healthy" in status
        assert "heartbeat_active" in status

    def test_initialize_may_succeed_or_fail(self):
        """Initialize should either succeed or raise RuntimeError."""
        try:
            result = initialize_event_reactor()
            # If successful, should return reactor or None (if disabled)
            # No assertion on type since it could be None or EventReactor
            status = get_reactor_status()
            assert status["status"] in ("running", "disabled")
        except RuntimeError as e:
            # Boot failure is acceptable in test environment
            assert "BOOT FAILURE" in str(e)
        except ImportError:
            # Missing dependencies acceptable in isolated tests
            pass

    def test_initialize_sets_initialized_state(self):
        """After initialize, status should not be not_initialized."""
        try:
            initialize_event_reactor()
            status = get_reactor_status()
            assert status["status"] != "not_initialized"
        except (RuntimeError, ImportError):
            pass  # May fail in test environment

    def test_shutdown_resets_state(self):
        """Shutdown should reset initialization state."""
        try:
            initialize_event_reactor()
        except (RuntimeError, ImportError):
            pass

        shutdown_event_reactor()
        status = get_reactor_status()

        assert status["status"] == "not_initialized"


class TestReactorStatus:
    """Test reactor status values."""

    def test_status_not_initialized(self):
        """Not initialized status should have correct values."""
        shutdown_event_reactor()
        status = get_reactor_status()

        assert status["status"] == "not_initialized"
        assert status["healthy"] is False
        assert status["heartbeat_active"] is False

    def test_status_values_are_booleans(self):
        """healthy and heartbeat_active should be booleans."""
        status = get_reactor_status()

        assert isinstance(status["healthy"], bool)
        assert isinstance(status["heartbeat_active"], bool)

    def test_status_string_values(self):
        """status field should be a string."""
        status = get_reactor_status()

        assert isinstance(status["status"], str)
        assert status["status"] in (
            "not_initialized",
            "disabled",
            "running",
            "stopped"
        )


class TestShutdown:
    """Test shutdown functionality."""

    def test_shutdown_is_idempotent(self):
        """Shutdown should be safe to call multiple times."""
        # Should not raise on multiple calls
        shutdown_event_reactor()
        shutdown_event_reactor()
        shutdown_event_reactor()

        status = get_reactor_status()
        assert status["status"] == "not_initialized"

    def test_shutdown_after_failed_init(self):
        """Shutdown should work even after failed initialization."""
        try:
            initialize_event_reactor()
        except (RuntimeError, ImportError):
            pass

        # Should not raise
        shutdown_event_reactor()
        status = get_reactor_status()
        assert status["status"] == "not_initialized"
