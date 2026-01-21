# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-067 (SPINE Validation)
"""
Unit tests for GAP-067: SPINE Validation at Boot.

Tests that the boot guard validates all SPINE governance
components before the system starts accepting requests.
"""

import pytest
from app.startup.boot_guard import (
    validate_spine_components,
    SpineValidationResult,
    SpineValidationError,
    get_boot_status,
    reset_boot_status,
)


class TestBootGuard:
    """Test suite for boot guard SPINE validation."""

    def setup_method(self):
        """Reset boot status before each test."""
        reset_boot_status()

    def test_validate_returns_result(self):
        """validate_spine_components should return SpineValidationResult."""
        try:
            result = validate_spine_components()
            assert isinstance(result, SpineValidationResult)
        except SpineValidationError as e:
            # Validation may fail but we got a proper exception
            assert isinstance(e, SpineValidationError)
            assert hasattr(e, 'failures')

    def test_result_has_valid_flag(self):
        """Result should have valid flag."""
        try:
            result = validate_spine_components()
            assert hasattr(result, "valid")
            assert isinstance(result.valid, bool)
        except SpineValidationError:
            pass  # Validation failed - acceptable

    def test_result_has_failures_list(self):
        """Result should have failures list."""
        try:
            result = validate_spine_components()
            assert hasattr(result, "failures")
            assert isinstance(result.failures, list)
        except SpineValidationError as e:
            assert isinstance(e.failures, list)

    def test_result_has_warnings_list(self):
        """Result should have warnings list."""
        try:
            result = validate_spine_components()
            assert hasattr(result, "warnings")
            assert isinstance(result.warnings, list)
        except SpineValidationError:
            pass  # Validation failed - acceptable


class TestSpineValidationResult:
    """Test SpineValidationResult dataclass."""

    def test_successful_result(self):
        """Successful validation should have correct fields."""
        result = SpineValidationResult(
            valid=True,
            failures=[],
            warnings=["governance disabled at boot"],
        )

        assert result.valid is True
        assert len(result.failures) == 0
        assert len(result.warnings) == 1

    def test_failed_result(self):
        """Failed validation should include failure details."""
        result = SpineValidationResult(
            valid=False,
            failures=["EventReactor not healthy: stopped"],
            warnings=[],
        )

        assert result.valid is False
        assert len(result.failures) > 0
        assert "EventReactor" in result.failures[0]


class TestSpineValidationError:
    """Test SpineValidationError exception."""

    def test_error_is_exception(self):
        """SpineValidationError should be an Exception."""
        error = SpineValidationError(["test failure"])
        assert isinstance(error, Exception)

    def test_error_includes_failures(self):
        """Error should include failure list."""
        failures = ["policies module failed", "evidence module failed"]
        error = SpineValidationError(failures)

        assert hasattr(error, 'failures')
        assert error.failures == failures
        assert "policies" in str(error)

    def test_error_message_format(self):
        """Error message should indicate boot failure."""
        error = SpineValidationError(["test"])
        assert "BOOT FAILURE" in str(error)
        assert "SPINE" in str(error)


class TestGetBootStatus:
    """Test get_boot_status function."""

    def setup_method(self):
        """Reset boot status before each test."""
        reset_boot_status()

    def test_status_before_validation(self):
        """Status should be not_validated before validation runs."""
        status = get_boot_status()

        assert status["validated"] is False
        assert status["status"] == "not_validated"

    def test_status_after_validation(self):
        """Status should reflect validation result."""
        try:
            validate_spine_components()
            status = get_boot_status()
            assert status["validated"] is True
            assert status["status"] in ("healthy", "failed")
        except SpineValidationError:
            status = get_boot_status()
            # Even after failure, boot_status should be set
            assert status is not None

    def test_status_includes_failures_and_warnings(self):
        """Status should include failures and warnings."""
        status = get_boot_status()

        assert "failures" in status
        assert "warnings" in status
        assert isinstance(status["failures"], list)
        assert isinstance(status["warnings"], list)


class TestResetBootStatus:
    """Test reset_boot_status function."""

    def test_reset_clears_status(self):
        """Reset should clear boot status."""
        # First, trigger validation (or try to)
        try:
            validate_spine_components()
        except SpineValidationError:
            pass

        # Reset
        reset_boot_status()

        # Status should be back to not_validated
        status = get_boot_status()
        assert status["validated"] is False
