# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: pytest
#   Execution: sync
# Role: Governance Orchestrator invariant tests
# Callers: pytest, CI
# Allowed Imports: L4, L6 (test subjects)
# Forbidden Imports: None (test layer)
# Reference: PIN-292, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1

"""
Governance Orchestrator Invariant Tests (Part-2 CRM Workflow)

Tests for the governance orchestrator - the workflow coordinator that
bridges contracts to jobs.

Invariants tested:
- JOB-001: Jobs require contract_id (no orphan jobs)
- JOB-002: Job steps execute in order
- JOB-003: Terminal states are immutable
- JOB-004: Evidence is recorded per step
- JOB-005: Health snapshots are read-only

Key constraints (PIN-292):
- Orchestrates only; does not execute jobs
- No health or audit authority
- Contract is the sole source of execution intent

Reference: PIN-292, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.contract import (
    ContractSource,
    ContractStatus,
    RiskLevel,
)
from app.models.governance_job import (
    JOB_TERMINAL_STATES,
    JOB_VALID_TRANSITIONS,
    HealthSnapshot,
    InvalidJobTransitionError,
    JobImmutableError,
    JobStatus,
    JobStep,
    StepResult,
    StepStatus,
)
from app.services.governance import (
    AuditEvidence,
    AuditTrigger,
    ContractActivationError,
    ContractActivationService,
    ContractService,
    ContractState,
    EligibilityDecision,
    EligibilityVerdict,
    ExecutionOrchestrator,
    GovernanceOrchestrator,
    IssueType,
    JobState,
    JobStateMachine,
    JobStateTracker,
    RecommendedAction,
    Severity,
    ValidatorVerdict,
)

# ==============================================================================
# TEST FIXTURES
# ==============================================================================


def make_validator_verdict(
    issue_type: IssueType = IssueType.CAPABILITY_REQUEST,
    severity: Severity = Severity.MEDIUM,
    confidence: Decimal = Decimal("0.85"),
) -> ValidatorVerdict:
    """Create a test validator verdict."""
    return ValidatorVerdict(
        issue_type=issue_type,
        severity=severity,
        affected_capabilities=["test_capability"],
        recommended_action=RecommendedAction.CREATE_CONTRACT,
        confidence_score=confidence,
        reason="Test validation",
        evidence={"test": "evidence"},
        analyzed_at=datetime.now(timezone.utc),
        validator_version="1.0.0",
    )


def make_eligibility_verdict(
    decision: EligibilityDecision = EligibilityDecision.MAY,
) -> EligibilityVerdict:
    """Create a test eligibility verdict."""
    return EligibilityVerdict(
        decision=decision,
        reason="Test eligibility",
        rules_evaluated=6,
        first_failing_rule=None if decision == EligibilityDecision.MAY else "test_rule",
        rule_results=(),
        blocking_signals=(),
        missing_prerequisites=(),
        evaluated_at=datetime.now(timezone.utc),
        rules_version="1.0.0",
    )


def make_eligible_contract() -> ContractState:
    """Create a contract in ELIGIBLE state."""
    contract_service = ContractService()
    return contract_service.create_contract(
        issue_id=uuid4(),
        source=ContractSource.CRM_FEEDBACK,
        title="Test Contract",
        description="Test description",
        proposed_changes={"changes": [{"type": "capability_enable", "capability_name": "test_cap"}]},
        affected_capabilities=["test_cap"],
        risk_level=RiskLevel.LOW,
        validator_verdict=make_validator_verdict(),
        eligibility_verdict=make_eligibility_verdict(),
        created_by="test_user",
    )


def make_approved_contract() -> ContractState:
    """Create a contract in APPROVED state."""
    contract_service = ContractService()
    contract_state = make_eligible_contract()

    from app.models.contract import ContractApproval

    approval = ContractApproval(
        approved_by="founder_1",
        activation_window_hours=24,
    )

    return contract_service.approve(contract_state, approval)


def make_job_state(
    contract_id: uuid4 = None,
    status: JobStatus = JobStatus.PENDING,
) -> JobState:
    """Create a test job state."""
    contract_id = contract_id or uuid4()
    now = datetime.now(timezone.utc)

    return JobState(
        job_id=uuid4(),
        contract_id=contract_id,
        status=status,
        status_reason="Test job",
        steps=[
            JobStep(
                step_index=0,
                step_type="capability_enable",
                target="test_cap",
                parameters={},
            ),
            JobStep(
                step_index=1,
                step_type="configuration_update",
                target="system",
                parameters={"key": "value"},
            ),
        ],
        current_step_index=0,
        total_steps=2,
        step_results=[],
        execution_evidence=None,
        health_snapshot_before=None,
        health_snapshot_after=None,
        created_at=now,
        started_at=None,
        completed_at=None,
        timeout_at=now + timedelta(hours=1),
        created_by="system",
        transition_history=[],
    )


# ==============================================================================
# JOB-001: Jobs require contract_id
# ==============================================================================


class TestJOB001JobsRequireContract:
    """Test that jobs cannot be created without a contract."""

    def test_contract_activation_requires_approved_contract(self):
        """Contract activation fails if contract is not APPROVED."""
        orchestrator = GovernanceOrchestrator()
        contract = make_eligible_contract()  # ELIGIBLE, not APPROVED

        with pytest.raises(ContractActivationError) as exc_info:
            orchestrator.activate_contract(contract)

        assert "must be APPROVED" in str(exc_info.value)

    def test_contract_activation_creates_job_with_contract_id(self):
        """Activation creates a job linked to the contract."""
        orchestrator = GovernanceOrchestrator()
        contract = make_approved_contract()

        updated_contract, job = orchestrator.activate_contract(contract)

        assert job.contract_id == contract.contract_id
        assert updated_contract.job_id == job.job_id

    def test_job_state_has_contract_reference(self):
        """Job state always has a contract_id."""
        job = make_job_state()
        assert job.contract_id is not None


# ==============================================================================
# JOB-002: Job steps execute in order
# ==============================================================================


class TestJOB002StepsInOrder:
    """Test that job steps are tracked in order."""

    def test_job_steps_have_sequential_indices(self):
        """Steps have sequential indices starting from 0."""
        job = make_job_state()

        indices = [s.step_index for s in job.steps]
        assert indices == [0, 1]

    def test_current_step_index_starts_at_zero(self):
        """New jobs start at step index 0."""
        job = make_job_state()
        assert job.current_step_index == 0

    def test_step_result_advances_index(self):
        """Recording a step result advances the step index."""
        tracker = JobStateTracker()
        job = make_job_state(status=JobStatus.RUNNING)

        result = StepResult(
            step_index=0,
            status=StepStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            output={"result": "success"},
            error=None,
            health_after=None,
        )

        updated = tracker.record_step_result(job, result)

        assert updated.current_step_index == 1
        assert len(updated.step_results) == 1

    def test_execution_orchestrator_preserves_step_order(self):
        """Execution orchestrator creates steps in order."""
        contract = make_approved_contract()

        # Modify contract to have multiple changes
        contract.proposed_changes = {
            "changes": [
                {"type": "capability_enable", "capability_name": "cap1"},
                {"type": "capability_enable", "capability_name": "cap2"},
                {"type": "capability_enable", "capability_name": "cap3"},
            ]
        }

        steps = ExecutionOrchestrator.create_job_plan(contract)

        assert len(steps) == 3
        assert [s.step_index for s in steps] == [0, 1, 2]
        assert [s.target for s in steps] == ["cap1", "cap2", "cap3"]


# ==============================================================================
# JOB-003: Terminal states are immutable
# ==============================================================================


class TestJOB003TerminalImmutable:
    """Test that terminal job states cannot be modified."""

    @pytest.mark.parametrize("terminal_status", list(JOB_TERMINAL_STATES))
    def test_terminal_job_cannot_transition(self, terminal_status: JobStatus):
        """Terminal jobs cannot transition to any other state."""
        job = make_job_state(status=terminal_status)

        for target in JobStatus:
            if target != terminal_status:
                with pytest.raises(JobImmutableError):
                    JobStateMachine.transition(job, target, "test", "system")

    def test_completed_job_is_immutable(self):
        """COMPLETED jobs are immutable."""
        job = make_job_state(status=JobStatus.COMPLETED)

        with pytest.raises(JobImmutableError) as exc_info:
            JobStateMachine.transition(job, JobStatus.RUNNING, "restart", "system")

        assert "terminal state" in str(exc_info.value)

    def test_failed_job_is_immutable(self):
        """FAILED jobs are immutable."""
        job = make_job_state(status=JobStatus.FAILED)

        with pytest.raises(JobImmutableError):
            JobStateMachine.transition(job, JobStatus.PENDING, "retry", "system")

    def test_cancelled_job_is_immutable(self):
        """CANCELLED jobs are immutable."""
        job = make_job_state(status=JobStatus.CANCELLED)

        with pytest.raises(JobImmutableError):
            JobStateMachine.transition(job, JobStatus.RUNNING, "resume", "system")

    def test_valid_transitions_from_terminal_are_empty(self):
        """Terminal states have no valid transitions."""
        for terminal in JOB_TERMINAL_STATES:
            valid = JOB_VALID_TRANSITIONS.get(terminal, frozenset())
            assert valid == frozenset()


# ==============================================================================
# JOB-004: Evidence is recorded per step
# ==============================================================================


class TestJOB004EvidencePerStep:
    """Test that evidence is recorded for each step."""

    def test_step_result_contains_output(self):
        """Step results can contain output data."""
        result = StepResult(
            step_index=0,
            status=StepStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            output={"capability": "enabled", "config_applied": True},
            error=None,
            health_after=None,
        )

        assert result.output is not None
        assert "capability" in result.output

    def test_step_result_contains_error_on_failure(self):
        """Failed step results contain error information."""
        result = StepResult(
            step_index=0,
            status=StepStatus.FAILED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            output=None,
            error="Capability not found in registry",
            health_after=None,
        )

        assert result.error is not None
        assert "not found" in result.error

    def test_audit_evidence_contains_all_step_results(self):
        """Audit evidence includes results from all steps."""
        job = make_job_state(status=JobStatus.RUNNING)
        tracker = JobStateTracker()

        # Record two step results
        result1 = StepResult(
            step_index=0,
            status=StepStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            output={"step": 0},
            error=None,
            health_after=None,
        )
        result2 = StepResult(
            step_index=1,
            status=StepStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            output={"step": 1},
            error=None,
            health_after=None,
        )

        job = tracker.record_step_result(job, result1)
        job = tracker.record_step_result(job, result2)

        # Complete the job
        job = JobStateMachine.transition(job, JobStatus.COMPLETED, "All steps done", "system")

        # Prepare evidence
        evidence = AuditTrigger.prepare_evidence(job)

        assert len(evidence.step_results) == 2
        assert evidence.step_results[0].step_index == 0
        assert evidence.step_results[1].step_index == 1


# ==============================================================================
# JOB-005: Health snapshots are read-only
# ==============================================================================


class TestJOB005HealthReadOnly:
    """Test that health snapshots are observations only."""

    def test_health_snapshot_is_observation(self):
        """Health snapshots are point-in-time observations."""
        snapshot = HealthSnapshot(
            captured_at=datetime.now(timezone.utc),
            capabilities={"test_cap": {"lifecycle": "LAUNCHED", "healthy": True}},
            system_health={"status": "healthy"},
        )

        assert snapshot.captured_at is not None
        assert "test_cap" in snapshot.capabilities

    def test_job_state_stores_before_snapshot(self):
        """Job state can store health before execution."""
        snapshot = HealthSnapshot(
            captured_at=datetime.now(timezone.utc),
            capabilities={"test_cap": {"lifecycle": "LAUNCHED"}},
            system_health={},
        )

        job = make_job_state()
        # Simulate setting health before
        job = JobState(
            job_id=job.job_id,
            contract_id=job.contract_id,
            status=job.status,
            status_reason=job.status_reason,
            steps=job.steps,
            current_step_index=job.current_step_index,
            total_steps=job.total_steps,
            step_results=job.step_results,
            execution_evidence=job.execution_evidence,
            health_snapshot_before=snapshot,
            health_snapshot_after=job.health_snapshot_after,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            timeout_at=job.timeout_at,
            created_by=job.created_by,
            transition_history=job.transition_history,
        )

        assert job.health_snapshot_before is not None
        assert job.health_snapshot_before.captured_at is not None

    def test_audit_evidence_includes_health_snapshots(self):
        """Audit evidence includes both health snapshots."""
        before = HealthSnapshot(
            captured_at=datetime.now(timezone.utc),
            capabilities={"cap": {"lifecycle": "LAUNCHED"}},
            system_health={},
        )
        after = HealthSnapshot(
            captured_at=datetime.now(timezone.utc),
            capabilities={"cap": {"lifecycle": "LAUNCHED", "modified": True}},
            system_health={},
        )

        job = make_job_state(status=JobStatus.COMPLETED)
        job = JobState(
            job_id=job.job_id,
            contract_id=job.contract_id,
            status=job.status,
            status_reason=job.status_reason,
            steps=job.steps,
            current_step_index=job.current_step_index,
            total_steps=job.total_steps,
            step_results=job.step_results,
            execution_evidence=job.execution_evidence,
            health_snapshot_before=before,
            health_snapshot_after=after,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=datetime.now(timezone.utc),
            timeout_at=job.timeout_at,
            created_by=job.created_by,
            transition_history=job.transition_history,
        )

        evidence = AuditTrigger.prepare_evidence(job)

        assert evidence.health_before is not None
        assert evidence.health_after is not None


# ==============================================================================
# JOB STATE MACHINE TESTS
# ==============================================================================


class TestJobStateMachine:
    """Test job state machine transitions."""

    def test_pending_to_running(self):
        """PENDING can transition to RUNNING."""
        job = make_job_state(status=JobStatus.PENDING)

        updated = JobStateMachine.transition(job, JobStatus.RUNNING, "Starting", "system")

        assert updated.status == JobStatus.RUNNING
        assert updated.started_at is not None

    def test_running_to_completed(self):
        """RUNNING can transition to COMPLETED."""
        job = make_job_state(status=JobStatus.RUNNING)

        updated = JobStateMachine.transition(job, JobStatus.COMPLETED, "Done", "system")

        assert updated.status == JobStatus.COMPLETED
        assert updated.completed_at is not None

    def test_running_to_failed(self):
        """RUNNING can transition to FAILED."""
        job = make_job_state(status=JobStatus.RUNNING)

        updated = JobStateMachine.transition(job, JobStatus.FAILED, "Step failed", "system")

        assert updated.status == JobStatus.FAILED
        assert updated.completed_at is not None

    def test_pending_to_cancelled(self):
        """PENDING can be CANCELLED."""
        job = make_job_state(status=JobStatus.PENDING)

        updated = JobStateMachine.transition(job, JobStatus.CANCELLED, "Cancelled by user", "user")

        assert updated.status == JobStatus.CANCELLED

    def test_invalid_transition_raises_error(self):
        """Invalid transitions raise InvalidJobTransitionError."""
        job = make_job_state(status=JobStatus.PENDING)

        # Cannot go directly from PENDING to COMPLETED
        with pytest.raises(InvalidJobTransitionError) as exc_info:
            JobStateMachine.transition(job, JobStatus.COMPLETED, "Skip", "system")

        assert "PENDING" in str(exc_info.value)
        assert "COMPLETED" in str(exc_info.value)

    def test_transition_records_history(self):
        """Transitions are recorded in history."""
        job = make_job_state(status=JobStatus.PENDING)

        updated = JobStateMachine.transition(job, JobStatus.RUNNING, "Starting", "test_user")

        assert len(updated.transition_history) == 1
        assert updated.transition_history[0].from_status == "PENDING"
        assert updated.transition_history[0].to_status == "RUNNING"
        assert updated.transition_history[0].transitioned_by == "test_user"


# ==============================================================================
# EXECUTION ORCHESTRATOR TESTS
# ==============================================================================


class TestExecutionOrchestrator:
    """Test job plan creation from contracts."""

    def test_creates_steps_from_changes_list(self):
        """Creates steps from a list of changes."""
        contract = make_approved_contract()
        contract.proposed_changes = {
            "changes": [
                {"type": "capability_enable", "capability_name": "cap1"},
                {"type": "capability_disable", "capability_name": "cap2"},
            ]
        }

        steps = ExecutionOrchestrator.create_job_plan(contract)

        assert len(steps) == 2
        assert steps[0].step_type == "capability_enable"
        assert steps[1].step_type == "capability_disable"

    def test_creates_step_from_single_change(self):
        """Creates step from a single change dict."""
        contract = make_approved_contract()
        contract.proposed_changes = {
            "type": "configuration_update",
            "scope": "system",
            "key": "max_workers",
            "new_value": 10,
        }

        steps = ExecutionOrchestrator.create_job_plan(contract)

        assert len(steps) == 1
        assert steps[0].step_type == "configuration_update"
        assert steps[0].target == "system"

    def test_raises_on_empty_changes(self):
        """Raises ValueError if no changes in contract."""
        contract = make_approved_contract()
        contract.proposed_changes = {}

        with pytest.raises(ValueError) as exc_info:
            ExecutionOrchestrator.create_job_plan(contract)

        assert "no proposed changes" in str(exc_info.value).lower()


# ==============================================================================
# JOB STATE TRACKER TESTS
# ==============================================================================


class TestJobStateTracker:
    """Test job state observation."""

    def test_calculate_completion_completed(self):
        """Calculates COMPLETED when all steps pass."""
        tracker = JobStateTracker()
        job = make_job_state(status=JobStatus.RUNNING)

        # Add two completed results
        job.step_results = [
            StepResult(
                step_index=0,
                status=StepStatus.COMPLETED,
                started_at=None,
                completed_at=None,
                output=None,
                error=None,
                health_after=None,
            ),
            StepResult(
                step_index=1,
                status=StepStatus.COMPLETED,
                started_at=None,
                completed_at=None,
                output=None,
                error=None,
                health_after=None,
            ),
        ]

        status, reason = tracker.calculate_completion_status(job)

        assert status == JobStatus.COMPLETED
        assert "All steps completed" in reason

    def test_calculate_completion_failed(self):
        """Calculates FAILED when any step fails."""
        tracker = JobStateTracker()
        job = make_job_state(status=JobStatus.RUNNING)

        job.step_results = [
            StepResult(
                step_index=0,
                status=StepStatus.COMPLETED,
                started_at=None,
                completed_at=None,
                output=None,
                error=None,
                health_after=None,
            ),
            StepResult(
                step_index=1,
                status=StepStatus.FAILED,
                started_at=None,
                completed_at=None,
                output=None,
                error="Oops",
                health_after=None,
            ),
        ]

        status, reason = tracker.calculate_completion_status(job)

        assert status == JobStatus.FAILED
        assert "Steps failed" in reason


# ==============================================================================
# AUDIT TRIGGER TESTS
# ==============================================================================


class TestAuditTrigger:
    """Test audit evidence preparation."""

    def test_should_trigger_on_completed(self):
        """Audit triggers when job is COMPLETED."""
        job = make_job_state(status=JobStatus.COMPLETED)
        assert AuditTrigger.should_trigger_audit(job) is True

    def test_should_trigger_on_failed(self):
        """Audit triggers when job is FAILED."""
        job = make_job_state(status=JobStatus.FAILED)
        assert AuditTrigger.should_trigger_audit(job) is True

    def test_should_trigger_on_cancelled(self):
        """Audit triggers when job is CANCELLED."""
        job = make_job_state(status=JobStatus.CANCELLED)
        assert AuditTrigger.should_trigger_audit(job) is True

    def test_should_not_trigger_on_running(self):
        """Audit does NOT trigger when job is RUNNING."""
        job = make_job_state(status=JobStatus.RUNNING)
        assert AuditTrigger.should_trigger_audit(job) is False

    def test_should_not_trigger_on_pending(self):
        """Audit does NOT trigger when job is PENDING."""
        job = make_job_state(status=JobStatus.PENDING)
        assert AuditTrigger.should_trigger_audit(job) is False

    def test_evidence_contains_all_fields(self):
        """Evidence package contains all required fields."""
        job = make_job_state(status=JobStatus.COMPLETED)
        job = JobState(
            job_id=job.job_id,
            contract_id=job.contract_id,
            status=job.status,
            status_reason=job.status_reason,
            steps=job.steps,
            current_step_index=job.current_step_index,
            total_steps=job.total_steps,
            step_results=[
                StepResult(
                    step_index=0,
                    status=StepStatus.COMPLETED,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    output={"result": "ok"},
                    error=None,
                    health_after=None,
                ),
            ],
            execution_evidence=None,
            health_snapshot_before=None,
            health_snapshot_after=None,
            created_at=job.created_at,
            started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            completed_at=datetime.now(timezone.utc),
            timeout_at=job.timeout_at,
            created_by=job.created_by,
            transition_history=job.transition_history,
        )

        evidence = AuditTrigger.prepare_evidence(job)

        assert evidence.job_id == job.job_id
        assert evidence.contract_id == job.contract_id
        assert evidence.job_status == JobStatus.COMPLETED
        assert len(evidence.steps) == 2
        assert len(evidence.step_results) == 1
        assert evidence.execution_duration_seconds is not None
        assert evidence.collected_at is not None


# ==============================================================================
# CONTRACT ACTIVATION SERVICE TESTS
# ==============================================================================


class TestContractActivationService:
    """Test contract activation workflow."""

    def test_activation_fails_for_non_approved(self):
        """Activation fails if contract is not APPROVED."""
        contract = make_eligible_contract()  # ELIGIBLE, not APPROVED
        service = ContractActivationService(ContractService())

        with pytest.raises(ContractActivationError):
            service.activate_contract(contract)

    def test_activation_creates_job_in_pending(self):
        """Activation creates a job in PENDING status."""
        contract = make_approved_contract()
        service = ContractActivationService(ContractService())

        updated_contract, job = service.activate_contract(contract)

        assert job.status == JobStatus.PENDING

    def test_activation_transitions_contract_to_active(self):
        """Activation transitions contract to ACTIVE."""
        contract = make_approved_contract()
        service = ContractActivationService(ContractService())

        updated_contract, job = service.activate_contract(contract)

        assert updated_contract.status == ContractStatus.ACTIVE
        assert updated_contract.job_id == job.job_id

    def test_activation_sets_timeout(self):
        """Activation sets job timeout."""
        contract = make_approved_contract()
        service = ContractActivationService(ContractService())

        _, job = service.activate_contract(contract, timeout_minutes=30)

        assert job.timeout_at is not None
        # Timeout should be roughly 30 minutes from now
        delta = job.timeout_at - job.created_at
        assert 29 <= delta.total_seconds() / 60 <= 31


# ==============================================================================
# GOVERNANCE ORCHESTRATOR FACADE TESTS
# ==============================================================================


class TestGovernanceOrchestratorFacade:
    """Test the main orchestrator facade."""

    def test_full_workflow_pending_to_completed(self):
        """Test the full workflow from activation to completion."""
        orchestrator = GovernanceOrchestrator()
        contract = make_approved_contract()

        # Step 1: Activate contract
        contract, job = orchestrator.activate_contract(contract)
        assert job.status == JobStatus.PENDING
        assert contract.status == ContractStatus.ACTIVE

        # Step 2: Start job
        job = orchestrator.start_job(job)
        assert job.status == JobStatus.RUNNING

        # Step 3: Record step results
        for i in range(job.total_steps):
            result = StepResult(
                step_index=i,
                status=StepStatus.COMPLETED,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                output={"step": i},
                error=None,
                health_after=None,
            )
            job = orchestrator.record_step_result(job, result)

        # Step 4: Complete job
        job = orchestrator.complete_job(job)
        assert job.status == JobStatus.COMPLETED

        # Step 5: Check if audit should trigger
        assert orchestrator.should_trigger_audit(job) is True

        # Step 6: Prepare evidence
        evidence = orchestrator.prepare_audit_evidence(job)
        assert evidence.job_status == JobStatus.COMPLETED

    def test_job_progress_tracking(self):
        """Test job progress query."""
        orchestrator = GovernanceOrchestrator()
        contract = make_approved_contract()

        _, job = orchestrator.activate_contract(contract)
        job = orchestrator.start_job(job)

        # Record one step
        result = StepResult(
            step_index=0,
            status=StepStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            output={},
            error=None,
            health_after=None,
        )
        job = orchestrator.record_step_result(job, result)

        progress = orchestrator.get_job_progress(job)

        assert progress["status"] == "RUNNING"
        assert progress["completed_steps"] == 1
        assert progress["total_steps"] == job.total_steps

    def test_cancel_job(self):
        """Test job cancellation."""
        orchestrator = GovernanceOrchestrator()
        contract = make_approved_contract()

        _, job = orchestrator.activate_contract(contract)

        job = orchestrator.cancel_job(job, "User requested", "user123")

        assert job.status == JobStatus.CANCELLED
        assert orchestrator.is_job_terminal(job) is True


# ==============================================================================
# ORCHESTRATOR AUTHORITY BOUNDARIES TESTS
# ==============================================================================


class TestOrchestratorBoundaries:
    """Test that orchestrator respects authority boundaries."""

    def test_orchestrator_does_not_execute(self):
        """Orchestrator creates jobs but doesn't execute them."""
        orchestrator = GovernanceOrchestrator()
        contract = make_approved_contract()

        _, job = orchestrator.activate_contract(contract)

        # Job is in PENDING, not RUNNING or COMPLETED
        # Actual execution requires L5 Job Executor
        assert job.status == JobStatus.PENDING
        assert len(job.step_results) == 0

    def test_orchestrator_observes_not_controls(self):
        """Orchestrator observes step results, doesn't generate them."""
        orchestrator = GovernanceOrchestrator()
        contract = make_approved_contract()

        _, job = orchestrator.activate_contract(contract)
        job = orchestrator.start_job(job)

        # The orchestrator can record results but doesn't create them
        # Results come from the Job Executor (L5)
        result = StepResult(
            step_index=0,
            status=StepStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            output={"from_executor": True},  # This would come from L5
            error=None,
            health_after=None,
        )

        # Orchestrator just records what happened
        job = orchestrator.record_step_result(job, result)

        assert job.step_results[0].output["from_executor"] is True

    def test_audit_trigger_does_not_decide(self):
        """Audit trigger prepares evidence but doesn't make verdicts."""
        job = make_job_state(status=JobStatus.COMPLETED)

        evidence = AuditTrigger.prepare_evidence(job)

        # Evidence package has no verdict - that's for audit layer (L8)
        assert isinstance(evidence, AuditEvidence)
        # There's no verdict field in evidence - just raw data
        assert hasattr(evidence, "job_status")
        assert hasattr(evidence, "step_results")
        # Verdict would be added by Audit Service, not here


# ==============================================================================
# STATE MACHINE COMPLETENESS TESTS
# ==============================================================================


class TestJobStateMachineCompleteness:
    """Test state machine is complete and well-defined."""

    def test_all_states_have_transition_entry(self):
        """Every job status has an entry in transitions map."""
        for status in JobStatus:
            assert status in JOB_VALID_TRANSITIONS

    def test_no_transition_to_pending(self):
        """No state can transition TO PENDING (only initial state)."""
        for source, targets in JOB_VALID_TRANSITIONS.items():
            assert JobStatus.PENDING not in targets

    def test_terminal_states_are_terminal(self):
        """Terminal states have no valid transitions."""
        for terminal in JOB_TERMINAL_STATES:
            assert JOB_VALID_TRANSITIONS[terminal] == frozenset()

    def test_non_terminal_states_have_transitions(self):
        """Non-terminal states have at least one transition."""
        non_terminal = {s for s in JobStatus if s not in JOB_TERMINAL_STATES}
        for status in non_terminal:
            assert len(JOB_VALID_TRANSITIONS[status]) > 0
