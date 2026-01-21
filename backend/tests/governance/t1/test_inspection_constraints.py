# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-033 (Inspection Constraints)
"""
Unit tests for GAP-033: Inspection Constraints.

Tests the inspection constraint enforcement service that checks
MonitorConfig flags before logging operations.

CRITICAL TEST COVERAGE:
- InspectionConstraintChecker imports and initializes
- Operations are correctly allowed/denied based on constraints
- Violations are correctly generated
- Helper functions work correctly
- Integration with MonitorConfig (from_monitor_config, from_snapshot)
"""

import pytest


class TestInspectionConstraintImports:
    """Test inspection constraint module imports."""

    def test_checker_import(self):
        """InspectionConstraintChecker should be importable."""
        from app.services.inspection import InspectionConstraintChecker

        assert InspectionConstraintChecker is not None

    def test_violation_import(self):
        """InspectionConstraintViolation should be importable."""
        from app.services.inspection import InspectionConstraintViolation

        assert InspectionConstraintViolation is not None

    def test_operation_import(self):
        """InspectionOperation should be importable."""
        from app.services.inspection import InspectionOperation

        assert InspectionOperation.LOG_PROMPT is not None

    def test_helper_imports(self):
        """Helper functions should be importable."""
        from app.services.inspection import (
            check_inspection_allowed,
            get_constraint_violations,
        )

        assert check_inspection_allowed is not None
        assert get_constraint_violations is not None


class TestInspectionOperation:
    """Test InspectionOperation enum."""

    def test_all_operations_defined(self):
        """All required operations should be defined."""
        from app.services.inspection import InspectionOperation

        assert InspectionOperation.LOG_PROMPT is not None
        assert InspectionOperation.LOG_RESPONSE is not None
        assert InspectionOperation.CAPTURE_PII is not None
        assert InspectionOperation.ACCESS_SECRET is not None

    def test_operation_values(self):
        """Operation values should be strings."""
        from app.services.inspection import InspectionOperation

        assert InspectionOperation.LOG_PROMPT.value == "log_prompt"
        assert InspectionOperation.LOG_RESPONSE.value == "log_response"
        assert InspectionOperation.CAPTURE_PII.value == "capture_pii"
        assert InspectionOperation.ACCESS_SECRET.value == "access_secret"


class TestInspectionConstraintChecker:
    """Test InspectionConstraintChecker class."""

    def test_default_all_denied(self):
        """Default checker should deny all operations."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker()

        assert not checker.is_allowed(InspectionOperation.LOG_PROMPT)
        assert not checker.is_allowed(InspectionOperation.LOG_RESPONSE)
        assert not checker.is_allowed(InspectionOperation.CAPTURE_PII)
        assert not checker.is_allowed(InspectionOperation.ACCESS_SECRET)

    def test_allow_prompt_logging(self):
        """Checker should allow prompt logging when enabled."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker(allow_prompt_logging=True)

        assert checker.is_allowed(InspectionOperation.LOG_PROMPT)
        assert not checker.is_allowed(InspectionOperation.LOG_RESPONSE)

    def test_allow_response_logging(self):
        """Checker should allow response logging when enabled."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker(allow_response_logging=True)

        assert not checker.is_allowed(InspectionOperation.LOG_PROMPT)
        assert checker.is_allowed(InspectionOperation.LOG_RESPONSE)

    def test_allow_pii_capture(self):
        """Checker should allow PII capture when enabled."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker(allow_pii_capture=True)

        assert checker.is_allowed(InspectionOperation.CAPTURE_PII)
        assert not checker.is_allowed(InspectionOperation.ACCESS_SECRET)

    def test_allow_secret_access(self):
        """Checker should allow secret access when enabled."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker(allow_secret_access=True)

        assert checker.is_allowed(InspectionOperation.ACCESS_SECRET)
        assert not checker.is_allowed(InspectionOperation.CAPTURE_PII)

    def test_allow_all(self):
        """Checker should allow all when all enabled."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker(
            allow_prompt_logging=True,
            allow_response_logging=True,
            allow_pii_capture=True,
            allow_secret_access=True,
        )

        for op in InspectionOperation:
            assert checker.is_allowed(op)

    def test_get_allowed_operations(self):
        """Should return list of allowed operations."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker(
            allow_prompt_logging=True,
            allow_pii_capture=True,
        )

        allowed = checker.get_allowed_operations()

        assert InspectionOperation.LOG_PROMPT in allowed
        assert InspectionOperation.CAPTURE_PII in allowed
        assert InspectionOperation.LOG_RESPONSE not in allowed
        assert InspectionOperation.ACCESS_SECRET not in allowed

    def test_get_denied_operations(self):
        """Should return list of denied operations."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker(
            allow_prompt_logging=True,
            allow_pii_capture=True,
        )

        denied = checker.get_denied_operations()

        assert InspectionOperation.LOG_RESPONSE in denied
        assert InspectionOperation.ACCESS_SECRET in denied
        assert InspectionOperation.LOG_PROMPT not in denied
        assert InspectionOperation.CAPTURE_PII not in denied


class TestInspectionConstraintViolation:
    """Test InspectionConstraintViolation."""

    def test_check_returns_violation_when_denied(self):
        """check() should return violation when operation denied."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker()  # All denied
        violation = checker.check(InspectionOperation.LOG_PROMPT)

        assert violation is not None
        assert violation.operation == InspectionOperation.LOG_PROMPT
        assert violation.constraint_field == "allow_prompt_logging"
        assert violation.constraint_value is False
        assert "not allowed" in violation.message

    def test_check_returns_none_when_allowed(self):
        """check() should return None when operation allowed."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker(allow_prompt_logging=True)
        violation = checker.check(InspectionOperation.LOG_PROMPT)

        assert violation is None

    def test_violation_to_dict(self):
        """Violation to_dict should return API-ready format."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker()
        violation = checker.check(InspectionOperation.LOG_RESPONSE)

        result = violation.to_dict()

        assert result["operation"] == "log_response"
        assert result["constraint_field"] == "allow_response_logging"
        assert result["constraint_value"] is False
        assert "message" in result

    def test_check_all_returns_all_violations(self):
        """check_all should return all violations."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker()  # All denied
        violations = checker.check_all(list(InspectionOperation))

        assert len(violations) == 4

    def test_check_all_returns_partial_violations(self):
        """check_all should return only violations for denied ops."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker(
            allow_prompt_logging=True,
            allow_response_logging=True,
        )
        violations = checker.check_all(list(InspectionOperation))

        assert len(violations) == 2
        ops = [v.operation for v in violations]
        assert InspectionOperation.CAPTURE_PII in ops
        assert InspectionOperation.ACCESS_SECRET in ops

    def test_check_all_returns_empty_when_all_allowed(self):
        """check_all should return empty when all allowed."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        checker = InspectionConstraintChecker(
            allow_prompt_logging=True,
            allow_response_logging=True,
            allow_pii_capture=True,
            allow_secret_access=True,
        )
        violations = checker.check_all(list(InspectionOperation))

        assert len(violations) == 0


class TestCheckerToDict:
    """Test checker to_dict method."""

    def test_to_dict_includes_all_fields(self):
        """to_dict should include all constraint fields."""
        from app.services.inspection import InspectionConstraintChecker

        checker = InspectionConstraintChecker(
            allow_prompt_logging=True,
            allow_response_logging=False,
            allow_pii_capture=True,
            allow_secret_access=False,
        )

        result = checker.to_dict()

        assert result["allow_prompt_logging"] is True
        assert result["allow_response_logging"] is False
        assert result["allow_pii_capture"] is True
        assert result["allow_secret_access"] is False
        assert "allowed_operations" in result
        assert "denied_operations" in result

    def test_to_dict_operations_lists(self):
        """to_dict should include correct operation lists."""
        from app.services.inspection import InspectionConstraintChecker

        checker = InspectionConstraintChecker(
            allow_prompt_logging=True,
            allow_pii_capture=True,
        )

        result = checker.to_dict()

        assert "log_prompt" in result["allowed_operations"]
        assert "capture_pii" in result["allowed_operations"]
        assert "log_response" in result["denied_operations"]
        assert "access_secret" in result["denied_operations"]


class TestCheckerFromMonitorConfig:
    """Test creating checker from MonitorConfig."""

    def test_from_monitor_config(self):
        """Should create checker from MonitorConfig instance."""
        from app.models.monitor_config import MonitorConfig
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        config = MonitorConfig(
            config_id="test-config",
            policy_id="test-policy",
            tenant_id="test-tenant",
            allow_prompt_logging=True,
            allow_response_logging=False,
            allow_pii_capture=True,
            allow_secret_access=False,
        )

        checker = InspectionConstraintChecker.from_monitor_config(config)

        assert checker.is_allowed(InspectionOperation.LOG_PROMPT)
        assert not checker.is_allowed(InspectionOperation.LOG_RESPONSE)
        assert checker.is_allowed(InspectionOperation.CAPTURE_PII)
        assert not checker.is_allowed(InspectionOperation.ACCESS_SECRET)

    def test_from_snapshot(self):
        """Should create checker from snapshot dict."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        snapshot = {
            "config_id": "test-config",
            "inspection_constraints": {
                "allow_prompt_logging": False,
                "allow_response_logging": True,
                "allow_pii_capture": False,
                "allow_secret_access": True,
            },
        }

        checker = InspectionConstraintChecker.from_snapshot(snapshot)

        assert not checker.is_allowed(InspectionOperation.LOG_PROMPT)
        assert checker.is_allowed(InspectionOperation.LOG_RESPONSE)
        assert not checker.is_allowed(InspectionOperation.CAPTURE_PII)
        assert checker.is_allowed(InspectionOperation.ACCESS_SECRET)

    def test_from_snapshot_missing_constraints(self):
        """Should handle snapshot without inspection_constraints."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        snapshot = {"config_id": "test-config"}

        checker = InspectionConstraintChecker.from_snapshot(snapshot)

        # All should be denied (defaults)
        assert not checker.is_allowed(InspectionOperation.LOG_PROMPT)
        assert not checker.is_allowed(InspectionOperation.LOG_RESPONSE)


class TestHelperFunctions:
    """Test helper functions."""

    def test_check_inspection_allowed_denied(self):
        """check_inspection_allowed should return False when denied."""
        from app.services.inspection import (
            InspectionOperation,
            check_inspection_allowed,
        )

        result = check_inspection_allowed(
            InspectionOperation.LOG_PROMPT,
            allow_prompt_logging=False,
        )

        assert result is False

    def test_check_inspection_allowed_allowed(self):
        """check_inspection_allowed should return True when allowed."""
        from app.services.inspection import (
            InspectionOperation,
            check_inspection_allowed,
        )

        result = check_inspection_allowed(
            InspectionOperation.LOG_PROMPT,
            allow_prompt_logging=True,
        )

        assert result is True

    def test_get_constraint_violations_all_denied(self):
        """get_constraint_violations should return all violations when denied."""
        from app.services.inspection import (
            InspectionOperation,
            get_constraint_violations,
        )

        violations = get_constraint_violations(
            [InspectionOperation.LOG_PROMPT, InspectionOperation.LOG_RESPONSE]
        )

        assert len(violations) == 2
        assert all(isinstance(v, dict) for v in violations)
        assert violations[0]["operation"] == "log_prompt"
        assert violations[1]["operation"] == "log_response"

    def test_get_constraint_violations_partial(self):
        """get_constraint_violations should return only violations."""
        from app.services.inspection import (
            InspectionOperation,
            get_constraint_violations,
        )

        violations = get_constraint_violations(
            [InspectionOperation.LOG_PROMPT, InspectionOperation.LOG_RESPONSE],
            allow_prompt_logging=True,  # This one allowed
        )

        assert len(violations) == 1
        assert violations[0]["operation"] == "log_response"

    def test_get_constraint_violations_none(self):
        """get_constraint_violations should return empty when all allowed."""
        from app.services.inspection import (
            InspectionOperation,
            get_constraint_violations,
        )

        violations = get_constraint_violations(
            [InspectionOperation.LOG_PROMPT, InspectionOperation.LOG_RESPONSE],
            allow_prompt_logging=True,
            allow_response_logging=True,
        )

        assert len(violations) == 0


class TestInspectionConstraintUseCases:
    """Test realistic use cases for inspection constraints."""

    def test_runner_pre_logging_check(self):
        """Simulate runner checking before logging."""
        from app.models.monitor_config import MonitorConfig
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        # Policy that allows prompt but not response logging
        config = MonitorConfig(
            config_id="runner-config",
            policy_id="pol-001",
            tenant_id="tenant-001",
            allow_prompt_logging=True,
            allow_response_logging=False,
        )

        checker = InspectionConstraintChecker.from_monitor_config(config)

        # Runner wants to log prompt - allowed
        assert checker.is_allowed(InspectionOperation.LOG_PROMPT)

        # Runner wants to log response - denied
        violation = checker.check(InspectionOperation.LOG_RESPONSE)
        assert violation is not None
        assert "not allowed" in violation.message

    def test_compliance_sensitive_policy(self):
        """Policy for compliance-sensitive workload (no PII, no secrets)."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        # Compliance-sensitive: allow logging but no PII/secrets
        checker = InspectionConstraintChecker(
            allow_prompt_logging=True,
            allow_response_logging=True,
            allow_pii_capture=False,
            allow_secret_access=False,
        )

        # Can log I/O
        assert checker.is_allowed(InspectionOperation.LOG_PROMPT)
        assert checker.is_allowed(InspectionOperation.LOG_RESPONSE)

        # Cannot capture sensitive data
        assert not checker.is_allowed(InspectionOperation.CAPTURE_PII)
        assert not checker.is_allowed(InspectionOperation.ACCESS_SECRET)

    def test_full_audit_policy(self):
        """Policy for full audit logging (all allowed)."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        # Full audit: allow everything
        checker = InspectionConstraintChecker(
            allow_prompt_logging=True,
            allow_response_logging=True,
            allow_pii_capture=True,
            allow_secret_access=True,
        )

        # All operations allowed
        for op in InspectionOperation:
            assert checker.is_allowed(op)

        # No violations
        violations = checker.check_all(list(InspectionOperation))
        assert len(violations) == 0

    def test_minimal_logging_policy(self):
        """Policy with minimal logging (all denied)."""
        from app.services.inspection import (
            InspectionConstraintChecker,
            InspectionOperation,
        )

        # Minimal: deny all inspection
        checker = InspectionConstraintChecker()

        # All operations denied
        for op in InspectionOperation:
            assert not checker.is_allowed(op)

        # All violations
        violations = checker.check_all(list(InspectionOperation))
        assert len(violations) == 4
