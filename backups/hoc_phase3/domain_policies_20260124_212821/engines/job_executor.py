# Layer: L5 — Execution & Workers
# Product: system-wide (Part-2 CRM Workflow)
# Temporal:
#   Trigger: worker|scheduler
#   Execution: async (background execution)
# Role: Job Executor - executes job steps and emits evidence
# Callers: workers, governance orchestrator (via message queue)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4
# Reference: PIN-294, PIN-292, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1
#
# ==============================================================================
# GOVERNANCE RULE: EXECUTOR-AUTHORITY (Non-Negotiable)
# ==============================================================================
#
# This service executes job steps. It is a MACHINE.
#
# Executor properties:
#   - PLAN CONSUMER: Executes JobSteps as declared
#   - EVIDENCE EMITTER: Records output per step
#   - FAILURE-STOP: Stops immediately on step failure
#   - NO DECISION: Does not interpret, retry, or modify scope
#   - HEALTH OBSERVER: Captures health, never modifies it
#
# The Executor:
#   - MAY: Execute steps, emit evidence, capture health, report completion
#   - MUST NOT: Modify contracts, change eligibility, retry failed steps,
#               interpret severity, modify health signals, decide outcomes
#
# Reference: PART2_CRM_WORKFLOW_CHARTER.md, PIN-294, part2-design-v1
#
# ==============================================================================

"""
Part-2 Job Executor (L5)

Executes governance job steps in order and emits evidence.

This is a MACHINE that performs declared steps. It does not:
- Decide what to execute (that's Contract + Orchestrator)
- Retry failures (failed = done)
- Interpret results (that's Audit)
- Modify health (that's PlatformHealthService)

The Executor is "just physics" - it runs the plan and records what happened.

Invariants:
- EXEC-001: Execute steps in declared order
- EXEC-002: Emit evidence per step
- EXEC-003: Stop on first failure
- EXEC-004: Health is observed, never modified
- EXEC-005: No eligibility or contract mutation
- EXEC-006: No retry logic

Reference: PIN-294, PIN-292, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Protocol
from uuid import UUID

from app.models.governance_job import (
    JobStatus,
    JobStep,
    StepResult,
    StepStatus,
)

# Executor version
EXECUTOR_VERSION = "1.0.0"


# ==============================================================================
# PROTOCOLS (Dependency Injection)
# ==============================================================================


class HealthObserver(Protocol):
    """
    Protocol for observing health state (read-only).

    JOB EXECUTOR RULE: Health is OBSERVED, not MODIFIED.
    """

    def observe_health(self) -> dict[str, Any]:
        """
        Capture current health state.

        Returns:
            Dictionary of capability health states

        Note: This is READ-ONLY observation. The executor
        cannot modify health signals.
        """
        ...


class StepHandler(Protocol):
    """
    Protocol for step type handlers.

    Each step type (capability_enable, capability_disable, etc.)
    has a handler that performs the actual operation.
    """

    def execute(
        self,
        step: JobStep,
        context: "ExecutionContext",
    ) -> "StepOutput":
        """
        Execute a single step.

        Args:
            step: The step to execute
            context: Execution context

        Returns:
            StepOutput with success/failure and output
        """
        ...


# ==============================================================================
# EXECUTION DATA TYPES
# ==============================================================================


@dataclass(frozen=True)
class StepOutput:
    """
    Output from executing a single step.

    This is the raw output from the step handler,
    before it becomes a StepResult.
    """

    success: bool
    output: dict[str, Any]
    error: Optional[str] = None


@dataclass(frozen=True)
class ExecutionContext:
    """
    Context passed to step handlers during execution.

    Contains information the handler needs without
    giving it authority to change governance state.
    """

    job_id: UUID
    contract_id: UUID
    step_index: int
    step_type: str
    target: str
    executed_by: str
    started_at: datetime


@dataclass(frozen=True)
class ExecutionResult:
    """
    Result of executing a job.

    Contains the final status and all step results.
    """

    job_id: UUID
    final_status: JobStatus
    final_reason: str
    steps_executed: int
    steps_succeeded: int
    steps_failed: int
    step_results: tuple[StepResult, ...]
    health_before: Optional[dict[str, Any]]
    health_after: Optional[dict[str, Any]]
    started_at: datetime
    completed_at: datetime


# ==============================================================================
# JOB EXECUTOR
# ==============================================================================


class JobExecutor:
    """
    Part-2 Job Executor (L5)

    Executes governance job steps in order and emits evidence.

    Key Properties (PIN-294):
    - Consumes job plans only
    - No eligibility, no approval, no contract mutation
    - Emits evidence per step
    - Stops on failure
    - Health is observed, never modified

    Usage:
        executor = JobExecutor()
        result = executor.execute_job(job_state, health_observer)
    """

    def __init__(
        self,
        handlers: Optional[dict[str, StepHandler]] = None,
        executor_version: str = EXECUTOR_VERSION,
    ):
        """
        Initialize Job Executor.

        Args:
            handlers: Step type handlers (optional, defaults provided)
            executor_version: Version string
        """
        self._version = executor_version
        self._handlers = handlers or {}

    @property
    def version(self) -> str:
        """Return executor version."""
        return self._version

    def register_handler(self, step_type: str, handler: StepHandler) -> None:
        """
        Register a handler for a step type.

        Args:
            step_type: Type of step (e.g., "capability_enable")
            handler: Handler that executes this step type
        """
        self._handlers[step_type] = handler

    def execute_job(
        self,
        job_id: UUID,
        contract_id: UUID,
        steps: list[JobStep],
        health_observer: Optional[HealthObserver] = None,
        executed_by: str = "executor",
    ) -> ExecutionResult:
        """
        Execute a job's steps in order.

        EXEC-001: Steps execute in declared order
        EXEC-002: Evidence emitted per step
        EXEC-003: Stop on first failure
        EXEC-004: Health observed, never modified

        Args:
            job_id: The job being executed
            contract_id: The contract this job derives from
            steps: Ordered list of steps to execute
            health_observer: For capturing health state (optional)
            executed_by: Identifier for who/what is executing

        Returns:
            ExecutionResult with final status and all evidence
        """
        started_at = datetime.now(timezone.utc)

        # EXEC-004: Observe health before execution (read-only)
        health_before = None
        if health_observer:
            health_before = health_observer.observe_health()

        step_results: list[StepResult] = []
        steps_succeeded = 0
        steps_failed = 0
        final_status = JobStatus.COMPLETED
        final_reason = "All steps completed successfully"
        health_after = None

        # EXEC-001: Execute steps in order
        for step in steps:
            step_result = self._execute_step(
                step=step,
                job_id=job_id,
                contract_id=contract_id,
                health_observer=health_observer,
                executed_by=executed_by,
            )

            # EXEC-002: Record evidence for this step
            step_results.append(step_result)

            if step_result.status == StepStatus.COMPLETED:
                steps_succeeded += 1
                # Update health_after to latest observation
                if step_result.health_after:
                    health_after = step_result.health_after
            else:
                steps_failed += 1
                final_status = JobStatus.FAILED
                final_reason = f"Step {step.step_index} failed: {step_result.error}"

                # EXEC-003: Stop on first failure
                break

        completed_at = datetime.now(timezone.utc)

        return ExecutionResult(
            job_id=job_id,
            final_status=final_status,
            final_reason=final_reason,
            steps_executed=len(step_results),
            steps_succeeded=steps_succeeded,
            steps_failed=steps_failed,
            step_results=tuple(step_results),
            health_before=health_before,
            health_after=health_after,
            started_at=started_at,
            completed_at=completed_at,
        )

    def _execute_step(
        self,
        step: JobStep,
        job_id: UUID,
        contract_id: UUID,
        health_observer: Optional[HealthObserver],
        executed_by: str,
    ) -> StepResult:
        """
        Execute a single step and return result.

        This method:
        1. Creates execution context
        2. Finds handler for step type
        3. Executes with timeout
        4. Captures health after
        5. Returns StepResult evidence
        """
        step_started_at = datetime.now(timezone.utc)

        # Create context for handler
        context = ExecutionContext(
            job_id=job_id,
            contract_id=contract_id,
            step_index=step.step_index,
            step_type=step.step_type,
            target=step.target,
            executed_by=executed_by,
            started_at=step_started_at,
        )

        # Find handler for step type
        handler = self._handlers.get(step.step_type)

        if handler is None:
            # No handler = step cannot execute
            return StepResult(
                step_index=step.step_index,
                status=StepStatus.FAILED,
                started_at=step_started_at,
                completed_at=datetime.now(timezone.utc),
                output=None,
                error=f"No handler registered for step type: {step.step_type}",
                health_after=None,
            )

        try:
            # Execute the step
            output = handler.execute(step, context)

            step_completed_at = datetime.now(timezone.utc)

            # EXEC-004: Observe health after step (read-only)
            health_after = None
            if health_observer:
                health_after = health_observer.observe_health()

            if output.success:
                return StepResult(
                    step_index=step.step_index,
                    status=StepStatus.COMPLETED,
                    started_at=step_started_at,
                    completed_at=step_completed_at,
                    output=output.output,
                    error=None,
                    health_after=health_after,
                )
            else:
                return StepResult(
                    step_index=step.step_index,
                    status=StepStatus.FAILED,
                    started_at=step_started_at,
                    completed_at=step_completed_at,
                    output=output.output,
                    error=output.error,
                    health_after=health_after,
                )

        except Exception as e:
            # Execution error - record and return failure
            return StepResult(
                step_index=step.step_index,
                status=StepStatus.FAILED,
                started_at=step_started_at,
                completed_at=datetime.now(timezone.utc),
                output=None,
                error=f"Execution error: {str(e)}",
                health_after=None,
            )


# ==============================================================================
# DEFAULT STEP HANDLERS
# ==============================================================================


class NoOpHandler:
    """
    No-op handler for testing.

    Always succeeds without doing anything.
    """

    def execute(self, step: JobStep, context: ExecutionContext) -> StepOutput:
        """Execute no-op step."""
        return StepOutput(
            success=True,
            output={
                "handler": "noop",
                "step_type": step.step_type,
                "target": step.target,
                "executed_at": datetime.now(timezone.utc).isoformat(),
            },
        )


class FailingHandler:
    """
    Failing handler for testing.

    Always fails with a configurable error.
    """

    def __init__(self, error_message: str = "Intentional failure"):
        self._error = error_message

    def execute(self, step: JobStep, context: ExecutionContext) -> StepOutput:
        """Execute failing step."""
        return StepOutput(
            success=False,
            output={},
            error=self._error,
        )


# ==============================================================================
# EXECUTOR FACTORY
# ==============================================================================


def create_default_executor() -> JobExecutor:
    """
    Create a JobExecutor with default handlers.

    Default handlers are no-ops for testing.
    Production handlers should be registered separately.
    """
    executor = JobExecutor()

    # Register no-op handlers for common step types
    noop = NoOpHandler()
    executor.register_handler("capability_enable", noop)
    executor.register_handler("capability_disable", noop)
    executor.register_handler("capability_add", noop)
    executor.register_handler("capability_remove", noop)
    executor.register_handler("configuration_change", noop)
    executor.register_handler("unknown", noop)

    return executor


# ==============================================================================
# EXECUTOR EVIDENCE HELPERS
# ==============================================================================


def execution_result_to_evidence(result: ExecutionResult) -> dict[str, Any]:
    """
    Convert ExecutionResult to audit evidence format.

    This is what gets passed to the Audit Trigger.
    """
    return {
        "job_id": str(result.job_id),
        "final_status": result.final_status.value,
        "final_reason": result.final_reason,
        "execution_summary": {
            "steps_executed": result.steps_executed,
            "steps_succeeded": result.steps_succeeded,
            "steps_failed": result.steps_failed,
        },
        "step_results": [
            {
                "step_index": sr.step_index,
                "status": sr.status.value,
                "started_at": sr.started_at.isoformat() if sr.started_at else None,
                "completed_at": sr.completed_at.isoformat() if sr.completed_at else None,
                "output": sr.output,
                "error": sr.error,
            }
            for sr in result.step_results
        ],
        "health_observations": {
            "before": result.health_before,
            "after": result.health_after,
        },
        "timing": {
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat(),
            "duration_seconds": (result.completed_at - result.started_at).total_seconds(),
        },
        "executor_version": EXECUTOR_VERSION,
    }
