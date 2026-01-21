# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-050 (RAC Durability Enforcement)
"""
Unit tests for GAP-050: RAC Durability Enforcement.

Tests the RAC durability enforcement service that checks
the rac_durability_enforce flag before operations.

CRITICAL TEST COVERAGE:
- RACDurabilityChecker imports and initializes
- Durability status correctly determined
- Enforcement raises error when enabled and not durable
- Helper functions work correctly
- Integration with AuditStore
"""

import pytest


class TestRACDurabilityImports:
    """Test RAC durability module imports."""

    def test_checker_import(self):
        """RACDurabilityChecker should be importable."""
        from app.services.audit.durability import RACDurabilityChecker

        assert RACDurabilityChecker is not None

    def test_error_import(self):
        """RACDurabilityEnforcementError should be importable."""
        from app.services.audit.durability import RACDurabilityEnforcementError

        assert RACDurabilityEnforcementError is not None

    def test_result_enum_import(self):
        """DurabilityCheckResult should be importable."""
        from app.services.audit.durability import DurabilityCheckResult

        assert DurabilityCheckResult.DURABLE is not None

    def test_response_import(self):
        """DurabilityCheckResponse should be importable."""
        from app.services.audit.durability import DurabilityCheckResponse

        assert DurabilityCheckResponse is not None

    def test_helper_imports(self):
        """Helper functions should be importable."""
        from app.services.audit.durability import (
            check_rac_durability,
            ensure_rac_durability,
        )

        assert check_rac_durability is not None
        assert ensure_rac_durability is not None


class TestDurabilityCheckResult:
    """Test DurabilityCheckResult enum."""

    def test_all_results_defined(self):
        """All required results should be defined."""
        from app.services.audit.durability import DurabilityCheckResult

        assert DurabilityCheckResult.DURABLE is not None
        assert DurabilityCheckResult.NOT_DURABLE is not None
        assert DurabilityCheckResult.ENFORCEMENT_DISABLED is not None
        assert DurabilityCheckResult.UNKNOWN is not None

    def test_result_values(self):
        """Result values should be strings."""
        from app.services.audit.durability import DurabilityCheckResult

        assert DurabilityCheckResult.DURABLE.value == "durable"
        assert DurabilityCheckResult.NOT_DURABLE.value == "not_durable"
        assert DurabilityCheckResult.ENFORCEMENT_DISABLED.value == "enforcement_disabled"


class TestDurabilityCheckResponse:
    """Test DurabilityCheckResponse dataclass."""

    def test_response_creation(self):
        """Should create response with all fields."""
        from app.services.audit.durability import (
            DurabilityCheckResponse,
            DurabilityCheckResult,
        )

        response = DurabilityCheckResponse(
            result=DurabilityCheckResult.DURABLE,
            is_durable=True,
            enforcement_enabled=True,
            durability_mode="REDIS",
            message="Test message",
        )

        assert response.result == DurabilityCheckResult.DURABLE
        assert response.is_durable is True
        assert response.enforcement_enabled is True
        assert response.durability_mode == "REDIS"
        assert response.message == "Test message"

    def test_response_to_dict(self):
        """to_dict should return API-ready format."""
        from app.services.audit.durability import (
            DurabilityCheckResponse,
            DurabilityCheckResult,
        )

        response = DurabilityCheckResponse(
            result=DurabilityCheckResult.DURABLE,
            is_durable=True,
            enforcement_enabled=True,
            durability_mode="REDIS",
            message="Test",
        )

        d = response.to_dict()

        assert d["result"] == "durable"
        assert d["is_durable"] is True
        assert d["enforcement_enabled"] is True
        assert d["durability_mode"] == "REDIS"


class TestRACDurabilityEnforcementError:
    """Test RACDurabilityEnforcementError exception."""

    def test_error_creation(self):
        """Should create error with all fields."""
        from app.services.audit.durability import RACDurabilityEnforcementError

        error = RACDurabilityEnforcementError(
            message="Test error",
            operation="add_ack",
            durability_mode="MEMORY",
            enforcement_enabled=True,
        )

        assert str(error) == "Test error"
        assert error.operation == "add_ack"
        assert error.durability_mode == "MEMORY"
        assert error.enforcement_enabled is True

    def test_error_to_dict(self):
        """to_dict should return structured error info."""
        from app.services.audit.durability import RACDurabilityEnforcementError

        error = RACDurabilityEnforcementError(
            message="Test error",
            operation="add_expectations",
            durability_mode="MEMORY",
            enforcement_enabled=True,
        )

        d = error.to_dict()

        assert d["error"] == "RACDurabilityEnforcementError"
        assert d["message"] == "Test error"
        assert d["operation"] == "add_expectations"
        assert d["durability_mode"] == "MEMORY"


class TestRACDurabilityChecker:
    """Test RACDurabilityChecker class."""

    def test_default_not_durable(self):
        """Default checker should be in MEMORY mode (not durable)."""
        from app.services.audit.durability import RACDurabilityChecker

        checker = RACDurabilityChecker()

        assert not checker.is_durable
        assert checker.enforcement_enabled

    def test_redis_mode_is_durable(self):
        """REDIS mode should be durable."""
        from app.services.audit.durability import RACDurabilityChecker

        checker = RACDurabilityChecker(
            enforcement_enabled=True,
            durability_mode="REDIS",
        )

        assert checker.is_durable

    def test_memory_mode_not_durable(self):
        """MEMORY mode should not be durable."""
        from app.services.audit.durability import RACDurabilityChecker

        checker = RACDurabilityChecker(
            enforcement_enabled=True,
            durability_mode="MEMORY",
        )

        assert not checker.is_durable

    def test_check_durable_returns_durable(self):
        """check() should return DURABLE when Redis mode."""
        from app.services.audit.durability import (
            DurabilityCheckResult,
            RACDurabilityChecker,
        )

        checker = RACDurabilityChecker(
            enforcement_enabled=True,
            durability_mode="REDIS",
        )

        response = checker.check()

        assert response.result == DurabilityCheckResult.DURABLE
        assert response.is_durable is True

    def test_check_not_durable_returns_not_durable(self):
        """check() should return NOT_DURABLE when Memory mode."""
        from app.services.audit.durability import (
            DurabilityCheckResult,
            RACDurabilityChecker,
        )

        checker = RACDurabilityChecker(
            enforcement_enabled=True,
            durability_mode="MEMORY",
        )

        response = checker.check()

        assert response.result == DurabilityCheckResult.NOT_DURABLE
        assert response.is_durable is False

    def test_check_enforcement_disabled(self):
        """check() should return ENFORCEMENT_DISABLED when disabled."""
        from app.services.audit.durability import (
            DurabilityCheckResult,
            RACDurabilityChecker,
        )

        checker = RACDurabilityChecker(
            enforcement_enabled=False,
            durability_mode="MEMORY",
        )

        response = checker.check()

        assert response.result == DurabilityCheckResult.ENFORCEMENT_DISABLED
        assert response.enforcement_enabled is False


class TestRACDurabilityCheckerEnsure:
    """Test ensure_durable method."""

    def test_ensure_durable_passes_when_durable(self):
        """ensure_durable should pass when storage is durable."""
        from app.services.audit.durability import RACDurabilityChecker

        checker = RACDurabilityChecker(
            enforcement_enabled=True,
            durability_mode="REDIS",
        )

        # Should not raise
        checker.ensure_durable("add_ack")

    def test_ensure_durable_raises_when_not_durable(self):
        """ensure_durable should raise when not durable and enforced."""
        from app.services.audit.durability import (
            RACDurabilityChecker,
            RACDurabilityEnforcementError,
        )

        checker = RACDurabilityChecker(
            enforcement_enabled=True,
            durability_mode="MEMORY",
        )

        with pytest.raises(RACDurabilityEnforcementError) as exc_info:
            checker.ensure_durable("add_ack")

        assert exc_info.value.operation == "add_ack"
        assert exc_info.value.durability_mode == "MEMORY"

    def test_ensure_durable_passes_when_enforcement_disabled(self):
        """ensure_durable should pass when enforcement disabled."""
        from app.services.audit.durability import RACDurabilityChecker

        checker = RACDurabilityChecker(
            enforcement_enabled=False,
            durability_mode="MEMORY",
        )

        # Should not raise even though not durable
        checker.ensure_durable("add_ack")


class TestRACDurabilityCheckerShouldAllow:
    """Test should_allow_operation method."""

    def test_should_allow_when_durable(self):
        """should_allow_operation should return True when durable."""
        from app.services.audit.durability import RACDurabilityChecker

        checker = RACDurabilityChecker(
            enforcement_enabled=True,
            durability_mode="REDIS",
        )

        allowed, reason = checker.should_allow_operation("add_ack")

        assert allowed is True
        assert "durable" in reason.lower()

    def test_should_allow_when_enforcement_disabled(self):
        """should_allow_operation should return True when enforcement disabled."""
        from app.services.audit.durability import RACDurabilityChecker

        checker = RACDurabilityChecker(
            enforcement_enabled=False,
            durability_mode="MEMORY",
        )

        allowed, reason = checker.should_allow_operation("add_ack")

        assert allowed is True
        assert "disabled" in reason.lower()

    def test_should_not_allow_when_not_durable_and_enforced(self):
        """should_allow_operation should return False when not durable."""
        from app.services.audit.durability import RACDurabilityChecker

        checker = RACDurabilityChecker(
            enforcement_enabled=True,
            durability_mode="MEMORY",
        )

        allowed, reason = checker.should_allow_operation("add_ack")

        assert allowed is False
        assert "blocked" in reason.lower()


class TestRACDurabilityCheckerFromStore:
    """Test creating checker from AuditStore."""

    def test_from_audit_store_memory(self):
        """Should detect MEMORY mode from store."""
        from app.services.audit.durability import RACDurabilityChecker

        # Mock store with MEMORY mode
        class MockStore:
            class Mode:
                value = "MEMORY"
            durability_mode = Mode()

        checker = RACDurabilityChecker.from_audit_store(
            MockStore(),
            enforcement_enabled=True,
        )

        assert checker._durability_mode == "MEMORY"

    def test_from_audit_store_redis(self):
        """Should detect REDIS mode from store."""
        from app.services.audit.durability import RACDurabilityChecker

        # Mock store with REDIS mode
        class MockStore:
            class Mode:
                value = "REDIS"
            durability_mode = Mode()

        checker = RACDurabilityChecker.from_audit_store(
            MockStore(),
            enforcement_enabled=True,
        )

        assert checker._durability_mode == "REDIS"

    def test_from_audit_store_none(self):
        """Should handle None store."""
        from app.services.audit.durability import RACDurabilityChecker

        checker = RACDurabilityChecker.from_audit_store(
            None,
            enforcement_enabled=True,
        )

        assert checker._durability_mode == "MEMORY"


class TestHelperFunctions:
    """Test helper functions."""

    def test_check_rac_durability_durable(self):
        """check_rac_durability should return DURABLE for Redis."""
        from app.services.audit.durability import (
            DurabilityCheckResult,
            check_rac_durability,
        )

        response = check_rac_durability(
            enforcement_enabled=True,
            durability_mode="REDIS",
        )

        assert response.result == DurabilityCheckResult.DURABLE

    def test_check_rac_durability_not_durable(self):
        """check_rac_durability should return NOT_DURABLE for Memory."""
        from app.services.audit.durability import (
            DurabilityCheckResult,
            check_rac_durability,
        )

        response = check_rac_durability(
            enforcement_enabled=True,
            durability_mode="MEMORY",
        )

        assert response.result == DurabilityCheckResult.NOT_DURABLE

    def test_ensure_rac_durability_passes(self):
        """ensure_rac_durability should pass when durable."""
        from app.services.audit.durability import ensure_rac_durability

        # Should not raise
        ensure_rac_durability(
            operation="test",
            enforcement_enabled=True,
            durability_mode="REDIS",
        )

    def test_ensure_rac_durability_raises(self):
        """ensure_rac_durability should raise when not durable."""
        from app.services.audit.durability import (
            RACDurabilityEnforcementError,
            ensure_rac_durability,
        )

        with pytest.raises(RACDurabilityEnforcementError):
            ensure_rac_durability(
                operation="test",
                enforcement_enabled=True,
                durability_mode="MEMORY",
            )


class TestRACDurabilityUseCases:
    """Test realistic use cases for RAC durability."""

    def test_production_enforcement(self):
        """Production with enforcement enabled requires Redis."""
        from app.services.audit.durability import (
            RACDurabilityChecker,
            RACDurabilityEnforcementError,
        )

        # Production-like config: enforcement enabled
        checker = RACDurabilityChecker(
            enforcement_enabled=True,
            durability_mode="MEMORY",  # But only memory available
        )

        # Should block operations
        with pytest.raises(RACDurabilityEnforcementError) as exc_info:
            checker.ensure_durable("add_expectations")

        assert "not durable" in str(exc_info.value).lower()

    def test_production_with_redis(self):
        """Production with Redis should allow operations."""
        from app.services.audit.durability import RACDurabilityChecker

        # Production-like config: enforcement enabled, Redis available
        checker = RACDurabilityChecker(
            enforcement_enabled=True,
            durability_mode="REDIS",
        )

        # All operations should pass
        checker.ensure_durable("add_expectations")
        checker.ensure_durable("add_ack")
        checker.ensure_durable("reconcile")

    def test_development_mode(self):
        """Development mode with enforcement disabled allows memory."""
        from app.services.audit.durability import RACDurabilityChecker

        # Dev-like config: enforcement disabled
        checker = RACDurabilityChecker(
            enforcement_enabled=False,
            durability_mode="MEMORY",
        )

        # All operations should pass (no enforcement)
        checker.ensure_durable("add_expectations")
        checker.ensure_durable("add_ack")

    def test_graceful_degradation_check(self):
        """Check allows graceful degradation when enforcement disabled."""
        from app.services.audit.durability import (
            DurabilityCheckResult,
            RACDurabilityChecker,
        )

        checker = RACDurabilityChecker(
            enforcement_enabled=False,
            durability_mode="MEMORY",
        )

        response = checker.check()

        # Returns enforcement disabled status
        assert response.result == DurabilityCheckResult.ENFORCEMENT_DISABLED
        # But still reports actual durability state
        assert response.is_durable is False
        # Message explains situation
        assert "disabled" in response.message.lower()

    def test_worker_before_ack(self):
        """Simulate worker checking durability before ack."""
        from app.services.audit.durability import RACDurabilityChecker

        # Config from governance profile
        class MockGovernanceConfig:
            rac_durability_enforce = True

        # Store with Redis
        class MockStore:
            class Mode:
                value = "REDIS"
            durability_mode = Mode()

        # Worker creates checker from config and store
        config = MockGovernanceConfig()
        checker = RACDurabilityChecker.from_audit_store(
            MockStore(),
            enforcement_enabled=config.rac_durability_enforce,
        )

        # Before adding ack
        allowed, reason = checker.should_allow_operation("add_ack")

        assert allowed is True
        # Proceed to add ack...
