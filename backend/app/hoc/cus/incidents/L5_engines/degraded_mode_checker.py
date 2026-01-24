# Layer: L5 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api/worker
#   Execution: sync
# Role: Governance degraded mode checker with incident response
# Callers: ROK (L5), prevention_engine, incident_engine
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: GAP-070 (Governance Degraded Mode)

"""
Module: degraded_mode_checker
Purpose: Check and manage governance degraded mode with incident integration.

When governance systems are unavailable or degraded, this module:
    - Tracks the degraded state with proper metadata
    - Creates incidents for degraded mode transitions
    - Enforces degraded mode rules (block new runs, warn existing)
    - Integrates with incident response for visibility

Degraded Mode States:
    - NORMAL: Governance is fully operational
    - DEGRADED: Governance is partially unavailable
    - CRITICAL: Governance is fully unavailable (block all)

Exports:
    - GovernanceDegradedModeError: Raised when degraded mode blocks operation
    - GovernanceDegradedModeChecker: Main checker class
    - DegradedModeIncidentCreator: Creates incidents for degraded mode
    - check_degraded_mode: Quick helper function
    - enter_degraded_with_incident: Enter degraded mode with incident
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Dict, FrozenSet, Optional
import logging

logger = logging.getLogger("nova.governance.degraded_mode")


class DegradedModeCheckResult(str, Enum):
    """Result of a degraded mode check."""

    NORMAL = "normal"  # Governance is fully operational
    DEGRADED = "degraded"  # Governance is partially available
    CRITICAL = "critical"  # Governance is fully unavailable
    CHECK_DISABLED = "check_disabled"  # Degraded mode checking is disabled


class DegradedModeState(str, Enum):
    """Possible degraded mode states."""

    NORMAL = "NORMAL"  # Fully operational
    DEGRADED = "DEGRADED"  # Partially available
    CRITICAL = "CRITICAL"  # Fully unavailable


# Actions for runs when in degraded mode
DEGRADED_MODE_ACTIONS: FrozenSet[str] = frozenset({
    "ALLOW",  # Allow runs to continue
    "WARN",  # Allow with warning
    "BLOCK",  # Block the operation
})


class GovernanceDegradedModeError(Exception):
    """
    Raised when governance degraded mode blocks an operation.

    This error indicates that governance is in a degraded state
    and the requested operation cannot be performed.
    """

    def __init__(
        self,
        message: str,
        state: DegradedModeState,
        operation: str,
        degraded_since: Optional[str],
        degraded_reason: Optional[str],
    ):
        super().__init__(message)
        self.state = state
        self.operation = operation
        self.degraded_since = degraded_since
        self.degraded_reason = degraded_reason

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/API responses."""
        return {
            "error": "GovernanceDegradedModeError",
            "message": str(self),
            "state": self.state.value,
            "operation": self.operation,
            "degraded_since": self.degraded_since,
            "degraded_reason": self.degraded_reason,
        }


@dataclass
class DegradedModeStatus:
    """Current degraded mode status."""

    state: DegradedModeState
    reason: Optional[str] = None
    entered_by: Optional[str] = None
    entered_at: Optional[str] = None
    new_runs_action: str = "BLOCK"  # What to do with new runs
    existing_runs_action: str = "WARN"  # What to do with in-flight runs
    incident_id: Optional[str] = None  # Incident created for this transition

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "state": self.state.value,
            "reason": self.reason,
            "entered_by": self.entered_by,
            "entered_at": self.entered_at,
            "new_runs_action": self.new_runs_action,
            "existing_runs_action": self.existing_runs_action,
            "incident_id": self.incident_id,
        }


@dataclass
class DegradedModeCheckResponse:
    """Response from a degraded mode check."""

    result: DegradedModeCheckResult
    is_degraded: bool
    check_enabled: bool
    state: DegradedModeState
    new_runs_action: str
    existing_runs_action: str
    message: str
    degraded_since: Optional[str] = None
    degraded_reason: Optional[str] = None
    incident_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "result": self.result.value,
            "is_degraded": self.is_degraded,
            "check_enabled": self.check_enabled,
            "state": self.state.value,
            "new_runs_action": self.new_runs_action,
            "existing_runs_action": self.existing_runs_action,
            "message": self.message,
            "degraded_since": self.degraded_since,
            "degraded_reason": self.degraded_reason,
            "incident_id": self.incident_id,
        }


@dataclass
class DegradedModeIncident:
    """Incident data for degraded mode transition."""

    incident_id: str
    tenant_id: str
    title: str
    description: str
    severity: str
    source: str
    degraded_state: DegradedModeState
    created_at: str


class DegradedModeIncidentCreator:
    """
    Creates incidents for degraded mode transitions.

    When governance enters or exits degraded mode, an incident
    is created to provide visibility and audit trail.
    """

    def __init__(self, tenant_id: str = "system"):
        """
        Initialize the incident creator.

        Args:
            tenant_id: Default tenant ID for incidents
        """
        self._tenant_id = tenant_id

    def create_degraded_incident(
        self,
        state: DegradedModeState,
        reason: str,
        entered_by: str,
    ) -> DegradedModeIncident:
        """
        Create an incident for entering degraded mode.

        Args:
            state: The degraded mode state being entered
            reason: Reason for entering degraded mode
            entered_by: Who/what triggered the transition

        Returns:
            DegradedModeIncident with incident details
        """
        import uuid

        incident_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        severity = "HIGH" if state == DegradedModeState.CRITICAL else "MEDIUM"
        title = f"Governance {state.value} Mode Entered"
        description = (
            f"Governance system entered {state.value} mode.\n\n"
            f"Reason: {reason}\n"
            f"Triggered by: {entered_by}\n"
            f"Time: {now}\n\n"
            f"Impact:\n"
            f"- New runs may be blocked or degraded\n"
            f"- Existing runs continue with warnings\n"
            f"- Policy enforcement may be limited"
        )

        incident = DegradedModeIncident(
            incident_id=incident_id,
            tenant_id=self._tenant_id,
            title=title,
            description=description,
            severity=severity,
            source="governance_degraded_mode",
            degraded_state=state,
            created_at=now,
        )

        logger.warning(
            "degraded_mode_incident_created",
            extra={
                "incident_id": incident_id,
                "state": state.value,
                "reason": reason,
                "severity": severity,
            },
        )

        return incident

    def create_recovery_incident(
        self,
        previous_state: DegradedModeState,
        recovered_by: str,
        duration_seconds: Optional[int] = None,
    ) -> DegradedModeIncident:
        """
        Create an incident for exiting degraded mode (recovery).

        Args:
            previous_state: The degraded mode state being exited
            recovered_by: Who/what triggered the recovery
            duration_seconds: How long system was in degraded mode

        Returns:
            DegradedModeIncident with incident details
        """
        import uuid

        incident_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        duration_str = f"{duration_seconds}s" if duration_seconds else "unknown"
        title = f"Governance Recovered from {previous_state.value} Mode"
        description = (
            f"Governance system recovered from {previous_state.value} mode.\n\n"
            f"Recovered by: {recovered_by}\n"
            f"Duration in degraded mode: {duration_str}\n"
            f"Recovery time: {now}\n\n"
            f"All governance functions restored."
        )

        incident = DegradedModeIncident(
            incident_id=incident_id,
            tenant_id=self._tenant_id,
            title=title,
            description=description,
            severity="LOW",
            source="governance_degraded_mode",
            degraded_state=DegradedModeState.NORMAL,
            created_at=now,
        )

        logger.info(
            "degraded_mode_recovery_incident_created",
            extra={
                "incident_id": incident_id,
                "previous_state": previous_state.value,
                "duration_seconds": duration_seconds,
            },
        )

        return incident


# Global state with thread safety
_state_lock = Lock()
_current_status: Optional[DegradedModeStatus] = None


class GovernanceDegradedModeChecker:
    """
    Checks and manages governance degraded mode.

    GAP-070: Add DEGRADED state for incident response.

    The checker validates governance availability and can enter/exit
    degraded mode, creating incidents for visibility.

    Usage:
        checker = GovernanceDegradedModeChecker(check_enabled=True)

        # Check before starting a new run
        response = checker.check()
        if response.is_degraded:
            handle_degraded_mode(response)

        # Or ensure not degraded (raises on degraded)
        checker.ensure_not_degraded("start_new_run")

        # Enter degraded mode with incident
        checker.enter_degraded(
            state=DegradedModeState.DEGRADED,
            reason="Database connection pool exhausted",
            entered_by="health_monitor",
        )
    """

    def __init__(
        self,
        check_enabled: bool = True,
        incident_creator: Optional[DegradedModeIncidentCreator] = None,
    ):
        """
        Initialize the degraded mode checker.

        Args:
            check_enabled: Whether degraded mode checking is enabled
            incident_creator: Optional incident creator for degraded transitions
        """
        self._check_enabled = check_enabled
        self._incident_creator = incident_creator or DegradedModeIncidentCreator()

    @classmethod
    def from_governance_config(cls, config: Any) -> "GovernanceDegradedModeChecker":
        """
        Create checker from GovernanceConfig.

        Args:
            config: GovernanceConfig instance

        Returns:
            GovernanceDegradedModeChecker configured from config
        """
        check_enabled = getattr(config, "degraded_mode_check_enabled", True)
        return cls(check_enabled=check_enabled)

    @property
    def check_enabled(self) -> bool:
        """Check if degraded mode checking is enabled."""
        return self._check_enabled

    def get_current_status(self) -> DegradedModeStatus:
        """
        Get current degraded mode status.

        Returns:
            Current DegradedModeStatus
        """
        global _current_status

        with _state_lock:
            if _current_status is None:
                return DegradedModeStatus(state=DegradedModeState.NORMAL)
            return _current_status

    def check(self) -> DegradedModeCheckResponse:
        """
        Check current degraded mode state.

        Returns:
            DegradedModeCheckResponse with current state
        """
        status = self.get_current_status()

        if not self._check_enabled:
            return DegradedModeCheckResponse(
                result=DegradedModeCheckResult.CHECK_DISABLED,
                is_degraded=status.state != DegradedModeState.NORMAL,
                check_enabled=False,
                state=status.state,
                new_runs_action="ALLOW",
                existing_runs_action="ALLOW",
                message="Degraded mode checking is disabled",
            )

        if status.state == DegradedModeState.NORMAL:
            return DegradedModeCheckResponse(
                result=DegradedModeCheckResult.NORMAL,
                is_degraded=False,
                check_enabled=True,
                state=DegradedModeState.NORMAL,
                new_runs_action="ALLOW",
                existing_runs_action="ALLOW",
                message="Governance is fully operational",
            )

        if status.state == DegradedModeState.CRITICAL:
            return DegradedModeCheckResponse(
                result=DegradedModeCheckResult.CRITICAL,
                is_degraded=True,
                check_enabled=True,
                state=DegradedModeState.CRITICAL,
                new_runs_action=status.new_runs_action,
                existing_runs_action=status.existing_runs_action,
                message=f"Governance is in CRITICAL mode: {status.reason or 'unknown reason'}",
                degraded_since=status.entered_at,
                degraded_reason=status.reason,
                incident_id=status.incident_id,
            )

        return DegradedModeCheckResponse(
            result=DegradedModeCheckResult.DEGRADED,
            is_degraded=True,
            check_enabled=True,
            state=DegradedModeState.DEGRADED,
            new_runs_action=status.new_runs_action,
            existing_runs_action=status.existing_runs_action,
            message=f"Governance is in DEGRADED mode: {status.reason or 'unknown reason'}",
            degraded_since=status.entered_at,
            degraded_reason=status.reason,
            incident_id=status.incident_id,
        )

    def ensure_not_degraded(self, operation: str) -> None:
        """
        Ensure governance is not in degraded mode or raise error.

        Args:
            operation: Name of the operation being attempted

        Raises:
            GovernanceDegradedModeError: If governance is degraded
        """
        response = self.check()

        if response.result == DegradedModeCheckResult.CRITICAL:
            raise GovernanceDegradedModeError(
                message=(
                    f"Operation '{operation}' blocked: governance is in CRITICAL mode. "
                    f"Reason: {response.degraded_reason or 'unknown'}"
                ),
                state=DegradedModeState.CRITICAL,
                operation=operation,
                degraded_since=response.degraded_since,
                degraded_reason=response.degraded_reason,
            )

        if response.result == DegradedModeCheckResult.DEGRADED:
            # In degraded mode, check if new runs should be blocked
            if response.new_runs_action == "BLOCK":
                raise GovernanceDegradedModeError(
                    message=(
                        f"Operation '{operation}' blocked: governance is in DEGRADED mode. "
                        f"Reason: {response.degraded_reason or 'unknown'}"
                    ),
                    state=DegradedModeState.DEGRADED,
                    operation=operation,
                    degraded_since=response.degraded_since,
                    degraded_reason=response.degraded_reason,
                )

    def enter_degraded(
        self,
        state: DegradedModeState,
        reason: str,
        entered_by: str,
        new_runs_action: str = "BLOCK",
        existing_runs_action: str = "WARN",
        create_incident: bool = True,
    ) -> DegradedModeStatus:
        """
        Enter degraded mode.

        Args:
            state: Degraded mode state to enter
            reason: Reason for entering degraded mode
            entered_by: Who/what triggered the transition
            new_runs_action: Action for new runs (ALLOW, WARN, BLOCK)
            existing_runs_action: Action for existing runs
            create_incident: Whether to create an incident

        Returns:
            DegradedModeStatus after transition
        """
        global _current_status

        incident_id = None
        if create_incident:
            incident = self._incident_creator.create_degraded_incident(
                state=state,
                reason=reason,
                entered_by=entered_by,
            )
            incident_id = incident.incident_id

        now = datetime.now(timezone.utc).isoformat()

        with _state_lock:
            _current_status = DegradedModeStatus(
                state=state,
                reason=reason,
                entered_by=entered_by,
                entered_at=now,
                new_runs_action=new_runs_action,
                existing_runs_action=existing_runs_action,
                incident_id=incident_id,
            )
            return _current_status

    def exit_degraded(
        self,
        exited_by: str,
        create_incident: bool = True,
    ) -> DegradedModeStatus:
        """
        Exit degraded mode (recover to normal).

        Args:
            exited_by: Who/what triggered the recovery
            create_incident: Whether to create a recovery incident

        Returns:
            DegradedModeStatus after transition
        """
        global _current_status

        previous_status = self.get_current_status()

        if create_incident and previous_status.state != DegradedModeState.NORMAL:
            duration = None
            if previous_status.entered_at:
                try:
                    entered = datetime.fromisoformat(previous_status.entered_at.replace("Z", "+00:00"))
                    duration = int((datetime.now(timezone.utc) - entered).total_seconds())
                except (ValueError, TypeError):
                    pass

            self._incident_creator.create_recovery_incident(
                previous_state=previous_status.state,
                recovered_by=exited_by,
                duration_seconds=duration,
            )

        with _state_lock:
            _current_status = DegradedModeStatus(state=DegradedModeState.NORMAL)
            return _current_status

    def should_allow_new_run(self, run_id: str) -> tuple[bool, str]:
        """
        Check if a new run should be allowed.

        Args:
            run_id: ID of the run being started

        Returns:
            Tuple of (allowed, reason_message)
        """
        response = self.check()

        if not response.is_degraded:
            return True, "Governance is operational"

        if response.new_runs_action == "ALLOW":
            return True, f"New runs allowed in {response.state.value} mode"

        if response.new_runs_action == "WARN":
            logger.warning(
                "new_run_degraded_mode_warning",
                extra={"run_id": run_id, "state": response.state.value},
            )
            return True, f"New run allowed with warning in {response.state.value} mode"

        return False, f"New runs blocked in {response.state.value} mode: {response.degraded_reason}"

    def get_existing_run_action(self) -> str:
        """
        Get action for existing/in-flight runs.

        Returns:
            Action string: ALLOW, WARN, or BLOCK
        """
        status = self.get_current_status()
        return status.existing_runs_action


def check_degraded_mode(
    check_enabled: bool = True,
) -> DegradedModeCheckResponse:
    """
    Quick helper to check degraded mode.

    Args:
        check_enabled: Whether checking is enabled

    Returns:
        DegradedModeCheckResponse with current state
    """
    checker = GovernanceDegradedModeChecker(check_enabled=check_enabled)
    return checker.check()


def ensure_not_degraded(
    operation: str,
    check_enabled: bool = True,
) -> None:
    """
    Quick helper to ensure not in degraded mode or raise error.

    Args:
        operation: Name of the operation being attempted
        check_enabled: Whether checking is enabled

    Raises:
        GovernanceDegradedModeError: If governance is degraded and blocking
    """
    checker = GovernanceDegradedModeChecker(check_enabled=check_enabled)
    checker.ensure_not_degraded(operation)


def enter_degraded_with_incident(
    state: DegradedModeState,
    reason: str,
    entered_by: str,
    new_runs_action: str = "BLOCK",
    existing_runs_action: str = "WARN",
) -> DegradedModeStatus:
    """
    Quick helper to enter degraded mode with incident.

    Args:
        state: Degraded mode state to enter
        reason: Reason for entering degraded mode
        entered_by: Who/what triggered the transition
        new_runs_action: Action for new runs
        existing_runs_action: Action for existing runs

    Returns:
        DegradedModeStatus after transition
    """
    checker = GovernanceDegradedModeChecker()
    return checker.enter_degraded(
        state=state,
        reason=reason,
        entered_by=entered_by,
        new_runs_action=new_runs_action,
        existing_runs_action=existing_runs_action,
        create_incident=True,
    )


# Cleanup function for testing
def _reset_degraded_mode_state() -> None:
    """Reset global state (for testing only)."""
    global _current_status
    with _state_lock:
        _current_status = None
