# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-051 (Phase-Status Invariants)
"""
Unit tests for GAP-051: Phase-Status Invariants.

Tests the phase-status invariant enforcement service that checks
the phase_status_invariant_enforce flag before transitions.

CRITICAL TEST COVERAGE:
- PhaseStatusInvariantChecker imports and initializes
- Invariant validation correctly determines valid/invalid
- Enforcement raises error when enabled and invalid
- Helper functions work correctly
- All phase-status combinations validated
"""

import pytest


class TestPhaseStatusInvariantImports:
    """Test phase-status invariant module imports."""

    def test_checker_import(self):
        """PhaseStatusInvariantChecker should be importable."""
        from app.services.rok import PhaseStatusInvariantChecker

        assert PhaseStatusInvariantChecker is not None

    def test_error_import(self):
        """PhaseStatusInvariantEnforcementError should be importable."""
        from app.services.rok import PhaseStatusInvariantEnforcementError

        assert PhaseStatusInvariantEnforcementError is not None

    def test_result_enum_import(self):
        """InvariantCheckResult should be importable."""
        from app.services.rok import InvariantCheckResult

        assert InvariantCheckResult.VALID is not None

    def test_response_import(self):
        """InvariantCheckResponse should be importable."""
        from app.services.rok import InvariantCheckResponse

        assert InvariantCheckResponse is not None

    def test_invariants_map_import(self):
        """PHASE_STATUS_INVARIANTS should be importable."""
        from app.services.rok import PHASE_STATUS_INVARIANTS

        assert PHASE_STATUS_INVARIANTS is not None
        assert len(PHASE_STATUS_INVARIANTS) == 7  # 7 phases

    def test_helper_imports(self):
        """Helper functions should be importable."""
        from app.services.rok import (
            check_phase_status_invariant,
            ensure_phase_status_invariant,
        )

        assert check_phase_status_invariant is not None
        assert ensure_phase_status_invariant is not None


class TestInvariantCheckResult:
    """Test InvariantCheckResult enum."""

    def test_all_results_defined(self):
        """All required results should be defined."""
        from app.services.rok import InvariantCheckResult

        assert InvariantCheckResult.VALID is not None
        assert InvariantCheckResult.INVALID is not None
        assert InvariantCheckResult.ENFORCEMENT_DISABLED is not None
        assert InvariantCheckResult.UNKNOWN_PHASE is not None

    def test_result_values(self):
        """Result values should be strings."""
        from app.services.rok import InvariantCheckResult

        assert InvariantCheckResult.VALID.value == "valid"
        assert InvariantCheckResult.INVALID.value == "invalid"


class TestPhaseStatusInvariants:
    """Test the phase-status invariants map."""

    def test_created_allows_queued(self):
        """CREATED phase should allow only 'queued' status."""
        from app.services.rok import PHASE_STATUS_INVARIANTS

        assert "queued" in PHASE_STATUS_INVARIANTS["CREATED"]
        assert len(PHASE_STATUS_INVARIANTS["CREATED"]) == 1

    def test_authorized_allows_queued(self):
        """AUTHORIZED phase should allow only 'queued' status."""
        from app.services.rok import PHASE_STATUS_INVARIANTS

        assert "queued" in PHASE_STATUS_INVARIANTS["AUTHORIZED"]

    def test_executing_allows_running(self):
        """EXECUTING phase should allow only 'running' status."""
        from app.services.rok import PHASE_STATUS_INVARIANTS

        assert "running" in PHASE_STATUS_INVARIANTS["EXECUTING"]
        assert len(PHASE_STATUS_INVARIANTS["EXECUTING"]) == 1

    def test_governance_check_allows_running(self):
        """GOVERNANCE_CHECK phase should allow only 'running' status."""
        from app.services.rok import PHASE_STATUS_INVARIANTS

        assert "running" in PHASE_STATUS_INVARIANTS["GOVERNANCE_CHECK"]

    def test_finalizing_allows_running(self):
        """FINALIZING phase should allow only 'running' status."""
        from app.services.rok import PHASE_STATUS_INVARIANTS

        assert "running" in PHASE_STATUS_INVARIANTS["FINALIZING"]

    def test_completed_allows_succeeded(self):
        """COMPLETED phase should allow only 'succeeded' status."""
        from app.services.rok import PHASE_STATUS_INVARIANTS

        assert "succeeded" in PHASE_STATUS_INVARIANTS["COMPLETED"]
        assert len(PHASE_STATUS_INVARIANTS["COMPLETED"]) == 1

    def test_failed_allows_failure_statuses(self):
        """FAILED phase should allow failure statuses."""
        from app.services.rok import PHASE_STATUS_INVARIANTS

        failed_statuses = PHASE_STATUS_INVARIANTS["FAILED"]
        assert "failed" in failed_statuses
        assert "failed_policy" in failed_statuses
        assert "cancelled" in failed_statuses
        assert "retry" in failed_statuses


class TestPhaseStatusInvariantChecker:
    """Test PhaseStatusInvariantChecker class."""

    def test_default_enforcement_enabled(self):
        """Default checker should have enforcement enabled."""
        from app.services.rok import PhaseStatusInvariantChecker

        checker = PhaseStatusInvariantChecker()

        assert checker.enforcement_enabled

    def test_enforcement_can_be_disabled(self):
        """Checker can be created with enforcement disabled."""
        from app.services.rok import PhaseStatusInvariantChecker

        checker = PhaseStatusInvariantChecker(enforcement_enabled=False)

        assert not checker.enforcement_enabled

    def test_valid_combination(self):
        """Check should return VALID for valid combinations."""
        from app.services.rok import (
            InvariantCheckResult,
            PhaseStatusInvariantChecker,
        )

        checker = PhaseStatusInvariantChecker()
        response = checker.check("EXECUTING", "running")

        assert response.result == InvariantCheckResult.VALID
        assert response.is_valid is True

    def test_invalid_combination_enforced(self):
        """Check should return INVALID for invalid combinations when enforced."""
        from app.services.rok import (
            InvariantCheckResult,
            PhaseStatusInvariantChecker,
        )

        checker = PhaseStatusInvariantChecker(enforcement_enabled=True)
        response = checker.check("EXECUTING", "queued")  # Invalid

        assert response.result == InvariantCheckResult.INVALID
        assert response.is_valid is False

    def test_invalid_combination_not_enforced(self):
        """Check should return ENFORCEMENT_DISABLED when not enforced."""
        from app.services.rok import (
            InvariantCheckResult,
            PhaseStatusInvariantChecker,
        )

        checker = PhaseStatusInvariantChecker(enforcement_enabled=False)
        response = checker.check("EXECUTING", "queued")  # Invalid

        assert response.result == InvariantCheckResult.ENFORCEMENT_DISABLED
        assert response.is_valid is False
        assert not response.enforcement_enabled

    def test_unknown_phase(self):
        """Check should return UNKNOWN_PHASE for unrecognized phases."""
        from app.services.rok import (
            InvariantCheckResult,
            PhaseStatusInvariantChecker,
        )

        checker = PhaseStatusInvariantChecker()
        response = checker.check("UNKNOWN_PHASE", "running")

        assert response.result == InvariantCheckResult.UNKNOWN_PHASE
        assert response.is_valid is True  # Can't invalidate unknown phase

    def test_case_insensitive_phase(self):
        """Check should be case-insensitive for phase names."""
        from app.services.rok import (
            InvariantCheckResult,
            PhaseStatusInvariantChecker,
        )

        checker = PhaseStatusInvariantChecker()

        response1 = checker.check("executing", "running")
        response2 = checker.check("EXECUTING", "running")
        response3 = checker.check("Executing", "running")

        assert response1.result == InvariantCheckResult.VALID
        assert response2.result == InvariantCheckResult.VALID
        assert response3.result == InvariantCheckResult.VALID


class TestPhaseStatusInvariantCheckerEnsure:
    """Test ensure_valid method."""

    def test_ensure_valid_passes_for_valid(self):
        """ensure_valid should pass for valid combinations."""
        from app.services.rok import PhaseStatusInvariantChecker

        checker = PhaseStatusInvariantChecker()

        # Should not raise
        checker.ensure_valid("EXECUTING", "running")
        checker.ensure_valid("COMPLETED", "succeeded")
        checker.ensure_valid("FAILED", "failed")

    def test_ensure_valid_raises_for_invalid(self):
        """ensure_valid should raise for invalid combinations when enforced."""
        from app.services.rok import (
            PhaseStatusInvariantChecker,
            PhaseStatusInvariantEnforcementError,
        )

        checker = PhaseStatusInvariantChecker(enforcement_enabled=True)

        with pytest.raises(PhaseStatusInvariantEnforcementError) as exc_info:
            checker.ensure_valid("EXECUTING", "queued")

        assert exc_info.value.phase == "EXECUTING"
        assert exc_info.value.status == "queued"
        assert "running" in exc_info.value.allowed_statuses

    def test_ensure_valid_passes_when_enforcement_disabled(self):
        """ensure_valid should pass when enforcement disabled."""
        from app.services.rok import PhaseStatusInvariantChecker

        checker = PhaseStatusInvariantChecker(enforcement_enabled=False)

        # Should not raise even though invalid
        checker.ensure_valid("EXECUTING", "queued")


class TestPhaseStatusInvariantEnforcementError:
    """Test PhaseStatusInvariantEnforcementError."""

    def test_error_creation(self):
        """Should create error with all fields."""
        from app.services.rok import PhaseStatusInvariantEnforcementError

        error = PhaseStatusInvariantEnforcementError(
            message="Test error",
            phase="EXECUTING",
            status="queued",
            allowed_statuses=frozenset({"running"}),
            enforcement_enabled=True,
        )

        assert str(error) == "Test error"
        assert error.phase == "EXECUTING"
        assert error.status == "queued"
        assert "running" in error.allowed_statuses

    def test_error_to_dict(self):
        """to_dict should return structured error info."""
        from app.services.rok import PhaseStatusInvariantEnforcementError

        error = PhaseStatusInvariantEnforcementError(
            message="Test error",
            phase="COMPLETED",
            status="running",
            allowed_statuses=frozenset({"succeeded"}),
            enforcement_enabled=True,
        )

        d = error.to_dict()

        assert d["error"] == "PhaseStatusInvariantEnforcementError"
        assert d["phase"] == "COMPLETED"
        assert d["status"] == "running"
        assert "succeeded" in d["allowed_statuses"]


class TestInvariantCheckResponse:
    """Test InvariantCheckResponse dataclass."""

    def test_response_creation(self):
        """Should create response with all fields."""
        from app.services.rok import (
            InvariantCheckResponse,
            InvariantCheckResult,
        )

        response = InvariantCheckResponse(
            result=InvariantCheckResult.VALID,
            is_valid=True,
            enforcement_enabled=True,
            phase="EXECUTING",
            status="running",
            allowed_statuses=frozenset({"running"}),
            message="Test",
        )

        assert response.result == InvariantCheckResult.VALID
        assert response.is_valid is True

    def test_response_to_dict(self):
        """to_dict should return API-ready format."""
        from app.services.rok import (
            InvariantCheckResponse,
            InvariantCheckResult,
        )

        response = InvariantCheckResponse(
            result=InvariantCheckResult.INVALID,
            is_valid=False,
            enforcement_enabled=True,
            phase="EXECUTING",
            status="queued",
            allowed_statuses=frozenset({"running"}),
            message="Invalid",
        )

        d = response.to_dict()

        assert d["result"] == "invalid"
        assert d["is_valid"] is False
        assert d["phase"] == "EXECUTING"


class TestShouldAllowTransition:
    """Test should_allow_transition method."""

    def test_allow_valid_transition(self):
        """should_allow_transition should return True for valid."""
        from app.services.rok import PhaseStatusInvariantChecker

        checker = PhaseStatusInvariantChecker()

        allowed, reason = checker.should_allow_transition("EXECUTING", "running")

        assert allowed is True

    def test_disallow_invalid_transition_enforced(self):
        """should_allow_transition should return False when enforced."""
        from app.services.rok import PhaseStatusInvariantChecker

        checker = PhaseStatusInvariantChecker(enforcement_enabled=True)

        allowed, reason = checker.should_allow_transition("EXECUTING", "queued")

        assert allowed is False
        assert "EXECUTING" in reason

    def test_allow_invalid_transition_not_enforced(self):
        """should_allow_transition should return True when not enforced."""
        from app.services.rok import PhaseStatusInvariantChecker

        checker = PhaseStatusInvariantChecker(enforcement_enabled=False)

        allowed, reason = checker.should_allow_transition("EXECUTING", "queued")

        assert allowed is True
        assert "disabled" in reason.lower()


class TestHelperFunctions:
    """Test helper functions."""

    def test_check_phase_status_invariant_valid(self):
        """check_phase_status_invariant should return VALID for valid."""
        from app.services.rok import (
            InvariantCheckResult,
            check_phase_status_invariant,
        )

        response = check_phase_status_invariant(
            phase="EXECUTING",
            status="running",
            enforcement_enabled=True,
        )

        assert response.result == InvariantCheckResult.VALID

    def test_check_phase_status_invariant_invalid(self):
        """check_phase_status_invariant should return INVALID for invalid."""
        from app.services.rok import (
            InvariantCheckResult,
            check_phase_status_invariant,
        )

        response = check_phase_status_invariant(
            phase="COMPLETED",
            status="running",
            enforcement_enabled=True,
        )

        assert response.result == InvariantCheckResult.INVALID

    def test_ensure_phase_status_invariant_passes(self):
        """ensure_phase_status_invariant should pass for valid."""
        from app.services.rok import ensure_phase_status_invariant

        # Should not raise
        ensure_phase_status_invariant(
            phase="FAILED",
            status="failed_policy",
            enforcement_enabled=True,
        )

    def test_ensure_phase_status_invariant_raises(self):
        """ensure_phase_status_invariant should raise for invalid."""
        from app.services.rok import (
            PhaseStatusInvariantEnforcementError,
            ensure_phase_status_invariant,
        )

        with pytest.raises(PhaseStatusInvariantEnforcementError):
            ensure_phase_status_invariant(
                phase="CREATED",
                status="running",
                enforcement_enabled=True,
            )


class TestPhaseStatusInvariantUseCases:
    """Test realistic use cases for phase-status invariants."""

    def test_rok_phase_transition_valid(self):
        """Simulate ROK validating a valid phase transition."""
        from app.services.rok import PhaseStatusInvariantChecker

        # ROK transitioning from EXECUTING to GOVERNANCE_CHECK
        checker = PhaseStatusInvariantChecker(enforcement_enabled=True)

        # Validate current state
        checker.ensure_valid("EXECUTING", "running")

        # Status stays "running" during GOVERNANCE_CHECK
        checker.ensure_valid("GOVERNANCE_CHECK", "running")

    def test_rok_phase_transition_to_failed(self):
        """Simulate ROK transitioning to FAILED phase."""
        from app.services.rok import PhaseStatusInvariantChecker

        checker = PhaseStatusInvariantChecker(enforcement_enabled=True)

        # Can fail with any failure status
        checker.ensure_valid("FAILED", "failed")
        checker.ensure_valid("FAILED", "failed_policy")
        checker.ensure_valid("FAILED", "cancelled")
        checker.ensure_valid("FAILED", "retry")

    def test_invalid_executing_completed(self):
        """EXECUTING + succeeded is invalid (common bug pattern)."""
        from app.services.rok import (
            PhaseStatusInvariantChecker,
            PhaseStatusInvariantEnforcementError,
        )

        checker = PhaseStatusInvariantChecker(enforcement_enabled=True)

        # Bug: trying to mark as succeeded while still in EXECUTING
        with pytest.raises(PhaseStatusInvariantEnforcementError):
            checker.ensure_valid("EXECUTING", "succeeded")

    def test_invalid_completed_failed(self):
        """COMPLETED + failed is invalid."""
        from app.services.rok import (
            PhaseStatusInvariantChecker,
            PhaseStatusInvariantEnforcementError,
        )

        checker = PhaseStatusInvariantChecker(enforcement_enabled=True)

        # Bug: trying to mark COMPLETED run as failed
        with pytest.raises(PhaseStatusInvariantEnforcementError):
            checker.ensure_valid("COMPLETED", "failed")

    def test_from_governance_config(self):
        """Create checker from GovernanceConfig."""
        from app.services.rok import PhaseStatusInvariantChecker

        # Mock governance config
        class MockGovernanceConfig:
            phase_status_invariant_enforce = True

        checker = PhaseStatusInvariantChecker.from_governance_config(
            MockGovernanceConfig()
        )

        assert checker.enforcement_enabled is True

    def test_from_governance_config_disabled(self):
        """Create checker with enforcement disabled via config."""
        from app.services.rok import PhaseStatusInvariantChecker

        # Mock governance config with enforcement disabled
        class MockGovernanceConfig:
            phase_status_invariant_enforce = False

        checker = PhaseStatusInvariantChecker.from_governance_config(
            MockGovernanceConfig()
        )

        assert checker.enforcement_enabled is False

        # Should not raise even for invalid combinations
        checker.ensure_valid("EXECUTING", "succeeded")  # Invalid but allowed

    def test_all_valid_combinations(self):
        """Verify all valid phase-status combinations pass."""
        from app.services.rok import PHASE_STATUS_INVARIANTS, PhaseStatusInvariantChecker

        checker = PhaseStatusInvariantChecker(enforcement_enabled=True)

        for phase, allowed_statuses in PHASE_STATUS_INVARIANTS.items():
            for status in allowed_statuses:
                # All should pass without raising
                checker.ensure_valid(phase, status)
