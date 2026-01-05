# Layer: L8 — Catalyst / Verification Tests
# Product: system-wide (Part-2 CRM Workflow)
# Temporal:
#   Trigger: pytest
#   Execution: sync
# Role: Invariant tests for Audit Service
# Callers: CI/CD, developers
# Reference: PIN-295, GOVERNANCE_AUDIT_MODEL.md

"""
Part-2 Governance Audit Service Invariant Tests

Tests for the audit verification layer (L8).

Invariants tested:
- AUDIT-001: All completed jobs require audit
- AUDIT-002: PASS required for COMPLETED
- AUDIT-003: FAIL triggers rollback
- AUDIT-004: Verdicts are immutable
- AUDIT-005: Evidence is preserved
- AUDIT-006: Health snapshots required

Checks tested:
- A-001: Scope Compliance
- A-002: Health Preservation
- A-003: Execution Fidelity
- A-004: Timing Compliance
- A-005: Rollback Availability
- A-006: Signal Consistency
- A-007: No Unauthorized Mutations

Reference: PIN-295, GOVERNANCE_AUDIT_MODEL.md
"""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.models.contract import AuditVerdict
from app.services.governance.audit_service import (
    AUDIT_SERVICE_VERSION,
    AuditCheck,
    AuditChecks,
    AuditInput,
    AuditService,
    CheckResult,
    RolloutGate,
    audit_result_to_record,
    create_audit_input_from_evidence,
)

# ==============================================================================
# TEST FIXTURES
# ==============================================================================


@pytest.fixture
def audit_service():
    """Create audit service for testing."""
    return AuditService()


@pytest.fixture
def base_audit_input():
    """Create a base audit input for testing."""
    now = datetime.now(timezone.utc)
    return AuditInput(
        job_id=uuid4(),
        contract_id=uuid4(),
        job_status="COMPLETED",
        contract_scope=["capability_a", "capability_b"],
        proposed_changes={"capability_name": "capability_a", "type": "enable"},
        steps_executed=[],
        step_results=[
            {
                "step_index": 0,
                "status": "COMPLETED",
                "output": {"target": "capability_a", "handler": "noop"},
            }
        ],
        health_before={"capability_a": "HEALTHY", "capability_b": "HEALTHY"},
        health_after={"capability_a": "HEALTHY", "capability_b": "HEALTHY"},
        activation_window_start=now - timedelta(hours=1),
        activation_window_end=now + timedelta(hours=23),
        job_started_at=now - timedelta(minutes=5),
        job_completed_at=now,
        execution_duration_seconds=300.0,
    )


# ==============================================================================
# AUDIT-001: ALL COMPLETED JOBS REQUIRE AUDIT
# ==============================================================================


class TestAUDIT001CompletedJobsRequireAudit:
    """AUDIT-001: All completed jobs require audit."""

    def test_audit_accepts_completed_job(self, audit_service: AuditService, base_audit_input: AuditInput):
        """Audit can process a completed job."""
        result = audit_service.audit(base_audit_input)

        assert result is not None
        assert result.job_id == base_audit_input.job_id
        assert result.contract_id == base_audit_input.contract_id

    def test_audit_accepts_failed_job(self, audit_service: AuditService):
        """Audit can process a failed job."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="FAILED",
            contract_scope=["capability_a"],
            proposed_changes={},
            steps_executed=[],
            step_results=[
                {
                    "step_index": 0,
                    "status": "FAILED",
                    "error": "Step execution failed",
                }
            ],
            health_before={"capability_a": "HEALTHY"},
            health_after={"capability_a": "HEALTHY"},
            activation_window_start=None,
            activation_window_end=None,
            job_started_at=now - timedelta(minutes=1),
            job_completed_at=now,
            execution_duration_seconds=60.0,
        )

        result = audit_service.audit(audit_input)

        assert result is not None
        assert result.verdict in [AuditVerdict.PASS, AuditVerdict.FAIL, AuditVerdict.INCONCLUSIVE]

    def test_audit_produces_valid_result(self, audit_service: AuditService, base_audit_input: AuditInput):
        """Audit produces a complete result."""
        result = audit_service.audit(base_audit_input)

        assert result.audit_id is not None
        assert result.verdict in [AuditVerdict.PASS, AuditVerdict.FAIL, AuditVerdict.INCONCLUSIVE]
        assert len(result.checks) == 7  # All 7 checks
        assert result.audited_at is not None
        assert result.auditor_version == AUDIT_SERVICE_VERSION


# ==============================================================================
# AUDIT-002: PASS REQUIRED FOR COMPLETED
# ==============================================================================


class TestAUDIT002PassRequiredForCompleted:
    """AUDIT-002: PASS required for COMPLETED."""

    def test_rollout_authorized_only_on_pass(self):
        """Rollout is authorized only with PASS verdict."""
        assert RolloutGate.is_rollout_authorized(AuditVerdict.PASS) is True
        assert RolloutGate.is_rollout_authorized(AuditVerdict.FAIL) is False
        assert RolloutGate.is_rollout_authorized(AuditVerdict.INCONCLUSIVE) is False
        assert RolloutGate.is_rollout_authorized(AuditVerdict.PENDING) is False

    def test_rollout_status_pass(self):
        """PASS verdict produces proceed action."""
        status = RolloutGate.get_rollout_status(AuditVerdict.PASS)

        assert status["authorized"] is True
        assert status["action"] == "proceed"

    def test_rollout_status_fail(self):
        """FAIL verdict produces rollback action."""
        status = RolloutGate.get_rollout_status(AuditVerdict.FAIL)

        assert status["authorized"] is False
        assert status["action"] == "rollback"

    def test_rollout_status_inconclusive(self):
        """INCONCLUSIVE verdict produces escalate action."""
        status = RolloutGate.get_rollout_status(AuditVerdict.INCONCLUSIVE)

        assert status["authorized"] is False
        assert status["action"] == "escalate"


# ==============================================================================
# AUDIT-003: FAIL TRIGGERS ROLLBACK
# ==============================================================================


class TestAUDIT003FailTriggersRollback:
    """AUDIT-003: FAIL triggers rollback."""

    def test_any_failed_check_produces_fail_verdict(self, audit_service: AuditService):
        """A single failed check produces FAIL verdict."""
        now = datetime.now(timezone.utc)
        # Create input that fails scope compliance
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["capability_a"],  # Only capability_a in scope
            proposed_changes={"capability_name": "capability_a"},
            steps_executed=[],
            step_results=[
                {
                    "step_index": 0,
                    "status": "COMPLETED",
                    "output": {"target": "capability_b", "handler": "noop"},  # Wrong target!
                }
            ],
            health_before={"capability_a": "HEALTHY"},
            health_after={"capability_a": "HEALTHY"},
            activation_window_start=now - timedelta(hours=1),
            activation_window_end=now + timedelta(hours=23),
            job_started_at=now - timedelta(minutes=5),
            job_completed_at=now,
            execution_duration_seconds=300.0,
        )

        result = audit_service.audit(audit_input)

        assert result.verdict == AuditVerdict.FAIL
        assert "Scope Compliance" in result.verdict_reason

    def test_fail_verdict_blocks_rollout(self):
        """FAIL verdict blocks rollout with rollback action."""
        status = RolloutGate.get_rollout_status(AuditVerdict.FAIL)

        assert status["authorized"] is False
        assert status["action"] == "rollback"
        assert "rollback" in status["reason"].lower()

    def test_multiple_failures_produces_fail(self, audit_service: AuditService):
        """Multiple failed checks still produces single FAIL verdict."""
        now = datetime.now(timezone.utc)
        # Outside activation window AND wrong scope
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["capability_a"],
            proposed_changes={"capability_name": "capability_a"},
            steps_executed=[],
            step_results=[
                {
                    "step_index": 0,
                    "status": "COMPLETED",
                    "output": {"target": "capability_b"},  # Wrong target
                }
            ],
            health_before={"capability_a": "HEALTHY"},
            health_after={"capability_a": "UNHEALTHY"},  # Health degraded
            activation_window_start=now + timedelta(hours=1),  # Future window
            activation_window_end=now + timedelta(hours=25),
            job_started_at=now - timedelta(minutes=5),
            job_completed_at=now,
            execution_duration_seconds=300.0,
        )

        result = audit_service.audit(audit_input)

        assert result.verdict == AuditVerdict.FAIL
        assert result.checks_failed >= 2


# ==============================================================================
# AUDIT-004: VERDICTS ARE IMMUTABLE
# ==============================================================================


class TestAUDIT004VerdictImmutability:
    """AUDIT-004: Verdicts are immutable."""

    def test_audit_result_is_frozen(self, audit_service: AuditService, base_audit_input: AuditInput):
        """AuditResult is a frozen dataclass."""
        result = audit_service.audit(base_audit_input)

        with pytest.raises(FrozenInstanceError):
            result.verdict = AuditVerdict.FAIL  # type: ignore

    def test_audit_check_is_frozen(self):
        """AuditCheck is a frozen dataclass."""
        check = AuditCheck(
            check_id="A-001",
            name="Test",
            question="Test?",
            result=CheckResult.PASS,
            reason="Test",
            evidence={},
        )

        with pytest.raises(FrozenInstanceError):
            check.result = CheckResult.FAIL  # type: ignore

    def test_audit_input_is_frozen(self):
        """AuditInput is a frozen dataclass."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=[],
            proposed_changes={},
            steps_executed=[],
            step_results=[],
            health_before=None,
            health_after=None,
            activation_window_start=None,
            activation_window_end=None,
            job_started_at=now,
            job_completed_at=now,
            execution_duration_seconds=0.0,
        )

        with pytest.raises(FrozenInstanceError):
            audit_input.job_status = "FAILED"  # type: ignore

    def test_checks_tuple_is_immutable(self, audit_service: AuditService, base_audit_input: AuditInput):
        """Checks tuple cannot be modified."""
        result = audit_service.audit(base_audit_input)

        # Tuple is immutable
        assert isinstance(result.checks, tuple)

        with pytest.raises(TypeError):
            result.checks[0] = None  # type: ignore


# ==============================================================================
# AUDIT-005: EVIDENCE IS PRESERVED
# ==============================================================================


class TestAUDIT005EvidencePreserved:
    """AUDIT-005: Evidence is preserved."""

    def test_evidence_summary_captured(self, audit_service: AuditService, base_audit_input: AuditInput):
        """Evidence summary is captured in result."""
        result = audit_service.audit(base_audit_input)

        assert result.evidence_summary is not None
        assert "job_id" in result.evidence_summary
        assert "contract_id" in result.evidence_summary
        assert "job_status" in result.evidence_summary

    def test_check_evidence_captured(self, audit_service: AuditService, base_audit_input: AuditInput):
        """Each check captures evidence."""
        result = audit_service.audit(base_audit_input)

        for check in result.checks:
            assert check.evidence is not None
            assert isinstance(check.evidence, dict)

    def test_health_snapshots_preserved(self, audit_service: AuditService, base_audit_input: AuditInput):
        """Health snapshots are preserved in result."""
        result = audit_service.audit(base_audit_input)

        assert result.health_snapshot_before == base_audit_input.health_before
        assert result.health_snapshot_after == base_audit_input.health_after

    def test_audit_result_serializable(self, audit_service: AuditService, base_audit_input: AuditInput):
        """Audit result can be serialized to record format."""
        result = audit_service.audit(base_audit_input)
        record = audit_result_to_record(result)

        assert "audit_id" in record
        assert "verdict" in record
        assert "checks_performed" in record
        assert len(record["checks_performed"]) == 7


# ==============================================================================
# AUDIT-006: HEALTH SNAPSHOTS REQUIRED
# ==============================================================================


class TestAUDIT006HealthSnapshotsRequired:
    """AUDIT-006: Health snapshots required."""

    def test_missing_health_before_inconclusive(self, audit_service: AuditService):
        """Missing health_before produces INCONCLUSIVE on health check."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["capability_a"],
            proposed_changes={},
            steps_executed=[],
            step_results=[],
            health_before=None,  # Missing!
            health_after={"capability_a": "HEALTHY"},
            activation_window_start=now - timedelta(hours=1),
            activation_window_end=now + timedelta(hours=23),
            job_started_at=now - timedelta(minutes=5),
            job_completed_at=now,
            execution_duration_seconds=300.0,
        )

        result = audit_service.audit(audit_input)

        # Find health preservation check
        health_check = next(c for c in result.checks if c.check_id == "A-002")
        assert health_check.result == CheckResult.INCONCLUSIVE

    def test_missing_health_after_inconclusive(self, audit_service: AuditService):
        """Missing health_after produces INCONCLUSIVE on health check."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["capability_a"],
            proposed_changes={},
            steps_executed=[],
            step_results=[],
            health_before={"capability_a": "HEALTHY"},
            health_after=None,  # Missing!
            activation_window_start=now - timedelta(hours=1),
            activation_window_end=now + timedelta(hours=23),
            job_started_at=now - timedelta(minutes=5),
            job_completed_at=now,
            execution_duration_seconds=300.0,
        )

        result = audit_service.audit(audit_input)

        # Find health preservation check
        health_check = next(c for c in result.checks if c.check_id == "A-002")
        assert health_check.result == CheckResult.INCONCLUSIVE

    def test_inconclusive_blocks_rollout(self):
        """INCONCLUSIVE verdict blocks rollout."""
        assert RolloutGate.is_rollout_authorized(AuditVerdict.INCONCLUSIVE) is False


# ==============================================================================
# CHECK A-001: SCOPE COMPLIANCE
# ==============================================================================


class TestCheckA001ScopeCompliance:
    """A-001: Scope Compliance tests."""

    def test_all_targets_in_scope_passes(self):
        """All targets within scope produces PASS."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["cap_a", "cap_b"],
            proposed_changes={},
            steps_executed=[],
            step_results=[
                {"status": "COMPLETED", "output": {"target": "cap_a"}},
                {"status": "COMPLETED", "output": {"target": "cap_b"}},
            ],
            health_before=None,
            health_after=None,
            activation_window_start=None,
            activation_window_end=None,
            job_started_at=now,
            job_completed_at=now,
            execution_duration_seconds=0.0,
        )

        check = AuditChecks.check_scope_compliance(audit_input)

        assert check.result == CheckResult.PASS

    def test_unauthorized_target_fails(self):
        """Target outside scope produces FAIL."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["cap_a"],
            proposed_changes={},
            steps_executed=[],
            step_results=[
                {"status": "COMPLETED", "output": {"target": "cap_b"}},  # Not in scope!
            ],
            health_before=None,
            health_after=None,
            activation_window_start=None,
            activation_window_end=None,
            job_started_at=now,
            job_completed_at=now,
            execution_duration_seconds=0.0,
        )

        check = AuditChecks.check_scope_compliance(audit_input)

        assert check.result == CheckResult.FAIL
        assert "cap_b" in str(check.evidence.get("unauthorized"))


# ==============================================================================
# CHECK A-002: HEALTH PRESERVATION
# ==============================================================================


class TestCheckA002HealthPreservation:
    """A-002: Health Preservation tests."""

    def test_health_maintained_passes(self):
        """Health maintained produces PASS."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=[],
            proposed_changes={},
            steps_executed=[],
            step_results=[],
            health_before={"cap_a": "HEALTHY", "cap_b": "DEGRADED"},
            health_after={"cap_a": "HEALTHY", "cap_b": "DEGRADED"},
            activation_window_start=None,
            activation_window_end=None,
            job_started_at=now,
            job_completed_at=now,
            execution_duration_seconds=0.0,
        )

        check = AuditChecks.check_health_preservation(audit_input)

        assert check.result == CheckResult.PASS

    def test_health_improved_passes(self):
        """Health improvement produces PASS."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=[],
            proposed_changes={},
            steps_executed=[],
            step_results=[],
            health_before={"cap_a": "DEGRADED"},
            health_after={"cap_a": "HEALTHY"},  # Improved!
            activation_window_start=None,
            activation_window_end=None,
            job_started_at=now,
            job_completed_at=now,
            execution_duration_seconds=0.0,
        )

        check = AuditChecks.check_health_preservation(audit_input)

        assert check.result == CheckResult.PASS

    def test_health_degraded_fails(self):
        """Health degradation produces FAIL."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=[],
            proposed_changes={},
            steps_executed=[],
            step_results=[],
            health_before={"cap_a": "HEALTHY"},
            health_after={"cap_a": "UNHEALTHY"},  # Degraded!
            activation_window_start=None,
            activation_window_end=None,
            job_started_at=now,
            job_completed_at=now,
            execution_duration_seconds=0.0,
        )

        check = AuditChecks.check_health_preservation(audit_input)

        assert check.result == CheckResult.FAIL


# ==============================================================================
# CHECK A-003: EXECUTION FIDELITY
# ==============================================================================


class TestCheckA003ExecutionFidelity:
    """A-003: Execution Fidelity tests."""

    def test_execution_matches_proposal_passes(self):
        """Execution matching proposal produces PASS."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["cap_a"],
            proposed_changes={"capability_name": "cap_a", "type": "enable"},
            steps_executed=[],
            step_results=[
                {"status": "COMPLETED", "output": {"target": "cap_a"}},
            ],
            health_before=None,
            health_after=None,
            activation_window_start=None,
            activation_window_end=None,
            job_started_at=now,
            job_completed_at=now,
            execution_duration_seconds=0.0,
        )

        check = AuditChecks.check_execution_fidelity(audit_input)

        assert check.result == CheckResult.PASS

    def test_missing_execution_fails(self):
        """Proposed change not executed produces FAIL on completed job."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["cap_a"],
            proposed_changes={"capability_name": "cap_a"},
            steps_executed=[],
            step_results=[],  # No steps executed!
            health_before=None,
            health_after=None,
            activation_window_start=None,
            activation_window_end=None,
            job_started_at=now,
            job_completed_at=now,
            execution_duration_seconds=0.0,
        )

        check = AuditChecks.check_execution_fidelity(audit_input)

        assert check.result == CheckResult.FAIL


# ==============================================================================
# CHECK A-004: TIMING COMPLIANCE
# ==============================================================================


class TestCheckA004TimingCompliance:
    """A-004: Timing Compliance tests."""

    def test_execution_within_window_passes(self):
        """Execution within window produces PASS."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=[],
            proposed_changes={},
            steps_executed=[],
            step_results=[],
            health_before=None,
            health_after=None,
            activation_window_start=now - timedelta(hours=2),
            activation_window_end=now + timedelta(hours=22),
            job_started_at=now - timedelta(minutes=30),
            job_completed_at=now,
            execution_duration_seconds=1800.0,
        )

        check = AuditChecks.check_timing_compliance(audit_input)

        assert check.result == CheckResult.PASS

    def test_execution_before_window_fails(self):
        """Execution before window produces FAIL."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=[],
            proposed_changes={},
            steps_executed=[],
            step_results=[],
            health_before=None,
            health_after=None,
            activation_window_start=now + timedelta(hours=1),  # Window in future
            activation_window_end=now + timedelta(hours=25),
            job_started_at=now - timedelta(minutes=30),  # Started before window
            job_completed_at=now,
            execution_duration_seconds=1800.0,
        )

        check = AuditChecks.check_timing_compliance(audit_input)

        assert check.result == CheckResult.FAIL

    def test_no_window_inconclusive(self):
        """No activation window produces INCONCLUSIVE."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=[],
            proposed_changes={},
            steps_executed=[],
            step_results=[],
            health_before=None,
            health_after=None,
            activation_window_start=None,  # No window
            activation_window_end=None,
            job_started_at=now - timedelta(minutes=30),
            job_completed_at=now,
            execution_duration_seconds=1800.0,
        )

        check = AuditChecks.check_timing_compliance(audit_input)

        assert check.result == CheckResult.INCONCLUSIVE


# ==============================================================================
# CHECK A-007: NO UNAUTHORIZED MUTATIONS
# ==============================================================================


class TestCheckA007NoUnauthorizedMutations:
    """A-007: No Unauthorized Mutations tests."""

    def test_only_scoped_changes_passes(self):
        """Changes only to scoped capabilities produces PASS."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["cap_a"],
            proposed_changes={},
            steps_executed=[],
            step_results=[],
            health_before={"cap_a": "DEGRADED", "cap_b": "HEALTHY"},
            health_after={"cap_a": "HEALTHY", "cap_b": "HEALTHY"},  # Only cap_a changed
            activation_window_start=None,
            activation_window_end=None,
            job_started_at=now,
            job_completed_at=now,
            execution_duration_seconds=0.0,
        )

        check = AuditChecks.check_no_unauthorized_mutations(audit_input)

        assert check.result == CheckResult.PASS

    def test_out_of_scope_change_fails(self):
        """Changes to out-of-scope capability produces FAIL."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["cap_a"],  # Only cap_a in scope
            proposed_changes={},
            steps_executed=[],
            step_results=[],
            health_before={"cap_a": "HEALTHY", "cap_b": "HEALTHY"},
            health_after={"cap_a": "HEALTHY", "cap_b": "UNHEALTHY"},  # cap_b changed!
            activation_window_start=None,
            activation_window_end=None,
            job_started_at=now,
            job_completed_at=now,
            execution_duration_seconds=0.0,
        )

        check = AuditChecks.check_no_unauthorized_mutations(audit_input)

        assert check.result == CheckResult.FAIL
        assert "cap_b" in check.evidence.get("unauthorized_changes", [])


# ==============================================================================
# VERDICT DETERMINATION
# ==============================================================================


class TestVerdictDetermination:
    """Verdict determination logic tests."""

    def test_all_pass_produces_pass_verdict(self, audit_service: AuditService, base_audit_input: AuditInput):
        """All checks passing produces PASS verdict."""
        result = audit_service.audit(base_audit_input)

        # Base input should pass all checks
        assert result.checks_failed == 0
        assert result.checks_inconclusive == 0
        assert result.verdict == AuditVerdict.PASS

    def test_fail_takes_priority_over_inconclusive(self, audit_service: AuditService):
        """FAIL verdict takes priority over INCONCLUSIVE."""
        now = datetime.now(timezone.utc)
        # Input with both failures and inconclusive
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["cap_a"],
            proposed_changes={"capability_name": "cap_a"},
            steps_executed=[],
            step_results=[
                {"status": "COMPLETED", "output": {"target": "cap_b"}},  # Scope fail
            ],
            health_before=None,  # Health inconclusive
            health_after=None,
            activation_window_start=None,  # Timing inconclusive
            activation_window_end=None,
            job_started_at=now,
            job_completed_at=now,
            execution_duration_seconds=0.0,
        )

        result = audit_service.audit(audit_input)

        assert result.verdict == AuditVerdict.FAIL  # FAIL takes priority

    def test_verdict_reason_includes_failed_checks(self, audit_service: AuditService):
        """Verdict reason includes failed check names."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["cap_a"],
            proposed_changes={},
            steps_executed=[],
            step_results=[
                {"status": "COMPLETED", "output": {"target": "cap_b"}},
            ],
            health_before=None,
            health_after=None,
            activation_window_start=None,
            activation_window_end=None,
            job_started_at=now,
            job_completed_at=now,
            execution_duration_seconds=0.0,
        )

        result = audit_service.audit(audit_input)

        assert "Scope Compliance" in result.verdict_reason


# ==============================================================================
# AUDIT SERVICE METADATA
# ==============================================================================


class TestAuditServiceMetadata:
    """Audit service metadata tests."""

    def test_service_has_version(self, audit_service: AuditService):
        """Service has version property."""
        assert audit_service.version == AUDIT_SERVICE_VERSION

    def test_custom_version(self):
        """Service can be created with custom version."""
        custom_service = AuditService(auditor_version="2.0.0")
        assert custom_service.version == "2.0.0"

    def test_result_includes_version(self, audit_service: AuditService, base_audit_input: AuditInput):
        """Result includes auditor version."""
        result = audit_service.audit(base_audit_input)
        assert result.auditor_version == AUDIT_SERVICE_VERSION


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================


class TestAuditIntegration:
    """Integration tests for audit flow."""

    def test_full_audit_flow_pass(self, audit_service: AuditService):
        """Full audit flow with all checks passing."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["capability_x", "capability_y"],
            proposed_changes=[
                {"capability_name": "capability_x", "type": "enable"},
                {"capability_name": "capability_y", "type": "enable"},
            ],
            steps_executed=[],
            step_results=[
                {
                    "step_index": 0,
                    "status": "COMPLETED",
                    "output": {"target": "capability_x", "handler": "noop"},
                },
                {
                    "step_index": 1,
                    "status": "COMPLETED",
                    "output": {"target": "capability_y", "handler": "noop"},
                },
            ],
            health_before={"capability_x": "HEALTHY", "capability_y": "HEALTHY"},
            health_after={"capability_x": "HEALTHY", "capability_y": "HEALTHY"},
            activation_window_start=now - timedelta(hours=1),
            activation_window_end=now + timedelta(hours=23),
            job_started_at=now - timedelta(minutes=10),
            job_completed_at=now,
            execution_duration_seconds=600.0,
        )

        result = audit_service.audit(audit_input)

        assert result.verdict == AuditVerdict.PASS
        assert result.checks_passed == 7
        assert result.checks_failed == 0
        assert RolloutGate.is_rollout_authorized(result.verdict) is True

    def test_full_audit_flow_fail(self, audit_service: AuditService):
        """Full audit flow with failure."""
        now = datetime.now(timezone.utc)
        audit_input = AuditInput(
            job_id=uuid4(),
            contract_id=uuid4(),
            job_status="COMPLETED",
            contract_scope=["capability_x"],
            proposed_changes={"capability_name": "capability_x"},
            steps_executed=[],
            step_results=[
                {
                    "step_index": 0,
                    "status": "COMPLETED",
                    "output": {"target": "capability_z"},  # Wrong target!
                },
            ],
            health_before={"capability_x": "HEALTHY"},
            health_after={"capability_x": "UNHEALTHY"},  # Degraded!
            activation_window_start=now - timedelta(hours=1),
            activation_window_end=now + timedelta(hours=23),
            job_started_at=now - timedelta(minutes=10),
            job_completed_at=now,
            execution_duration_seconds=600.0,
        )

        result = audit_service.audit(audit_input)

        assert result.verdict == AuditVerdict.FAIL
        assert result.checks_failed >= 2
        assert RolloutGate.is_rollout_authorized(result.verdict) is False

    def test_create_audit_input_helper(self):
        """Test helper to create audit input from evidence."""
        job_id = uuid4()
        contract_id = uuid4()
        execution_result = {
            "step_results": [{"step_index": 0, "status": "COMPLETED", "output": {"target": "cap_a"}}],
            "health_observations": {
                "before": {"cap_a": "HEALTHY"},
                "after": {"cap_a": "HEALTHY"},
            },
            "timing": {
                "started_at": "2026-01-04T10:00:00+00:00",
                "completed_at": "2026-01-04T10:05:00+00:00",
                "duration_seconds": 300.0,
            },
        }

        audit_input = create_audit_input_from_evidence(
            job_id=job_id,
            contract_id=contract_id,
            job_status="COMPLETED",
            contract_scope=["cap_a"],
            proposed_changes={"capability_name": "cap_a"},
            execution_result=execution_result,
        )

        assert audit_input.job_id == job_id
        assert audit_input.contract_id == contract_id
        assert audit_input.job_status == "COMPLETED"
        assert len(audit_input.step_results) == 1
        assert audit_input.health_before is not None
