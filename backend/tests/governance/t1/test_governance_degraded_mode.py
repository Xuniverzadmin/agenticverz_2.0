# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-070 (Governance Degraded Mode)
"""
Unit tests for GAP-070: Governance Degraded Mode.

Tests the governance degraded mode checker service that manages
degraded state with incident response integration.

CRITICAL TEST COVERAGE:
- GovernanceDegradedModeChecker imports and initializes
- Degraded mode state correctly determined
- Enforcement raises error when degraded
- Incident creation for degraded transitions
- Helper functions work correctly
"""

import pytest


class TestGovernanceDegradedModeImports:
    """Test governance degraded mode module imports."""

    def test_checker_import(self):
        """GovernanceDegradedModeChecker should be importable."""
        from app.services.governance.degraded import GovernanceDegradedModeChecker

        assert GovernanceDegradedModeChecker is not None

    def test_error_import(self):
        """GovernanceDegradedModeError should be importable."""
        from app.services.governance.degraded import GovernanceDegradedModeError

        assert GovernanceDegradedModeError is not None

    def test_result_enum_import(self):
        """DegradedModeCheckResult should be importable."""
        from app.services.governance.degraded import DegradedModeCheckResult

        assert DegradedModeCheckResult.NORMAL is not None

    def test_state_enum_import(self):
        """DegradedModeState should be importable."""
        from app.services.governance.degraded import DegradedModeState

        assert DegradedModeState.NORMAL is not None
        assert DegradedModeState.DEGRADED is not None
        assert DegradedModeState.CRITICAL is not None

    def test_response_import(self):
        """DegradedModeCheckResponse should be importable."""
        from app.services.governance.degraded import DegradedModeCheckResponse

        assert DegradedModeCheckResponse is not None

    def test_incident_creator_import(self):
        """DegradedModeIncidentCreator should be importable."""
        from app.services.governance.degraded import DegradedModeIncidentCreator

        assert DegradedModeIncidentCreator is not None

    def test_helper_imports(self):
        """Helper functions should be importable."""
        from app.services.governance.degraded import (
            check_degraded_mode,
            enter_degraded_with_incident,
            ensure_not_degraded,
        )

        assert check_degraded_mode is not None
        assert enter_degraded_with_incident is not None
        assert ensure_not_degraded is not None


class TestDegradedModeCheckResult:
    """Test DegradedModeCheckResult enum."""

    def test_all_results_defined(self):
        """All required results should be defined."""
        from app.services.governance.degraded import DegradedModeCheckResult

        assert DegradedModeCheckResult.NORMAL is not None
        assert DegradedModeCheckResult.DEGRADED is not None
        assert DegradedModeCheckResult.CRITICAL is not None
        assert DegradedModeCheckResult.CHECK_DISABLED is not None

    def test_result_values(self):
        """Result values should be strings."""
        from app.services.governance.degraded import DegradedModeCheckResult

        assert DegradedModeCheckResult.NORMAL.value == "normal"
        assert DegradedModeCheckResult.DEGRADED.value == "degraded"
        assert DegradedModeCheckResult.CRITICAL.value == "critical"


class TestDegradedModeState:
    """Test DegradedModeState enum."""

    def test_all_states_defined(self):
        """All required states should be defined."""
        from app.services.governance.degraded import DegradedModeState

        assert DegradedModeState.NORMAL is not None
        assert DegradedModeState.DEGRADED is not None
        assert DegradedModeState.CRITICAL is not None

    def test_state_values(self):
        """State values should be strings."""
        from app.services.governance.degraded import DegradedModeState

        assert DegradedModeState.NORMAL.value == "NORMAL"
        assert DegradedModeState.DEGRADED.value == "DEGRADED"
        assert DegradedModeState.CRITICAL.value == "CRITICAL"


class TestGovernanceDegradedModeChecker:
    """Test GovernanceDegradedModeChecker class."""

    def setup_method(self):
        """Reset state before each test."""
        from app.services.governance.degraded.degraded_mode_checker import (
            _reset_degraded_mode_state,
        )

        _reset_degraded_mode_state()

    def test_default_check_enabled(self):
        """Default checker should have check enabled."""
        from app.services.governance.degraded import GovernanceDegradedModeChecker

        checker = GovernanceDegradedModeChecker()

        assert checker.check_enabled

    def test_check_can_be_disabled(self):
        """Checker can be created with check disabled."""
        from app.services.governance.degraded import GovernanceDegradedModeChecker

        checker = GovernanceDegradedModeChecker(check_enabled=False)

        assert not checker.check_enabled

    def test_check_returns_normal_initially(self):
        """Check should return NORMAL when governance is operational."""
        from app.services.governance.degraded import (
            DegradedModeCheckResult,
            GovernanceDegradedModeChecker,
        )

        checker = GovernanceDegradedModeChecker()
        response = checker.check()

        assert response.result == DegradedModeCheckResult.NORMAL
        assert response.is_degraded is False
        assert response.state.value == "NORMAL"

    def test_check_disabled_returns_disabled(self):
        """Check should return CHECK_DISABLED when disabled."""
        from app.services.governance.degraded import (
            DegradedModeCheckResult,
            GovernanceDegradedModeChecker,
        )

        checker = GovernanceDegradedModeChecker(check_enabled=False)
        response = checker.check()

        assert response.result == DegradedModeCheckResult.CHECK_DISABLED
        assert response.check_enabled is False


class TestGovernanceDegradedModeCheckerEnterExit:
    """Test enter and exit degraded mode."""

    def setup_method(self):
        """Reset state before each test."""
        from app.services.governance.degraded.degraded_mode_checker import (
            _reset_degraded_mode_state,
        )

        _reset_degraded_mode_state()

    def test_enter_degraded_mode(self):
        """enter_degraded should transition to degraded state."""
        from app.services.governance.degraded import (
            DegradedModeState,
            GovernanceDegradedModeChecker,
        )

        checker = GovernanceDegradedModeChecker()

        status = checker.enter_degraded(
            state=DegradedModeState.DEGRADED,
            reason="Database connection pool exhausted",
            entered_by="health_monitor",
            create_incident=False,
        )

        assert status.state == DegradedModeState.DEGRADED
        assert status.reason == "Database connection pool exhausted"
        assert status.entered_by == "health_monitor"

    def test_enter_degraded_check_returns_degraded(self):
        """Check should return DEGRADED after entering degraded mode."""
        from app.services.governance.degraded import (
            DegradedModeCheckResult,
            DegradedModeState,
            GovernanceDegradedModeChecker,
        )

        checker = GovernanceDegradedModeChecker()

        checker.enter_degraded(
            state=DegradedModeState.DEGRADED,
            reason="Test reason",
            entered_by="test",
            create_incident=False,
        )

        response = checker.check()

        assert response.result == DegradedModeCheckResult.DEGRADED
        assert response.is_degraded is True
        assert response.degraded_reason == "Test reason"

    def test_enter_critical_mode(self):
        """enter_degraded should transition to critical state."""
        from app.services.governance.degraded import (
            DegradedModeCheckResult,
            DegradedModeState,
            GovernanceDegradedModeChecker,
        )

        checker = GovernanceDegradedModeChecker()

        checker.enter_degraded(
            state=DegradedModeState.CRITICAL,
            reason="Full system failure",
            entered_by="system",
            create_incident=False,
        )

        response = checker.check()

        assert response.result == DegradedModeCheckResult.CRITICAL
        assert response.is_degraded is True

    def test_exit_degraded_mode(self):
        """exit_degraded should restore normal state."""
        from app.services.governance.degraded import (
            DegradedModeCheckResult,
            DegradedModeState,
            GovernanceDegradedModeChecker,
        )

        checker = GovernanceDegradedModeChecker()

        # Enter degraded mode
        checker.enter_degraded(
            state=DegradedModeState.DEGRADED,
            reason="Test",
            entered_by="test",
            create_incident=False,
        )

        # Exit degraded mode
        checker.exit_degraded(exited_by="operator", create_incident=False)

        # Check state is normal
        response = checker.check()

        assert response.result == DegradedModeCheckResult.NORMAL
        assert response.is_degraded is False


class TestGovernanceDegradedModeCheckerEnsure:
    """Test ensure_not_degraded method."""

    def setup_method(self):
        """Reset state before each test."""
        from app.services.governance.degraded.degraded_mode_checker import (
            _reset_degraded_mode_state,
        )

        _reset_degraded_mode_state()

    def test_ensure_passes_when_normal(self):
        """ensure_not_degraded should pass when governance is normal."""
        from app.services.governance.degraded import GovernanceDegradedModeChecker

        checker = GovernanceDegradedModeChecker()

        # Should not raise
        checker.ensure_not_degraded("start_new_run")

    def test_ensure_raises_when_critical(self):
        """ensure_not_degraded should raise when critical."""
        from app.services.governance.degraded import (
            DegradedModeState,
            GovernanceDegradedModeChecker,
            GovernanceDegradedModeError,
        )

        checker = GovernanceDegradedModeChecker()

        checker.enter_degraded(
            state=DegradedModeState.CRITICAL,
            reason="Full failure",
            entered_by="test",
            create_incident=False,
        )

        with pytest.raises(GovernanceDegradedModeError) as exc_info:
            checker.ensure_not_degraded("start_new_run")

        assert exc_info.value.state == DegradedModeState.CRITICAL
        assert exc_info.value.operation == "start_new_run"

    def test_ensure_raises_when_degraded_and_blocking(self):
        """ensure_not_degraded should raise when degraded and new runs blocked."""
        from app.services.governance.degraded import (
            DegradedModeState,
            GovernanceDegradedModeChecker,
            GovernanceDegradedModeError,
        )

        checker = GovernanceDegradedModeChecker()

        checker.enter_degraded(
            state=DegradedModeState.DEGRADED,
            reason="Degraded",
            entered_by="test",
            new_runs_action="BLOCK",
            create_incident=False,
        )

        with pytest.raises(GovernanceDegradedModeError):
            checker.ensure_not_degraded("start_new_run")

    def test_ensure_passes_when_degraded_and_allowing(self):
        """ensure_not_degraded should pass when degraded but allowing new runs."""
        from app.services.governance.degraded import (
            DegradedModeState,
            GovernanceDegradedModeChecker,
        )

        checker = GovernanceDegradedModeChecker()

        checker.enter_degraded(
            state=DegradedModeState.DEGRADED,
            reason="Degraded but allowing",
            entered_by="test",
            new_runs_action="ALLOW",
            create_incident=False,
        )

        # Should not raise
        checker.ensure_not_degraded("start_new_run")


class TestGovernanceDegradedModeError:
    """Test GovernanceDegradedModeError exception."""

    def test_error_creation(self):
        """Should create error with all fields."""
        from app.services.governance.degraded import (
            DegradedModeState,
            GovernanceDegradedModeError,
        )

        error = GovernanceDegradedModeError(
            message="Test error",
            state=DegradedModeState.CRITICAL,
            operation="start_run",
            degraded_since="2024-01-01T00:00:00Z",
            degraded_reason="Database failure",
        )

        assert str(error) == "Test error"
        assert error.state == DegradedModeState.CRITICAL
        assert error.operation == "start_run"

    def test_error_to_dict(self):
        """to_dict should return structured error info."""
        from app.services.governance.degraded import (
            DegradedModeState,
            GovernanceDegradedModeError,
        )

        error = GovernanceDegradedModeError(
            message="Test error",
            state=DegradedModeState.DEGRADED,
            operation="test_op",
            degraded_since="2024-01-01T00:00:00Z",
            degraded_reason="Test reason",
        )

        d = error.to_dict()

        assert d["error"] == "GovernanceDegradedModeError"
        assert d["state"] == "DEGRADED"
        assert d["operation"] == "test_op"


class TestDegradedModeCheckResponse:
    """Test DegradedModeCheckResponse dataclass."""

    def test_response_creation(self):
        """Should create response with all fields."""
        from app.services.governance.degraded import (
            DegradedModeCheckResponse,
            DegradedModeCheckResult,
            DegradedModeState,
        )

        response = DegradedModeCheckResponse(
            result=DegradedModeCheckResult.NORMAL,
            is_degraded=False,
            check_enabled=True,
            state=DegradedModeState.NORMAL,
            new_runs_action="ALLOW",
            existing_runs_action="ALLOW",
            message="Test",
        )

        assert response.result == DegradedModeCheckResult.NORMAL
        assert response.is_degraded is False

    def test_response_to_dict(self):
        """to_dict should return API-ready format."""
        from app.services.governance.degraded import (
            DegradedModeCheckResponse,
            DegradedModeCheckResult,
            DegradedModeState,
        )

        response = DegradedModeCheckResponse(
            result=DegradedModeCheckResult.DEGRADED,
            is_degraded=True,
            check_enabled=True,
            state=DegradedModeState.DEGRADED,
            new_runs_action="BLOCK",
            existing_runs_action="WARN",
            message="Degraded",
            degraded_reason="Test reason",
        )

        d = response.to_dict()

        assert d["result"] == "degraded"
        assert d["is_degraded"] is True
        assert d["state"] == "DEGRADED"


class TestDegradedModeIncidentCreator:
    """Test DegradedModeIncidentCreator class."""

    def test_creator_import(self):
        """DegradedModeIncidentCreator should be importable."""
        from app.services.governance.degraded import DegradedModeIncidentCreator

        creator = DegradedModeIncidentCreator()
        assert creator is not None

    def test_create_degraded_incident(self):
        """Should create incident for degraded mode transition."""
        from app.services.governance.degraded import (
            DegradedModeIncidentCreator,
            DegradedModeState,
        )

        creator = DegradedModeIncidentCreator(tenant_id="test-tenant")

        incident = creator.create_degraded_incident(
            state=DegradedModeState.DEGRADED,
            reason="Database connection failed",
            entered_by="health_monitor",
        )

        assert incident.incident_id is not None
        assert incident.tenant_id == "test-tenant"
        assert "DEGRADED" in incident.title
        assert incident.severity == "MEDIUM"

    def test_create_critical_incident(self):
        """Critical state should create HIGH severity incident."""
        from app.services.governance.degraded import (
            DegradedModeIncidentCreator,
            DegradedModeState,
        )

        creator = DegradedModeIncidentCreator()

        incident = creator.create_degraded_incident(
            state=DegradedModeState.CRITICAL,
            reason="Full system failure",
            entered_by="system",
        )

        assert incident.severity == "HIGH"

    def test_create_recovery_incident(self):
        """Should create incident for recovery from degraded mode."""
        from app.services.governance.degraded import (
            DegradedModeIncidentCreator,
            DegradedModeState,
        )

        creator = DegradedModeIncidentCreator()

        incident = creator.create_recovery_incident(
            previous_state=DegradedModeState.DEGRADED,
            recovered_by="operator",
            duration_seconds=300,
        )

        assert incident.incident_id is not None
        assert "Recovered" in incident.title
        assert incident.severity == "LOW"


class TestShouldAllowNewRun:
    """Test should_allow_new_run method."""

    def setup_method(self):
        """Reset state before each test."""
        from app.services.governance.degraded.degraded_mode_checker import (
            _reset_degraded_mode_state,
        )

        _reset_degraded_mode_state()

    def test_allow_when_normal(self):
        """should_allow_new_run should return True when normal."""
        from app.services.governance.degraded import GovernanceDegradedModeChecker

        checker = GovernanceDegradedModeChecker()

        allowed, reason = checker.should_allow_new_run("run-123")

        assert allowed is True
        assert "operational" in reason.lower()

    def test_block_when_degraded_and_blocking(self):
        """should_allow_new_run should return False when blocking."""
        from app.services.governance.degraded import (
            DegradedModeState,
            GovernanceDegradedModeChecker,
        )

        checker = GovernanceDegradedModeChecker()

        checker.enter_degraded(
            state=DegradedModeState.DEGRADED,
            reason="Test",
            entered_by="test",
            new_runs_action="BLOCK",
            create_incident=False,
        )

        allowed, reason = checker.should_allow_new_run("run-123")

        assert allowed is False
        assert "blocked" in reason.lower()

    def test_allow_with_warning_when_warn_action(self):
        """should_allow_new_run should return True with warning."""
        from app.services.governance.degraded import (
            DegradedModeState,
            GovernanceDegradedModeChecker,
        )

        checker = GovernanceDegradedModeChecker()

        checker.enter_degraded(
            state=DegradedModeState.DEGRADED,
            reason="Test",
            entered_by="test",
            new_runs_action="WARN",
            create_incident=False,
        )

        allowed, reason = checker.should_allow_new_run("run-123")

        assert allowed is True
        assert "warning" in reason.lower()


class TestHelperFunctions:
    """Test helper functions."""

    def setup_method(self):
        """Reset state before each test."""
        from app.services.governance.degraded.degraded_mode_checker import (
            _reset_degraded_mode_state,
        )

        _reset_degraded_mode_state()

    def test_check_degraded_mode_normal(self):
        """check_degraded_mode should return NORMAL initially."""
        from app.services.governance.degraded import (
            DegradedModeCheckResult,
            check_degraded_mode,
        )

        response = check_degraded_mode(check_enabled=True)

        assert response.result == DegradedModeCheckResult.NORMAL
        assert response.is_degraded is False

    def test_ensure_not_degraded_passes(self):
        """ensure_not_degraded should pass when normal."""
        from app.services.governance.degraded import ensure_not_degraded

        # Should not raise
        ensure_not_degraded(operation="test", check_enabled=True)

    def test_enter_degraded_with_incident(self):
        """enter_degraded_with_incident should enter degraded mode."""
        from app.services.governance.degraded import (
            DegradedModeState,
            check_degraded_mode,
            enter_degraded_with_incident,
        )

        status = enter_degraded_with_incident(
            state=DegradedModeState.DEGRADED,
            reason="Test reason",
            entered_by="test",
        )

        assert status.state == DegradedModeState.DEGRADED
        assert status.incident_id is not None

        response = check_degraded_mode()
        assert response.is_degraded is True


class TestGovernanceDegradedModeUseCases:
    """Test realistic use cases for governance degraded mode."""

    def setup_method(self):
        """Reset state before each test."""
        from app.services.governance.degraded.degraded_mode_checker import (
            _reset_degraded_mode_state,
        )

        _reset_degraded_mode_state()

    def test_health_monitor_enters_degraded(self):
        """Simulate health monitor detecting degraded state."""
        from app.services.governance.degraded import (
            DegradedModeState,
            GovernanceDegradedModeChecker,
        )

        checker = GovernanceDegradedModeChecker()

        # Health monitor detects issue
        status = checker.enter_degraded(
            state=DegradedModeState.DEGRADED,
            reason="Policy engine response time > 5s",
            entered_by="health_monitor",
            new_runs_action="WARN",  # Allow with warning
            create_incident=False,
        )

        # New runs allowed with warning
        allowed, _ = checker.should_allow_new_run("run-456")
        assert allowed is True

        # Existing runs get WARN action
        action = checker.get_existing_run_action()
        assert action == "WARN"

    def test_operator_recovers_from_degraded(self):
        """Simulate operator recovering from degraded mode."""
        from app.services.governance.degraded import (
            DegradedModeState,
            GovernanceDegradedModeChecker,
        )

        checker = GovernanceDegradedModeChecker()

        # Enter degraded mode
        checker.enter_degraded(
            state=DegradedModeState.DEGRADED,
            reason="Manual maintenance",
            entered_by="operator",
            create_incident=False,
        )

        # Operator completes maintenance
        status = checker.exit_degraded(
            exited_by="operator",
            create_incident=False,
        )

        assert status.state == DegradedModeState.NORMAL

        # Full functionality restored
        response = checker.check()
        assert response.is_degraded is False

    def test_critical_blocks_all_new_runs(self):
        """CRITICAL mode should block all new runs."""
        from app.services.governance.degraded import (
            DegradedModeState,
            GovernanceDegradedModeChecker,
            GovernanceDegradedModeError,
        )

        checker = GovernanceDegradedModeChecker()

        # Enter critical mode
        checker.enter_degraded(
            state=DegradedModeState.CRITICAL,
            reason="Database completely unavailable",
            entered_by="system",
            create_incident=False,
        )

        # All operations should be blocked
        with pytest.raises(GovernanceDegradedModeError):
            checker.ensure_not_degraded("start_new_run")

    def test_from_governance_config(self):
        """Create checker from GovernanceConfig."""
        from app.services.governance.degraded import GovernanceDegradedModeChecker

        class MockGovernanceConfig:
            degraded_mode_check_enabled = True

        checker = GovernanceDegradedModeChecker.from_governance_config(
            MockGovernanceConfig()
        )

        assert checker.check_enabled is True

    def test_from_governance_config_disabled(self):
        """Create checker with check disabled via config."""
        from app.services.governance.degraded import GovernanceDegradedModeChecker

        class MockGovernanceConfig:
            degraded_mode_check_enabled = False

        checker = GovernanceDegradedModeChecker.from_governance_config(
            MockGovernanceConfig()
        )

        assert checker.check_enabled is False
