# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: worker-pool
#   Execution: sync-over-async
# Role: Run Orchestration Kernel - Single authority for run lifecycle
# Callers: WorkerPool (L5), RunRunner (L5)
# Allowed Imports: L4 (via facades only), L6
# Forbidden Imports: L1, L2, L3, L4 engines directly
# Reference: PIN-454 (Cross-Domain Orchestration Audit), Section 8.1

"""
Run Orchestration Kernel (ROK)

The ROK is the single authority for run lifecycle management. It:

1. Manages phase transitions (CREATED → AUTHORIZED → EXECUTING → ...)
2. Declares audit expectations at T0 (run start)
3. Coordinates governance checks across domains
4. Emits finalize_run acknowledgment when complete

Architecture:

    ┌──────────────────────────────────────────────────────────────────┐
    │                    Run Orchestration Kernel (ROK)                │
    │                         L5: Execution                            │
    ├──────────────────────────────────────────────────────────────────┤
    │  STATE MACHINE:                                                  │
    │  CREATED → AUTHORIZED → EXECUTING → GOVERNANCE_CHECK             │
    │                                    → FINALIZING → COMPLETED/FAILED│
    │                                                                  │
    │  DOMAIN COORDINATION (via L4 Facades):                           │
    │  ├─ IncidentFacade    → incident creation                        │
    │  ├─ GovernanceFacade  → policy evaluation, lessons               │
    │  └─ TraceFacade       → observability                            │
    │                                                                  │
    │  INVARIANTS:                                                     │
    │  • Every run transition emits AuditExpectation                   │
    │  • GOVERNANCE_CHECK is mandatory before FINALIZING               │
    │  • No direct engine calls — facades only                         │
    │  • run_id is the correlation key across all domains              │
    └──────────────────────────────────────────────────────────────────┘

Usage:

    kernel = RunOrchestrationKernel(run_id)

    # Declare expectations at run start (T0)
    kernel.declare_expectations()

    # Execute through phases
    kernel.authorize()
    kernel.begin_execution()

    # ... runner executes skills ...

    # Governance check (blocks until all acks received or timeout)
    kernel.governance_check()

    # Finalize
    kernel.finalize()
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.worker.orchestration.phases import (
    PhaseStateMachine,
    PhaseTransitionError,
    RunPhase,
)

logger = logging.getLogger("nova.worker.orchestration.rok")

# Configuration
RAC_ENABLED = os.getenv("RAC_ENABLED", "true").lower() == "true"
GOVERNANCE_TIMEOUT_MS = int(os.getenv("ROK_GOVERNANCE_TIMEOUT_MS", "5000"))
DEFAULT_RUN_TIMEOUT_MS = int(os.getenv("ROK_DEFAULT_RUN_TIMEOUT_MS", "30000"))
GRACE_PERIOD_MS = int(os.getenv("ROK_GRACE_PERIOD_MS", "5000"))


class GovernanceCheckError(Exception):
    """Raised when governance check fails."""

    def __init__(self, message: str, missing_acks: Optional[list] = None):
        super().__init__(message)
        self.missing_acks = missing_acks or []


class RunOrchestrationKernel:
    """
    Single authority for run lifecycle management.

    Coordinates:
    - Phase state machine
    - Audit expectation/acknowledgment flow
    - Governance checks across domains

    Layer: L5 (Execution)
    Callers: WorkerPool, RunRunner
    """

    def __init__(
        self,
        run_id: str,
        tenant_id: Optional[str] = None,
        run_timeout_ms: int = DEFAULT_RUN_TIMEOUT_MS,
    ):
        """
        Initialize the Run Orchestration Kernel.

        Args:
            run_id: The run ID to orchestrate
            tenant_id: Tenant scope (optional, loaded from run if not provided)
            run_timeout_ms: Expected run duration for deadline calculation
        """
        self._run_id = UUID(run_id)
        self._tenant_id = tenant_id
        self._run_timeout_ms = run_timeout_ms
        self._state_machine = PhaseStateMachine(self._run_id)
        self._expectations_declared = False
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None

    @property
    def run_id(self) -> UUID:
        """Run ID."""
        return self._run_id

    @property
    def phase(self) -> RunPhase:
        """Current phase."""
        return self._state_machine.phase

    @property
    def is_terminal(self) -> bool:
        """Check if in terminal phase."""
        return self._state_machine.context.is_terminal()

    # =========================================================================
    # Expectation Declaration (T0)
    # =========================================================================

    def declare_expectations(self) -> None:
        """
        Declare audit expectations at T0 (run start).

        This MUST be called before execution begins. It registers
        what MUST happen during this run for audit reconciliation.

        PIN-454: Creates expectations for:
        - INCIDENTS / create_incident
        - POLICIES / evaluate_policy
        - LOGS / start_trace
        - ORCHESTRATOR / finalize_run (liveness guarantee)
        """
        if self._expectations_declared:
            logger.warning(
                "rok.expectations_already_declared",
                extra={"run_id": str(self._run_id)},
            )
            return

        if not RAC_ENABLED:
            logger.debug(
                "rok.rac_disabled_skipping_expectations",
                extra={"run_id": str(self._run_id)},
            )
            self._expectations_declared = True
            return

        try:
            # L5 imports (migrated to HOC per SWEEP-04)
            from app.hoc.cus.logs.L5_schemas.audit_models import create_run_expectations
            from app.hoc.cus.general.L5_engines.audit_store import get_audit_store

            expectations = create_run_expectations(
                run_id=self._run_id,
                run_timeout_ms=self._run_timeout_ms,
                grace_period_ms=GRACE_PERIOD_MS,
            )

            store = get_audit_store()
            store.add_expectations(self._run_id, expectations)

            self._expectations_declared = True
            self._started_at = datetime.now(timezone.utc)

            logger.info(
                "rok.expectations_declared",
                extra={
                    "run_id": str(self._run_id),
                    "expectation_count": len(expectations),
                    "domains": [e.domain.value for e in expectations],
                },
            )

        except Exception as e:
            # RAC failures should not block execution
            logger.warning(
                f"rok.expectation_declaration_failed: {e}",
                extra={"run_id": str(self._run_id)},
            )
            self._expectations_declared = True  # Mark as done to avoid retry

    # =========================================================================
    # Phase Transitions
    # =========================================================================

    def authorize(self, authorization_decision: str = "GRANTED") -> bool:
        """
        Transition to AUTHORIZED phase.

        Args:
            authorization_decision: Authorization result from L6

        Returns:
            True if authorized, False if denied
        """
        if authorization_decision != "GRANTED":
            self._state_machine.fail(
                f"Authorization {authorization_decision}",
                authorization_decision=authorization_decision,
            )
            return False

        try:
            self._state_machine.transition_to(
                RunPhase.AUTHORIZED,
                reason="Authorization granted",
            )
            return True
        except PhaseTransitionError as e:
            logger.error(
                "rok.authorize_transition_failed",
                extra={"run_id": str(self._run_id), "error": str(e)},
            )
            return False

    def begin_execution(self) -> bool:
        """
        Transition to EXECUTING phase.

        Returns:
            True if transition successful
        """
        try:
            self._state_machine.transition_to(
                RunPhase.EXECUTING,
                reason="Execution starting",
            )
            return True
        except PhaseTransitionError as e:
            logger.error(
                "rok.begin_execution_failed",
                extra={"run_id": str(self._run_id), "error": str(e)},
            )
            return False

    def execution_complete(self, success: bool, error: Optional[str] = None) -> bool:
        """
        Signal execution complete, transition to GOVERNANCE_CHECK.

        Args:
            success: Whether execution succeeded
            error: Error message if failed

        Returns:
            True if transition successful
        """
        if not success and error:
            # Still go to GOVERNANCE_CHECK to create incident/policy records
            # The actual failure will be recorded in those records
            pass

        try:
            self._state_machine.transition_to(
                RunPhase.GOVERNANCE_CHECK,
                reason="Execution complete, starting governance check",
                execution_success=success,
                execution_error=error,
            )
            return True
        except PhaseTransitionError as e:
            logger.error(
                "rok.execution_complete_failed",
                extra={"run_id": str(self._run_id), "error": str(e)},
            )
            return False

    # =========================================================================
    # Governance Check
    # =========================================================================

    def governance_check(
        self,
        timeout_ms: int = GOVERNANCE_TIMEOUT_MS,
        require_all_acks: bool = False,
    ) -> bool:
        """
        Perform governance check.

        This verifies that all expected domain operations have completed
        by checking the RAC ack store.

        Args:
            timeout_ms: Maximum time to wait for acks (reserved for future async wait)
            require_all_acks: If True, fail if any acks missing (strict mode)

        Returns:
            True if governance check passed
        """
        # Note: timeout_ms is reserved for future async wait implementation
        _ = timeout_ms  # Acknowledge parameter for future use

        if self.phase != RunPhase.GOVERNANCE_CHECK:
            logger.warning(
                "rok.governance_check_wrong_phase",
                extra={"run_id": str(self._run_id), "phase": self.phase.value},
            )
            return False

        if not RAC_ENABLED:
            logger.debug(
                "rok.rac_disabled_skipping_governance_check",
                extra={"run_id": str(self._run_id)},
            )
            return True

        try:
            # L5 import (migrated to HOC per SWEEP-04)
            from app.hoc.cus.logs.L5_engines.audit_reconciler import get_audit_reconciler

            reconciler = get_audit_reconciler()
            result = reconciler.reconcile(self._run_id)

            # Update state machine with governance results
            self._state_machine.mark_governance_check(
                incident_created=not any(
                    d == "incidents" and a == "create_incident"
                    for d, a in result.missing_actions
                ),
                policy_evaluated=not any(
                    d == "policies" and a == "evaluate_policy"
                    for d, a in result.missing_actions
                ),
                trace_completed=not any(
                    d == "logs" and a == "start_trace"
                    for d, a in result.missing_actions
                ),
            )

            logger.info(
                "rok.governance_check_result",
                extra={
                    "run_id": str(self._run_id),
                    "status": result.status,
                    "missing_count": len(result.missing_actions),
                    "drift_count": len(result.drift_actions),
                    "is_clean": result.is_clean,
                },
            )

            if require_all_acks and result.has_missing:
                raise GovernanceCheckError(
                    f"Missing acks: {result.missing_actions}",
                    missing_acks=result.missing_actions,
                )

            return True

        except GovernanceCheckError:
            raise
        except Exception as e:
            logger.warning(
                f"rok.governance_check_failed: {e}",
                extra={"run_id": str(self._run_id)},
            )
            # Don't fail the run for RAC check failures
            return True

    def begin_finalization(self) -> bool:
        """
        Transition to FINALIZING phase.

        Returns:
            True if transition successful
        """
        try:
            self._state_machine.transition_to(
                RunPhase.FINALIZING,
                reason="Governance check complete, finalizing",
            )
            return True
        except PhaseTransitionError as e:
            logger.error(
                "rok.begin_finalization_failed",
                extra={"run_id": str(self._run_id), "error": str(e)},
            )
            return False

    # =========================================================================
    # Finalization
    # =========================================================================

    def finalize(self, success: bool = True, error: Optional[str] = None) -> bool:
        """
        Finalize the run and emit finalize_run acknowledgment.

        This is the terminal operation. After this:
        - Run is in COMPLETED or FAILED state
        - finalize_run ack is emitted (liveness proof)
        - Audit store can be cleaned up

        Args:
            success: Whether the run succeeded
            error: Error message if failed

        Returns:
            True if finalization successful
        """
        self._completed_at = datetime.now(timezone.utc)

        try:
            if success:
                self._state_machine.transition_to(
                    RunPhase.COMPLETED,
                    reason="Run completed successfully",
                )
            else:
                self._state_machine.fail(error or "Unknown error")

            # Emit finalize_run ack (liveness proof)
            self._emit_finalize_ack(success, error)

            logger.info(
                "rok.finalized",
                extra={
                    "run_id": str(self._run_id),
                    "final_phase": self.phase.value,
                    "success": success,
                    "duration_ms": self._calculate_duration_ms(),
                },
            )

            return True

        except PhaseTransitionError as e:
            logger.error(
                "rok.finalize_failed",
                extra={"run_id": str(self._run_id), "error": str(e)},
            )
            return False

    def fail(self, error: str) -> bool:
        """
        Fail the run from any phase.

        Args:
            error: Error message

        Returns:
            True if transition successful
        """
        try:
            self._state_machine.fail(error)
            self._completed_at = datetime.now(timezone.utc)

            # Emit finalize_run ack with error
            self._emit_finalize_ack(success=False, error=error)

            logger.info(
                "rok.failed",
                extra={
                    "run_id": str(self._run_id),
                    "error": error,
                    "from_phase": self._state_machine.context.transitions[-1].from_phase.value
                    if self._state_machine.context.transitions
                    else "unknown",
                },
            )

            return True
        except PhaseTransitionError as e:
            logger.error(
                "rok.fail_transition_failed",
                extra={"run_id": str(self._run_id), "error": str(e)},
            )
            return False

    # =========================================================================
    # Internal Methods
    # =========================================================================

    def _emit_finalize_ack(self, success: bool, error: Optional[str]) -> None:
        """
        Emit the finalize_run acknowledgment.

        This is the liveness proof — it proves the run completed
        (successfully or not).
        """
        if not RAC_ENABLED:
            return

        try:
            # L5 imports (migrated to HOC per SWEEP-04)
            from app.hoc.cus.logs.L5_schemas.audit_models import AuditAction, AuditDomain, DomainAck
            from app.hoc.cus.general.L5_engines.audit_store import get_audit_store

            ack = DomainAck(
                run_id=self._run_id,
                domain=AuditDomain.ORCHESTRATOR,
                action=AuditAction.FINALIZE_RUN,
                result_id=str(self._run_id) if success else None,
                error=error,
            )

            store = get_audit_store()
            store.add_ack(self._run_id, ack)

            logger.debug(
                "rok.finalize_ack_emitted",
                extra={
                    "run_id": str(self._run_id),
                    "success": success,
                },
            )

        except Exception as e:
            logger.warning(f"rok.finalize_ack_failed: {e}")

    def _calculate_duration_ms(self) -> int:
        """Calculate run duration in milliseconds."""
        if not self._started_at or not self._completed_at:
            return 0
        delta = self._completed_at - self._started_at
        return int(delta.total_seconds() * 1000)

    def get_context(self) -> dict:
        """Get orchestration context for logging/debugging."""
        return {
            "run_id": str(self._run_id),
            "phase": self.phase.value,
            "expectations_declared": self._expectations_declared,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
            "transitions": [t.to_dict() for t in self._state_machine.get_history()],
            "governance": {
                "incident_created": self._state_machine.context.incident_created,
                "policy_evaluated": self._state_machine.context.policy_evaluated,
                "trace_completed": self._state_machine.context.trace_completed,
                "all_acks_received": self._state_machine.context.all_acks_received,
            },
        }


# =============================================================================
# Factory Function
# =============================================================================


def create_rok(
    run_id: str,
    tenant_id: Optional[str] = None,
    run_timeout_ms: int = DEFAULT_RUN_TIMEOUT_MS,
) -> RunOrchestrationKernel:
    """
    Factory function for RunOrchestrationKernel.

    Args:
        run_id: The run ID to orchestrate
        tenant_id: Tenant scope (optional)
        run_timeout_ms: Expected run duration

    Returns:
        RunOrchestrationKernel instance
    """
    return RunOrchestrationKernel(
        run_id=run_id,
        tenant_id=tenant_id,
        run_timeout_ms=run_timeout_ms,
    )
