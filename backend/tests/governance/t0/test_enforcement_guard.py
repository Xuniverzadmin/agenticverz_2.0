# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-030 (Enforcement Guard)
"""
Unit tests for GAP-030: Enforcement Guard.

Tests that the enforcement guard context manager ensures
enforcement checks are never skipped.
"""

import pytest
from app.hoc.int.worker.enforcement.enforcement_guard import (
    enforcement_guard,
    EnforcementSkippedError,
)


class TestEnforcementGuard:
    """Test suite for enforcement guard."""

    def test_guard_requires_mark_enforcement_checked(self):
        """Guard should raise if mark_enforcement_checked() not called."""
        run_context = {"run_id": "test-run", "tenant_id": "test-tenant"}

        with pytest.raises(EnforcementSkippedError):
            with enforcement_guard(run_context, step_number=0) as guard:
                # Intentionally not calling guard.mark_enforcement_checked()
                pass

    def test_guard_succeeds_when_marked(self):
        """Guard should succeed when mark_enforcement_checked() is called."""
        run_context = {"run_id": "test-run", "tenant_id": "test-tenant"}

        # Should not raise
        with enforcement_guard(run_context, step_number=0) as guard:
            guard.mark_enforcement_checked()

    def test_guard_tracks_step_number(self):
        """Guard should track step number for logging."""
        run_context = {"run_id": "test-run", "tenant_id": "test-tenant"}

        with enforcement_guard(run_context, step_number=5) as guard:
            assert guard.step_number == 5
            guard.mark_enforcement_checked()

    def test_guard_error_includes_run_id(self):
        """EnforcementSkippedError should include run_id."""
        run_context = {"run_id": "run-123", "tenant_id": "tenant-456"}

        try:
            with enforcement_guard(run_context, step_number=0) as guard:
                pass
        except EnforcementSkippedError as e:
            assert "run-123" in str(e) or hasattr(e, "run_id")

    def test_guard_error_includes_step_number(self):
        """EnforcementSkippedError should include step number."""
        run_context = {"run_id": "test-run", "tenant_id": "test-tenant"}

        try:
            with enforcement_guard(run_context, step_number=7) as guard:
                pass
        except EnforcementSkippedError as e:
            assert "7" in str(e) or hasattr(e, "step_number")

    def test_guard_can_be_marked_multiple_times(self):
        """Multiple mark_enforcement_checked() calls should be safe."""
        run_context = {"run_id": "test-run", "tenant_id": "test-tenant"}

        with enforcement_guard(run_context, step_number=0) as guard:
            guard.mark_enforcement_checked()
            guard.mark_enforcement_checked()  # Second call should be safe

    def test_guard_propagates_exceptions(self):
        """Guard should propagate exceptions from inner code."""
        run_context = {"run_id": "test-run", "tenant_id": "test-tenant"}

        with pytest.raises(ValueError, match="Test error"):
            with enforcement_guard(run_context, step_number=0) as guard:
                guard.mark_enforcement_checked()
                raise ValueError("Test error")

    def test_guard_still_checks_after_exception(self):
        """Guard should still check enforcement after exception."""
        run_context = {"run_id": "test-run", "tenant_id": "test-tenant"}

        # Exception without marking should raise EnforcementSkippedError
        with pytest.raises(EnforcementSkippedError):
            with enforcement_guard(run_context, step_number=0) as guard:
                raise RuntimeError("Inner error")


class TestEnforcementSkippedError:
    """Test EnforcementSkippedError exception."""

    def test_error_is_exception(self):
        """EnforcementSkippedError should be an Exception."""
        error = EnforcementSkippedError(step_number=5, run_id="test-run")
        assert isinstance(error, Exception)

    def test_error_message_format(self):
        """Error message should include run_id and step."""
        error = EnforcementSkippedError(step_number=5, run_id="run-123")
        message = str(error)

        assert "run-123" in message
        assert "5" in message
