# capability_id: CAP-009
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: system-condition or operator-action
#   Execution: sync
# Lifecycle:
#   Emits: degraded_mode_change
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Degraded mode for governance system (pure state logic)
# Callers: main.py, prevention_engine.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-070
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure logic

"""
Degraded Mode - Graceful Governance Degradation

When governance systems are partially unavailable, the system
can enter degraded mode:
- New runs are blocked
- Existing runs continue with WARN action
- Telemetry and logging continue

This prevents cascading failures while maintaining visibility.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Optional

logger = logging.getLogger("nova.policy.degraded_mode")

# Global state with thread safety
_state_lock = Lock()
_degraded_mode_active = False
_degraded_mode_status: Optional["DegradedModeStatus"] = None


@dataclass
class DegradedModeStatus:
    """Current status of degraded mode."""

    is_active: bool = False
    reason: Optional[str] = None
    entered_by: Optional[str] = None
    entered_at: Optional[str] = None
    existing_runs_action: str = "WARN"  # What to do with in-flight runs

    @classmethod
    def get_inactive(cls) -> "DegradedModeStatus":
        """Get inactive status."""
        return cls(is_active=False)


@dataclass
class DegradedModeTransition:
    """Result of degraded mode transition."""

    success: bool
    message: str
    transitioned_at: Optional[str] = None


def enter_degraded_mode(
    reason: str,
    entered_by: str,
    existing_runs_action: str = "WARN",
) -> DegradedModeTransition:
    """
    Enter degraded mode.

    New runs will be blocked, existing runs continue with warnings.

    Args:
        reason: Why degraded mode is being entered
        entered_by: Identifier of operator/system entering
        existing_runs_action: Action for in-flight runs (WARN, ALLOW, BLOCK)

    Returns:
        DegradedModeTransition result
    """
    global _degraded_mode_active, _degraded_mode_status

    now_str = datetime.now(timezone.utc).isoformat()

    with _state_lock:
        _degraded_mode_active = True
        _degraded_mode_status = DegradedModeStatus(
            is_active=True,
            reason=reason,
            entered_by=entered_by,
            entered_at=now_str,
            existing_runs_action=existing_runs_action,
        )

    logger.warning(
        "degraded_mode_entered",
        extra={
            "reason": reason,
            "entered_by": entered_by,
            "entered_at": now_str,
            "existing_runs_action": existing_runs_action,
        },
    )

    return DegradedModeTransition(
        success=True,
        message=f"Entered degraded mode: {reason}",
        transitioned_at=now_str,
    )


def exit_degraded_mode(
    exited_by: str = "system",
) -> DegradedModeTransition:
    """
    Exit degraded mode.

    Restores normal governance operation.

    Args:
        exited_by: Identifier of operator/system exiting

    Returns:
        DegradedModeTransition result
    """
    global _degraded_mode_active, _degraded_mode_status

    now_str = datetime.now(timezone.utc).isoformat()

    with _state_lock:
        was_active = _degraded_mode_active
        _degraded_mode_active = False
        _degraded_mode_status = DegradedModeStatus.get_inactive()

    if was_active:
        logger.info(
            "degraded_mode_exited",
            extra={
                "exited_by": exited_by,
                "exited_at": now_str,
            },
        )

    return DegradedModeTransition(
        success=True,
        message=f"Exited degraded mode",
        transitioned_at=now_str,
    )


def is_degraded_mode_active() -> bool:
    """
    Check if degraded mode is currently active.

    Returns:
        True if system is in degraded mode
    """
    with _state_lock:
        return _degraded_mode_active


def get_degraded_mode_status() -> DegradedModeStatus:
    """
    Get current degraded mode status.

    Returns:
        Current DegradedModeStatus
    """
    global _degraded_mode_status

    with _state_lock:
        if _degraded_mode_status is None:
            return DegradedModeStatus.get_inactive()
        return _degraded_mode_status


def should_allow_new_run(run_id: str) -> bool:
    """
    Check if a new run should be allowed.

    In degraded mode, new runs are blocked.

    Args:
        run_id: ID of the run being started

    Returns:
        True if run should be allowed, False to block
    """
    if not is_degraded_mode_active():
        return True

    logger.warning(
        "new_run_blocked_degraded_mode",
        extra={"run_id": run_id},
    )
    return False


def get_existing_run_action() -> str:
    """
    Get action for existing/in-flight runs in degraded mode.

    Returns:
        Action string: WARN, ALLOW, or BLOCK
    """
    with _state_lock:
        if _degraded_mode_status is None:
            return "ALLOW"
        return _degraded_mode_status.existing_runs_action
