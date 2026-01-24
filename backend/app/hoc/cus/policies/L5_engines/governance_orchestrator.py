# Layer: L5 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Governance Orchestrator - orchestrates contract execution
# Callers: L3 (adapters), L2 (governance APIs)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-292, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1
#
# ==============================================================================
# GOVERNANCE RULE: ORCHESTRATOR-AUTHORITY (Non-Negotiable)
# ==============================================================================
#
# This service orchestrates governance workflow execution.
#
# Orchestrator properties:
#   - ORCHESTRATES ONLY: Does not execute jobs (that's L5)
#   - NO HEALTH AUTHORITY: Captures health, does not modify it
#   - NO AUDIT AUTHORITY: Triggers audit, does not decide verdicts
#   - CONTRACT-BOUND: All actions derive from contract intent
#
# The Orchestrator:
#   - MAY: Activate contracts, create jobs, observe job state, trigger audit
#   - MUST NOT: Execute jobs, modify health, decide audit verdicts
#
# Reference: PART2_CRM_WORKFLOW_CHARTER.md, PIN-292, part2-design-v1
#
# ==============================================================================

"""
Part-2 Governance Orchestrator (L4)

Orchestrates the governance workflow from contract activation through
audit triggering. This is the "traffic controller" - it directs flow
but does not execute.

Components:
1. Contract Activation Service - APPROVED → ACTIVE
2. Execution Orchestrator - contract → job plan
3. Job State Tracker - observes job states
4. Audit Trigger - hands evidence to audit layer

Key Constraints (PIN-292):
- Orchestrates only; does not execute jobs
- No health or audit authority
- Contract is the sole source of execution intent
- MAY_NOT remains mechanically un-overridable

Reference: PART2_CRM_WORKFLOW_CHARTER.md, PIN-292, part2-design-v1
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Protocol
from uuid import UUID, uuid4

from app.models.contract import (
    ContractStatus,
)
from app.models.governance_job import (
    JOB_TERMINAL_STATES,
    JOB_VALID_TRANSITIONS,
    HealthSnapshot,
    InvalidJobTransitionError,
    JobImmutableError,
    JobStatus,
    JobStep,
    JobTransitionRecord,
    StepResult,
    StepStatus,
)
from app.services.governance.contract_service import ContractService, ContractState

# Orchestrator version
ORCHESTRATOR_VERSION = "1.0.0"


# ==============================================================================
# LOOKUP PROTOCOLS (Dependency Injection)
# ==============================================================================


class HealthLookup(Protocol):
    """Protocol for capturing health state (read-only)."""

    def capture_health_snapshot(self) -> HealthSnapshot:
        """Capture current health state for evidence."""
        ...


# ==============================================================================
# JOB STATE
# ==============================================================================


@dataclass
class JobState:
    """
    In-memory representation of job state.

    Used for state tracking before persistence.
    """

    job_id: UUID
    contract_id: UUID
    status: JobStatus
    status_reason: Optional[str]
    steps: list[JobStep]
    current_step_index: int
    total_steps: int
    step_results: list[StepResult]
    execution_evidence: Optional[dict[str, Any]]
    health_snapshot_before: Optional[HealthSnapshot]
    health_snapshot_after: Optional[HealthSnapshot]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    timeout_at: Optional[datetime]
    created_by: str
    transition_history: list[JobTransitionRecord] = field(default_factory=list)


# ==============================================================================
# JOB STATE MACHINE
# ==============================================================================


class JobStateMachine:
    """
    State machine for Governance Job lifecycle.

    Enforces:
    - JOB-002: Job steps execute in order
    - JOB-003: Terminal states are immutable
    """

    @staticmethod
    def can_transition(
        from_status: JobStatus,
        to_status: JobStatus,
    ) -> bool:
        """Check if a transition is valid."""
        valid_targets = JOB_VALID_TRANSITIONS.get(from_status, frozenset())
        return to_status in valid_targets

    @staticmethod
    def validate_transition(
        state: JobState,
        to_status: JobStatus,
    ) -> None:
        """
        Validate a job state transition.

        Raises:
            JobImmutableError: If job is in terminal state
            InvalidJobTransitionError: If transition is invalid
        """
        # JOB-003: Terminal states are immutable
        if state.status in JOB_TERMINAL_STATES:
            raise JobImmutableError(state.job_id, state.status)

        # Valid transitions only
        if not JobStateMachine.can_transition(state.status, to_status):
            raise InvalidJobTransitionError(
                state.status,
                to_status,
                f"No valid transition from {state.status.value} to {to_status.value}",
            )

    @staticmethod
    def transition(
        state: JobState,
        to_status: JobStatus,
        reason: str,
        transitioned_by: str,
        step_index: Optional[int] = None,
    ) -> JobState:
        """
        Execute a job state transition.

        Args:
            state: Current job state
            to_status: Target status
            reason: Reason for transition
            transitioned_by: Who initiated the transition
            step_index: Current step index (if applicable)

        Returns:
            New JobState with updated status

        Raises:
            JobImmutableError: If job is in terminal state
            InvalidJobTransitionError: If transition is invalid
        """
        # Validate transition
        JobStateMachine.validate_transition(state, to_status)

        # Record transition
        now = datetime.now(timezone.utc)
        transition_record = JobTransitionRecord(
            from_status=state.status.value,
            to_status=to_status.value,
            step_index=step_index,
            reason=reason,
            transitioned_by=transitioned_by,
            transitioned_at=now,
        )

        # Build updated state
        new_history = state.transition_history + [transition_record]

        # Determine timestamps
        started_at = state.started_at
        completed_at = state.completed_at

        if to_status == JobStatus.RUNNING and started_at is None:
            started_at = now

        if to_status in JOB_TERMINAL_STATES and completed_at is None:
            completed_at = now

        return JobState(
            job_id=state.job_id,
            contract_id=state.contract_id,
            status=to_status,
            status_reason=reason,
            steps=state.steps,
            current_step_index=step_index if step_index is not None else state.current_step_index,
            total_steps=state.total_steps,
            step_results=state.step_results,
            execution_evidence=state.execution_evidence,
            health_snapshot_before=state.health_snapshot_before,
            health_snapshot_after=state.health_snapshot_after,
            created_at=state.created_at,
            started_at=started_at,
            completed_at=completed_at,
            timeout_at=state.timeout_at,
            created_by=state.created_by,
            transition_history=new_history,
        )


# ==============================================================================
# EXECUTION ORCHESTRATOR
# ==============================================================================


class ExecutionOrchestrator:
    """
    Translates contract → job plan.

    This is purely a planning service. It does NOT execute.

    Responsibilities:
    1. Parse contract proposed_changes into JobSteps
    2. Validate step ordering
    3. Calculate timeouts

    Reference: PART2_CRM_WORKFLOW_CHARTER.md Step 7
    """

    @staticmethod
    def create_job_plan(
        contract_state: ContractState,
        timeout_minutes: int = 60,
    ) -> list[JobStep]:
        """
        Create job execution plan from contract.

        Args:
            contract_state: The contract to plan execution for
            timeout_minutes: Total job timeout in minutes

        Returns:
            Ordered list of JobSteps

        Raises:
            ValueError: If contract has no proposed changes
        """
        if not contract_state.proposed_changes:
            raise ValueError("Contract has no proposed changes")

        steps: list[JobStep] = []
        changes = contract_state.proposed_changes

        # Parse proposed_changes into steps
        # The contract proposed_changes schema is flexible,
        # but typically contains a list of changes or a single change
        if isinstance(changes, list):
            for idx, change in enumerate(changes):
                step = ExecutionOrchestrator._parse_change_to_step(idx, change)
                steps.append(step)
        elif isinstance(changes, dict):
            # Single change or structured changes
            if "changes" in changes:
                for idx, change in enumerate(changes["changes"]):
                    step = ExecutionOrchestrator._parse_change_to_step(idx, change)
                    steps.append(step)
            else:
                # Single change as dict
                step = ExecutionOrchestrator._parse_change_to_step(0, changes)
                steps.append(step)

        if not steps:
            raise ValueError("No valid steps could be created from proposed changes")

        return steps

    @staticmethod
    def _parse_change_to_step(index: int, change: dict[str, Any]) -> JobStep:
        """Parse a single change into a JobStep."""
        change_type = change.get("type", "unknown")
        target = change.get("capability_name") or change.get("scope") or "system"
        parameters = {k: v for k, v in change.items() if k not in ("type", "capability_name", "scope")}

        return JobStep(
            step_index=index,
            step_type=change_type,
            target=target,
            parameters=parameters,
            timeout_seconds=300,  # 5 minutes per step default
        )


# ==============================================================================
# JOB STATE TRACKER
# ==============================================================================


class JobStateTracker:
    """
    Observes job state - does NOT control execution.

    This is purely an observation service.

    Responsibilities:
    1. Track job state transitions
    2. Record step results
    3. Capture evidence for audit

    Key constraint: This service READS state, it doesn't DRIVE execution.
    The actual execution is done by L5 Job Executor.
    """

    def record_step_result(
        self,
        job_state: JobState,
        step_result: StepResult,
    ) -> JobState:
        """
        Record a step result (observation only).

        Args:
            job_state: Current job state
            step_result: Result of the step (from executor)

        Returns:
            Updated JobState with recorded result
        """
        new_results = job_state.step_results + [step_result]

        return JobState(
            job_id=job_state.job_id,
            contract_id=job_state.contract_id,
            status=job_state.status,
            status_reason=job_state.status_reason,
            steps=job_state.steps,
            current_step_index=step_result.step_index + 1,
            total_steps=job_state.total_steps,
            step_results=new_results,
            execution_evidence=job_state.execution_evidence,
            health_snapshot_before=job_state.health_snapshot_before,
            health_snapshot_after=step_result.health_after,
            created_at=job_state.created_at,
            started_at=job_state.started_at,
            completed_at=job_state.completed_at,
            timeout_at=job_state.timeout_at,
            created_by=job_state.created_by,
            transition_history=job_state.transition_history,
        )

    def calculate_completion_status(
        self,
        job_state: JobState,
    ) -> tuple[JobStatus, str]:
        """
        Calculate what the job's terminal status should be.

        Based on step results, determine if job COMPLETED or FAILED.
        This is observation - the actual transition is done by whoever
        calls JobStateMachine.transition().

        Returns:
            Tuple of (status, reason)
        """
        if not job_state.step_results:
            return JobStatus.FAILED, "No step results recorded"

        failed_steps = [r for r in job_state.step_results if r.status == StepStatus.FAILED]

        if failed_steps:
            failed_indices = [r.step_index for r in failed_steps]
            return JobStatus.FAILED, f"Steps failed: {failed_indices}"

        completed_steps = [r for r in job_state.step_results if r.status == StepStatus.COMPLETED]

        if len(completed_steps) == job_state.total_steps:
            return JobStatus.COMPLETED, "All steps completed successfully"

        return JobStatus.FAILED, f"Only {len(completed_steps)}/{job_state.total_steps} steps completed"


# ==============================================================================
# AUDIT TRIGGER
# ==============================================================================


@dataclass
class AuditEvidence:
    """
    Evidence package for audit layer.

    This is what we hand to the auditor (L8).
    """

    job_id: UUID
    contract_id: UUID
    job_status: JobStatus
    steps: list[JobStep]
    step_results: list[StepResult]
    health_before: Optional[HealthSnapshot]
    health_after: Optional[HealthSnapshot]
    execution_duration_seconds: Optional[float]
    collected_at: datetime


class AuditTrigger:
    """
    Prepares and hands evidence to audit layer.

    This service does NOT make audit decisions.
    It packages evidence and signals that audit should occur.

    The actual audit logic is in the Audit Service (L8).
    """

    @staticmethod
    def prepare_evidence(job_state: JobState) -> AuditEvidence:
        """
        Prepare evidence package for audit.

        Args:
            job_state: Completed (or failed) job state

        Returns:
            AuditEvidence package for audit layer
        """
        # Calculate execution duration
        duration = None
        if job_state.started_at and job_state.completed_at:
            delta = job_state.completed_at - job_state.started_at
            duration = delta.total_seconds()

        return AuditEvidence(
            job_id=job_state.job_id,
            contract_id=job_state.contract_id,
            job_status=job_state.status,
            steps=job_state.steps,
            step_results=job_state.step_results,
            health_before=job_state.health_snapshot_before,
            health_after=job_state.health_snapshot_after,
            execution_duration_seconds=duration,
            collected_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def should_trigger_audit(job_state: JobState) -> bool:
        """
        Determine if audit should be triggered.

        Audit is triggered when job reaches a terminal state.
        """
        return job_state.status in JOB_TERMINAL_STATES


# ==============================================================================
# CONTRACT ACTIVATION SERVICE
# ==============================================================================


class ContractActivationError(Exception):
    """Raised when contract activation fails."""

    def __init__(self, contract_id: UUID, reason: str):
        self.contract_id = contract_id
        self.reason = reason
        super().__init__(f"Cannot activate contract {contract_id}: {reason}")


class ContractActivationService:
    """
    Activates approved contracts (APPROVED → ACTIVE).

    This is the bridge between the contract state machine and job creation.

    Responsibilities:
    1. Verify contract is APPROVED
    2. Create job plan from contract
    3. Create job record
    4. Transition contract to ACTIVE

    Key constraint: Activation creates a job but does NOT execute it.
    """

    def __init__(
        self,
        contract_service: ContractService,
        health_lookup: Optional[HealthLookup] = None,
    ):
        self._contract_service = contract_service
        self._health_lookup = health_lookup
        self._orchestrator = ExecutionOrchestrator()

    def activate_contract(
        self,
        contract_state: ContractState,
        activated_by: str = "system",
        timeout_minutes: int = 60,
    ) -> tuple[ContractState, JobState]:
        """
        Activate an approved contract.

        This method:
        1. Validates contract is APPROVED
        2. Creates job plan
        3. Creates job state (PENDING)
        4. Transitions contract to ACTIVE
        5. Captures initial health snapshot

        Args:
            contract_state: Contract in APPROVED state
            activated_by: Who is activating
            timeout_minutes: Job timeout

        Returns:
            Tuple of (updated contract state, new job state)

        Raises:
            ContractActivationError: If activation fails
        """
        # Validate contract is APPROVED
        if contract_state.status != ContractStatus.APPROVED:
            raise ContractActivationError(
                contract_state.contract_id,
                f"Contract must be APPROVED, not {contract_state.status.value}",
            )

        # Create job plan from contract
        try:
            steps = self._orchestrator.create_job_plan(
                contract_state,
                timeout_minutes=timeout_minutes,
            )
        except ValueError as e:
            raise ContractActivationError(
                contract_state.contract_id,
                f"Failed to create job plan: {e}",
            )

        # Generate job ID
        job_id = uuid4()
        now = datetime.now(timezone.utc)

        # Capture initial health snapshot if available
        health_before = None
        if self._health_lookup:
            try:
                health_before = self._health_lookup.capture_health_snapshot()
            except Exception:
                # Health capture failure is not fatal, but should be noted
                pass

        # Create job state (PENDING)
        job_state = JobState(
            job_id=job_id,
            contract_id=contract_state.contract_id,
            status=JobStatus.PENDING,
            status_reason="Job created, awaiting execution",
            steps=steps,
            current_step_index=0,
            total_steps=len(steps),
            step_results=[],
            execution_evidence=None,
            health_snapshot_before=health_before,
            health_snapshot_after=None,
            created_at=now,
            started_at=None,
            completed_at=None,
            timeout_at=now + timedelta(minutes=timeout_minutes),
            created_by=activated_by,
            transition_history=[],
        )

        # Transition contract to ACTIVE
        updated_contract = self._contract_service.activate(
            state=contract_state,
            job_id=job_id,
            activated_by=activated_by,
        )

        return updated_contract, job_state


# ==============================================================================
# GOVERNANCE ORCHESTRATOR (FACADE)
# ==============================================================================


class GovernanceOrchestrator:
    """
    Facade for all governance orchestration services.

    This is the main entry point for governance workflow orchestration.
    It combines:
    - Contract Activation Service
    - Execution Orchestrator
    - Job State Tracker
    - Audit Trigger

    Key Properties (PIN-292):
    - Orchestrates only; does not execute jobs
    - No health or audit authority
    - Contract is the sole source of execution intent

    Reference: PART2_CRM_WORKFLOW_CHARTER.md, PIN-292
    """

    def __init__(
        self,
        contract_service: Optional[ContractService] = None,
        health_lookup: Optional[HealthLookup] = None,
    ):
        self._contract_service = contract_service or ContractService()
        self._activation_service = ContractActivationService(
            self._contract_service,
            health_lookup,
        )
        self._job_tracker = JobStateTracker()
        self._job_state_machine = JobStateMachine
        self._audit_trigger = AuditTrigger

    @property
    def version(self) -> str:
        """Return orchestrator version."""
        return ORCHESTRATOR_VERSION

    # ==========================================================================
    # CONTRACT ACTIVATION
    # ==========================================================================

    def activate_contract(
        self,
        contract_state: ContractState,
        activated_by: str = "system",
        timeout_minutes: int = 60,
    ) -> tuple[ContractState, JobState]:
        """
        Activate an approved contract, creating a job.

        This is the entry point for contract execution.
        After activation, the job is in PENDING state.
        The actual execution is done by the Job Executor (L5).

        Args:
            contract_state: Contract in APPROVED state
            activated_by: Who is activating
            timeout_minutes: Job timeout

        Returns:
            Tuple of (updated contract, new job)
        """
        return self._activation_service.activate_contract(
            contract_state=contract_state,
            activated_by=activated_by,
            timeout_minutes=timeout_minutes,
        )

    # ==========================================================================
    # JOB STATE TRACKING
    # ==========================================================================

    def start_job(
        self,
        job_state: JobState,
        started_by: str = "system",
    ) -> JobState:
        """
        Transition job from PENDING to RUNNING.

        Called when the Job Executor starts execution.
        """
        return self._job_state_machine.transition(
            state=job_state,
            to_status=JobStatus.RUNNING,
            reason="Execution started",
            transitioned_by=started_by,
            step_index=0,
        )

    def record_step_result(
        self,
        job_state: JobState,
        step_result: StepResult,
    ) -> JobState:
        """
        Record a step result from the executor.

        This is observation only - we're recording what happened.
        """
        return self._job_tracker.record_step_result(job_state, step_result)

    def complete_job(
        self,
        job_state: JobState,
        completed_by: str = "system",
    ) -> JobState:
        """
        Transition job to terminal state based on step results.

        Determines COMPLETED or FAILED based on recorded step results.
        """
        status, reason = self._job_tracker.calculate_completion_status(job_state)

        return self._job_state_machine.transition(
            state=job_state,
            to_status=status,
            reason=reason,
            transitioned_by=completed_by,
        )

    def cancel_job(
        self,
        job_state: JobState,
        reason: str,
        cancelled_by: str = "system",
    ) -> JobState:
        """
        Cancel a job manually.

        Can be called on PENDING or RUNNING jobs.
        """
        return self._job_state_machine.transition(
            state=job_state,
            to_status=JobStatus.CANCELLED,
            reason=reason,
            transitioned_by=cancelled_by,
        )

    # ==========================================================================
    # AUDIT TRIGGERING
    # ==========================================================================

    def should_trigger_audit(self, job_state: JobState) -> bool:
        """Check if audit should be triggered for this job."""
        return self._audit_trigger.should_trigger_audit(job_state)

    def prepare_audit_evidence(self, job_state: JobState) -> AuditEvidence:
        """
        Prepare evidence package for the audit layer.

        This prepares evidence but does NOT make audit decisions.
        The Audit Service (L8) receives this and makes the verdict.
        """
        return self._audit_trigger.prepare_evidence(job_state)

    # ==========================================================================
    # QUERY HELPERS
    # ==========================================================================

    def is_job_terminal(self, job_state: JobState) -> bool:
        """Check if job is in terminal state."""
        return job_state.status in JOB_TERMINAL_STATES

    def can_start_job(self, job_state: JobState) -> bool:
        """Check if job can be started."""
        return job_state.status == JobStatus.PENDING

    def get_job_progress(self, job_state: JobState) -> dict[str, Any]:
        """Get job execution progress."""
        return {
            "job_id": str(job_state.job_id),
            "status": job_state.status.value,
            "current_step": job_state.current_step_index,
            "total_steps": job_state.total_steps,
            "completed_steps": len([r for r in job_state.step_results if r.status == StepStatus.COMPLETED]),
            "failed_steps": len([r for r in job_state.step_results if r.status == StepStatus.FAILED]),
        }
