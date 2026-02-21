# capability_id: CAP-012
# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Run Orchestration Kernel phase definitions and state machine
# Callers: RunOrchestrationKernel (L5)
# Allowed Imports: L6 (stdlib only)
# Forbidden Imports: L1, L2, L3, L4
# Reference: PIN-454 (Cross-Domain Orchestration Audit), Section 8.1

"""
ROK Phase State Machine

Defines the phases a run goes through during execution:

    CREATED → AUTHORIZED → EXECUTING → GOVERNANCE_CHECK → FINALIZING → COMPLETED/FAILED

Each phase has:
- Entry conditions (what must be true to enter)
- Exit conditions (what must be true to exit)
- Failure modes (what happens if something goes wrong)

Design Principles:
1. Every phase transition is auditable
2. GOVERNANCE_CHECK is mandatory before FINALIZING
3. run_id is the correlation key across all phases
4. Phases are immutable once transitioned
5. Phase-Status invariants are enforced at every transition (PIN-454)
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set
from uuid import UUID

logger = logging.getLogger("nova.worker.orchestration.phases")


class RunPhase(str, Enum):
    """
    Phases of run execution.

    Order is enforced by ROK — no phase can be skipped.
    """

    # Initial phase after POST /runs
    CREATED = "CREATED"

    # Authorization computed and verified
    AUTHORIZED = "AUTHORIZED"

    # Skills are being executed
    EXECUTING = "EXECUTING"

    # Execution complete, governance checks in progress
    GOVERNANCE_CHECK = "GOVERNANCE_CHECK"

    # Governance passed, finalizing run state
    FINALIZING = "FINALIZING"

    # Terminal phases
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PhaseTransitionError(Exception):
    """Raised when an invalid phase transition is attempted."""

    def __init__(self, from_phase: RunPhase, to_phase: RunPhase, reason: str):
        self.from_phase = from_phase
        self.to_phase = to_phase
        self.reason = reason
        super().__init__(f"Invalid transition {from_phase} → {to_phase}: {reason}")


class PhaseStatusInvariantError(Exception):
    """
    Raised when a phase-status invariant is violated.

    Per PIN-454: "If a run is in phase X, then the only allowed statuses are Y, Z."
    This ensures phase and status are always consistent.
    """

    def __init__(
        self,
        phase: RunPhase,
        status: str,
        allowed_statuses: FrozenSet[str],
    ):
        self.phase = phase
        self.status = status
        self.allowed_statuses = allowed_statuses
        allowed_list = ", ".join(sorted(allowed_statuses))
        super().__init__(
            f"Phase-status invariant violated: Phase {phase.value} does not allow "
            f"status '{status}'. Allowed statuses: [{allowed_list}]"
        )


# =============================================================================
# Phase-Status Invariants (PIN-454 Section 3.1)
# =============================================================================
#
# These invariants define which run statuses are valid for each phase.
# Violations indicate a bug in the orchestration logic.
#
# Design notes:
# - CREATED/AUTHORIZED: Run is queued, waiting for processing
# - EXECUTING: Run is actively executing skills
# - GOVERNANCE_CHECK/FINALIZING: Run is still "running" during governance/finalization
# - COMPLETED: Run succeeded
# - FAILED: Run ended in any failure state (failed, policy violation, cancelled, retry)

PHASE_STATUS_INVARIANTS: Dict[RunPhase, FrozenSet[str]] = {
    # Initial phases: run is queued
    RunPhase.CREATED: frozenset({"queued"}),
    RunPhase.AUTHORIZED: frozenset({"queued"}),

    # Active phases: run is executing or in governance
    RunPhase.EXECUTING: frozenset({"running"}),
    RunPhase.GOVERNANCE_CHECK: frozenset({"running"}),
    RunPhase.FINALIZING: frozenset({"running"}),

    # Terminal success
    RunPhase.COMPLETED: frozenset({"succeeded"}),

    # Terminal failure: any error state
    RunPhase.FAILED: frozenset({"failed", "failed_policy", "cancelled", "retry"}),
}

# Feature flag for invariant enforcement
PHASE_STATUS_INVARIANT_ENFORCE = os.getenv(
    "PHASE_STATUS_INVARIANT_ENFORCE", "true"
).lower() == "true"


def assert_phase_status_invariant(
    phase: RunPhase,
    status: str,
    run_id: Optional[UUID] = None,
    raise_on_violation: bool = True,
) -> bool:
    """
    Assert that a phase-status combination is valid.

    Per PIN-454 Section 3.1: Phase vs Status Consistency Contract.
    This should be called at every phase transition to ensure invariants hold.

    Args:
        phase: Current or target phase
        status: Current run status
        run_id: Optional run ID for logging
        raise_on_violation: If True, raise exception on violation; if False, log warning

    Returns:
        True if invariant holds, False if violated (when raise_on_violation=False)

    Raises:
        PhaseStatusInvariantError: If invariant violated and raise_on_violation=True
    """
    allowed_statuses = PHASE_STATUS_INVARIANTS.get(phase)
    if allowed_statuses is None:
        logger.warning(
            "rok.unknown_phase_for_invariant",
            extra={"phase": phase.value, "run_id": str(run_id) if run_id else None},
        )
        return True  # Unknown phase, can't validate

    if status not in allowed_statuses:
        logger.error(
            "rok.phase_status_invariant_violated",
            extra={
                "phase": phase.value,
                "status": status,
                "allowed_statuses": list(allowed_statuses),
                "run_id": str(run_id) if run_id else None,
            },
        )

        if raise_on_violation and PHASE_STATUS_INVARIANT_ENFORCE:
            raise PhaseStatusInvariantError(phase, status, allowed_statuses)
        return False

    return True


def get_expected_statuses_for_phase(phase: RunPhase) -> FrozenSet[str]:
    """
    Get the valid run statuses for a given phase.

    Args:
        phase: The phase to query

    Returns:
        Frozenset of valid status strings
    """
    return PHASE_STATUS_INVARIANTS.get(phase, frozenset())


# Valid phase transitions
VALID_TRANSITIONS: Dict[RunPhase, List[RunPhase]] = {
    RunPhase.CREATED: [RunPhase.AUTHORIZED, RunPhase.FAILED],
    RunPhase.AUTHORIZED: [RunPhase.EXECUTING, RunPhase.FAILED],
    RunPhase.EXECUTING: [RunPhase.GOVERNANCE_CHECK, RunPhase.FAILED],
    RunPhase.GOVERNANCE_CHECK: [RunPhase.FINALIZING, RunPhase.FAILED],
    RunPhase.FINALIZING: [RunPhase.COMPLETED, RunPhase.FAILED],
    RunPhase.COMPLETED: [],  # Terminal
    RunPhase.FAILED: [],  # Terminal
}


@dataclass
class PhaseTransition:
    """
    Record of a phase transition.

    Immutable after creation — provides audit trail for run lifecycle.
    """

    from_phase: RunPhase
    to_phase: RunPhase
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage/logging."""
        return {
            "from_phase": self.from_phase.value,
            "to_phase": self.to_phase.value,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
            "metadata": self.metadata,
        }


@dataclass
class PhaseContext:
    """
    Context for the current phase.

    Provides information needed for phase execution and transition decisions.
    """

    run_id: UUID
    current_phase: RunPhase
    entered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None
    transitions: List[PhaseTransition] = field(default_factory=list)

    # Run status tracking (for phase-status invariant assertions)
    run_status: Optional[str] = None

    # Governance check results (populated during GOVERNANCE_CHECK)
    incident_created: bool = False
    policy_evaluated: bool = False
    trace_completed: bool = False
    all_acks_received: bool = False

    def can_transition_to(self, target: RunPhase) -> bool:
        """Check if transition to target phase is valid."""
        valid_targets = VALID_TRANSITIONS.get(self.current_phase, [])
        return target in valid_targets

    def is_terminal(self) -> bool:
        """Check if current phase is terminal."""
        return self.current_phase in (RunPhase.COMPLETED, RunPhase.FAILED)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage/logging."""
        return {
            "run_id": str(self.run_id),
            "current_phase": self.current_phase.value,
            "entered_at": self.entered_at.isoformat(),
            "error": self.error,
            "run_status": self.run_status,
            "transitions": [t.to_dict() for t in self.transitions],
            "incident_created": self.incident_created,
            "policy_evaluated": self.policy_evaluated,
            "trace_completed": self.trace_completed,
            "all_acks_received": self.all_acks_received,
        }


class PhaseStateMachine:
    """
    State machine for run phase transitions.

    Enforces valid transitions and records history.

    Layer: L5 (Execution)
    """

    def __init__(self, run_id: UUID, initial_phase: RunPhase = RunPhase.CREATED):
        """
        Initialize state machine.

        Args:
            run_id: The run being tracked
            initial_phase: Starting phase (default: CREATED)
        """
        self._context = PhaseContext(
            run_id=run_id,
            current_phase=initial_phase,
        )

    @property
    def phase(self) -> RunPhase:
        """Current phase."""
        return self._context.current_phase

    @property
    def context(self) -> PhaseContext:
        """Phase context (read-only)."""
        return self._context

    @property
    def run_id(self) -> UUID:
        """Run ID."""
        return self._context.run_id

    def transition_to(
        self,
        target: RunPhase,
        reason: Optional[str] = None,
        run_status: Optional[str] = None,
        **metadata: Any,
    ) -> PhaseTransition:
        """
        Transition to a new phase.

        Args:
            target: Target phase
            reason: Human-readable reason for transition
            run_status: Optional run status to validate phase-status invariant.
                If provided, asserts that the target phase allows this status.
            **metadata: Additional context for the transition

        Returns:
            PhaseTransition record

        Raises:
            PhaseTransitionError: If transition is invalid
            PhaseStatusInvariantError: If phase-status invariant violated
        """
        if not self._context.can_transition_to(target):
            raise PhaseTransitionError(
                self._context.current_phase,
                target,
                f"Not a valid transition from {self._context.current_phase}",
            )

        # Assert phase-status invariant if run_status provided
        if run_status is not None:
            assert_phase_status_invariant(
                phase=target,
                status=run_status,
                run_id=self._context.run_id,
                raise_on_violation=True,
            )
            # Update context with new run_status
            self._context.run_status = run_status

        # Create transition record
        transition = PhaseTransition(
            from_phase=self._context.current_phase,
            to_phase=target,
            reason=reason,
            metadata=dict(metadata),
        )

        # Update context
        self._context.transitions.append(transition)
        self._context.current_phase = target
        self._context.entered_at = transition.timestamp

        logger.info(
            "rok.phase_transition",
            extra={
                "run_id": str(self._context.run_id),
                "from_phase": transition.from_phase.value,
                "to_phase": transition.to_phase.value,
                "run_status": run_status,
                "reason": reason,
            },
        )

        return transition

    def fail(
        self,
        error: str,
        run_status: Optional[str] = None,
        **metadata: Any,
    ) -> PhaseTransition:
        """
        Transition to FAILED state.

        This is always valid from any non-terminal phase.

        Args:
            error: Error message
            run_status: Optional run status for phase-status invariant assertion.
                Valid values for FAILED phase: "failed", "failed_policy", "cancelled", "retry"
            **metadata: Additional context

        Returns:
            PhaseTransition record

        Raises:
            PhaseTransitionError: If already in terminal phase
            PhaseStatusInvariantError: If run_status not valid for FAILED phase
        """
        if self._context.is_terminal():
            raise PhaseTransitionError(
                self._context.current_phase,
                RunPhase.FAILED,
                "Cannot fail from terminal phase",
            )

        self._context.error = error
        return self.transition_to(
            RunPhase.FAILED,
            reason=f"Error: {error}",
            run_status=run_status,
            error=error,
            **metadata,
        )

    def set_run_status(self, status: str) -> None:
        """
        Update the run status and validate phase-status invariant.

        This should be called when run status changes outside of phase transitions.

        Args:
            status: The new run status

        Raises:
            PhaseStatusInvariantError: If status not valid for current phase
        """
        assert_phase_status_invariant(
            phase=self._context.current_phase,
            status=status,
            run_id=self._context.run_id,
            raise_on_violation=True,
        )
        self._context.run_status = status

        logger.debug(
            "rok.run_status_updated",
            extra={
                "run_id": str(self._context.run_id),
                "phase": self._context.current_phase.value,
                "run_status": status,
            },
        )

    def mark_governance_check(
        self,
        incident_created: bool = False,
        policy_evaluated: bool = False,
        trace_completed: bool = False,
    ) -> None:
        """
        Update governance check status.

        Called during GOVERNANCE_CHECK phase to track which
        domain operations have completed.
        """
        if incident_created:
            self._context.incident_created = True
        if policy_evaluated:
            self._context.policy_evaluated = True
        if trace_completed:
            self._context.trace_completed = True

        # Check if all governance acks received
        self._context.all_acks_received = (
            self._context.incident_created
            and self._context.policy_evaluated
            and self._context.trace_completed
        )

    def get_history(self) -> List[PhaseTransition]:
        """Get transition history."""
        return list(self._context.transitions)


# Phase-specific entry/exit conditions
PHASE_CONDITIONS = {
    RunPhase.CREATED: {
        "entry": "Run record exists in database",
        "exit": "Authorization decision computed",
        "failure": "Invalid run data or system error",
    },
    RunPhase.AUTHORIZED: {
        "entry": "Authorization decision = GRANTED",
        "exit": "Worker claims run, begins execution",
        "failure": "Authorization DENIED or PENDING",
    },
    RunPhase.EXECUTING: {
        "entry": "Worker has claimed run",
        "exit": "All skills complete (success or error)",
        "failure": "Skill execution error, budget exceeded, timeout",
    },
    RunPhase.GOVERNANCE_CHECK: {
        "entry": "Execution complete (any outcome)",
        "exit": "All domain acks received",
        "failure": "Governance timeout, missing acks",
    },
    RunPhase.FINALIZING: {
        "entry": "All governance checks passed",
        "exit": "DB commit + events published",
        "failure": "Commit error, event publish error",
    },
    RunPhase.COMPLETED: {
        "entry": "Finalization successful",
        "exit": "N/A (terminal)",
        "failure": "N/A (terminal)",
    },
    RunPhase.FAILED: {
        "entry": "Error at any phase",
        "exit": "N/A (terminal)",
        "failure": "N/A (terminal)",
    },
}
