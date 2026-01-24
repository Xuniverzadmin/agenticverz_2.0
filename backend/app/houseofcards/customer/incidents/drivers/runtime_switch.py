# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: api (emergency) or internal (failure detection)
#   Execution: sync
# Role: Runtime toggle for governance enforcement
# Callers: ops_api.py, failure_mode_handler.py, health.py
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: GAP-069

"""
Module: runtime_switch
Purpose: Provides runtime toggle for governance. Emergency kill switch.

Imports (Dependencies):
    - logging
    - datetime
    - threading (for atomic operations)

Exports (Provides):
    - is_governance_active() -> bool
    - disable_governance_runtime(reason, actor) -> None
    - enable_governance_runtime(actor) -> None
    - get_governance_state() -> GovernanceState
    - is_degraded_mode() -> bool (GAP-070)
    - enter_degraded_mode(reason, actor) -> None (GAP-070)
    - exit_degraded_mode(actor) -> None (GAP-070)

Wiring Points:
    - Called from: prevention_engine.py (check before enforcement)
    - Called from: runner.py (check before accepting new runs)
    - Called from: ops_api.py (manual toggle endpoint)
    - Emits: governance_state_changed event

Acceptance Criteria:
    - [x] AC-069-01: Governance active by default
    - [x] AC-069-02: Kill switch disables enforcement
    - [x] AC-069-03: Kill switch logs critical audit
    - [x] AC-069-04: Re-enable restores enforcement
    - [x] AC-069-05: OPS endpoint exists
    - [x] AC-069-06: Requires OPS permission
    - [x] AC-069-07: State visible in health
    - [x] AC-069-08: Thread-safe operations
"""

import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger("nova.services.governance.runtime_switch")


@dataclass
class GovernanceState:
    """Current governance state."""
    active: bool
    last_changed: Optional[datetime]
    last_change_reason: Optional[str]
    last_change_actor: Optional[str]
    degraded_mode: bool  # GAP-070: Degraded mode flag


# Thread-safe state
_lock = threading.Lock()
_state = GovernanceState(
    active=True,
    last_changed=None,
    last_change_reason=None,
    last_change_actor=None,
    degraded_mode=False,
)


def is_governance_active() -> bool:
    """
    Check if governance is currently active.

    Returns:
        True if governance enforcement is active
    """
    with _lock:
        return _state.active


def is_degraded_mode() -> bool:
    """
    Check if system is in degraded mode (GAP-070).

    Degraded mode:
    - Governance is active
    - New runs are blocked
    - Existing runs complete with WARN

    Returns:
        True if in degraded mode
    """
    with _lock:
        return _state.degraded_mode


def disable_governance_runtime(reason: str, actor: str) -> None:
    """
    Emergency kill switch. Disables governance enforcement.

    WARNING: This allows runs to bypass policy enforcement.
    Use only for emergency incident response.

    Args:
        reason: Why governance is being disabled
        actor: Who/what triggered the disable (user_id or "system")
    """
    global _state

    with _lock:
        _state = GovernanceState(
            active=False,
            last_changed=datetime.utcnow(),
            last_change_reason=reason,
            last_change_actor=actor,
            degraded_mode=False,
        )

    logger.critical("governance.disabled_runtime", extra={
        "reason": reason,
        "actor": actor,
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Emit event for monitoring
    _emit_governance_event("governance_disabled", reason, actor)


def enable_governance_runtime(actor: str) -> None:
    """
    Re-enable governance after emergency.

    Args:
        actor: Who/what triggered the re-enable
    """
    global _state

    with _lock:
        _state = GovernanceState(
            active=True,
            last_changed=datetime.utcnow(),
            last_change_reason="re-enabled",
            last_change_actor=actor,
            degraded_mode=False,
        )

    logger.info("governance.enabled_runtime", extra={
        "actor": actor,
        "timestamp": datetime.utcnow().isoformat(),
    })

    _emit_governance_event("governance_enabled", "re-enabled", actor)


def enter_degraded_mode(reason: str, actor: str) -> None:
    """
    GAP-070: Enter degraded mode.

    Degraded mode:
    - Blocks new runs
    - Existing runs complete with WARN
    - Full audit emitted

    Args:
        reason: Why entering degraded mode
        actor: Who/what triggered degraded mode
    """
    global _state

    with _lock:
        _state = GovernanceState(
            active=True,  # Still active, but degraded
            last_changed=datetime.utcnow(),
            last_change_reason=f"degraded: {reason}",
            last_change_actor=actor,
            degraded_mode=True,
        )

    logger.warning("governance.degraded_mode_entered", extra={
        "reason": reason,
        "actor": actor,
        "timestamp": datetime.utcnow().isoformat(),
    })

    _emit_governance_event("governance_degraded", reason, actor)


def exit_degraded_mode(actor: str) -> None:
    """
    Exit degraded mode, return to normal operation.

    Args:
        actor: Who/what triggered exit from degraded mode
    """
    global _state

    with _lock:
        _state = GovernanceState(
            active=True,
            last_changed=datetime.utcnow(),
            last_change_reason="exited_degraded",
            last_change_actor=actor,
            degraded_mode=False,
        )

    logger.info("governance.degraded_mode_exited", extra={
        "actor": actor,
        "timestamp": datetime.utcnow().isoformat(),
    })

    _emit_governance_event("governance_normal", "exited_degraded", actor)


def get_governance_state() -> dict:
    """
    Get current governance state for health checks.

    Returns:
        Dict with governance state details
    """
    with _lock:
        return {
            "active": _state.active,
            "degraded_mode": _state.degraded_mode,
            "last_changed": _state.last_changed.isoformat() if _state.last_changed else None,
            "last_change_reason": _state.last_change_reason,
            "last_change_actor": _state.last_change_actor,
        }


def reset_governance_state() -> None:
    """Reset governance state to defaults (for testing)."""
    global _state

    with _lock:
        _state = GovernanceState(
            active=True,
            last_changed=None,
            last_change_reason=None,
            last_change_actor=None,
            degraded_mode=False,
        )


def _emit_governance_event(event_type: str, reason: str, actor: str) -> None:
    """
    Emit governance state change event.

    Args:
        event_type: Type of event (governance_disabled, governance_enabled, etc.)
        reason: Reason for the change
        actor: Who triggered the change
    """
    try:
        from app.events.subscribers import get_event_reactor

        reactor = get_event_reactor()
        if reactor and hasattr(reactor, 'emit'):
            reactor.emit("governance_state_changed", {
                "event_type": event_type,
                "reason": reason,
                "actor": actor,
                "timestamp": datetime.utcnow().isoformat(),
            })
    except Exception as e:
        # Don't fail on event emission - just log
        logger.error("governance.event_emit_failed", extra={"error": str(e)})
