# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: operator-action
#   Execution: sync
# Lifecycle:
#   Emits: kill_switch_activated
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Runtime kill switch for governance bypass (pure state logic)
# Callers: main.py, prevention_engine.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-069
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure logic

"""
Kill Switch - Runtime Governance Bypass

Provides emergency governance disable capability without restart.
When active, all governance checks are bypassed (fail-open mode).

Use cases:
- Emergency maintenance
- Security incident response
- Governance system failures

Security considerations:
- Activation requires authenticated operator
- All activations are logged
- Automatic timeout for safety
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Optional

logger = logging.getLogger("nova.policy.kill_switch")

# Global state with thread safety
_state_lock = Lock()
_kill_switch_active = False
_kill_switch_status: Optional["KillSwitchStatus"] = None


@dataclass
class KillSwitchStatus:
    """Current status of the kill switch."""

    is_active: bool = False
    reason: Optional[str] = None
    activated_by: Optional[str] = None
    activated_at: Optional[str] = None
    auto_expire_at: Optional[str] = None

    @classmethod
    def get_current(cls) -> "KillSwitchStatus":
        """Get current kill switch status."""
        global _kill_switch_status
        with _state_lock:
            if _kill_switch_status is None:
                return cls(is_active=False)
            return _kill_switch_status


@dataclass
class KillSwitchActivation:
    """Result of kill switch activation."""

    success: bool
    message: str
    activated_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class KillSwitchDeactivation:
    """Result of kill switch deactivation."""

    success: bool
    message: str
    deactivated_at: Optional[str] = None


def activate_kill_switch(
    reason: str,
    activated_by: str,
    auto_expire_minutes: int = 60,
) -> KillSwitchActivation:
    """
    Activate the runtime kill switch.

    When active, governance checks are bypassed (fail-open).

    Args:
        reason: Why the kill switch is being activated
        activated_by: Identifier of operator activating
        auto_expire_minutes: Auto-deactivate after this many minutes

    Returns:
        KillSwitchActivation result
    """
    global _kill_switch_active, _kill_switch_status

    now = datetime.now(timezone.utc)
    now_str = now.isoformat()
    expire_str = None

    if auto_expire_minutes > 0:
        from datetime import timedelta

        expire_at = now + timedelta(minutes=auto_expire_minutes)
        expire_str = expire_at.isoformat()

    with _state_lock:
        _kill_switch_active = True
        _kill_switch_status = KillSwitchStatus(
            is_active=True,
            reason=reason,
            activated_by=activated_by,
            activated_at=now_str,
            auto_expire_at=expire_str,
        )

    logger.warning(
        "kill_switch_activated",
        extra={
            "reason": reason,
            "activated_by": activated_by,
            "activated_at": now_str,
            "auto_expire_at": expire_str,
        },
    )

    return KillSwitchActivation(
        success=True,
        message=f"Kill switch activated by {activated_by}",
        activated_at=now_str,
    )


def deactivate_kill_switch(
    deactivated_by: str = "system",
) -> KillSwitchDeactivation:
    """
    Deactivate the runtime kill switch.

    Restores normal governance enforcement.

    Args:
        deactivated_by: Identifier of operator deactivating

    Returns:
        KillSwitchDeactivation result
    """
    global _kill_switch_active, _kill_switch_status

    now_str = datetime.now(timezone.utc).isoformat()

    with _state_lock:
        was_active = _kill_switch_active
        _kill_switch_active = False
        _kill_switch_status = KillSwitchStatus(is_active=False)

    if was_active:
        logger.info(
            "kill_switch_deactivated",
            extra={
                "deactivated_by": deactivated_by,
                "deactivated_at": now_str,
            },
        )

    return KillSwitchDeactivation(
        success=True,
        message=f"Kill switch deactivated by {deactivated_by}",
        deactivated_at=now_str,
    )


def is_kill_switch_active() -> bool:
    """
    Check if kill switch is currently active.

    Also handles auto-expiration.

    Returns:
        True if governance should be bypassed
    """
    global _kill_switch_active, _kill_switch_status

    with _state_lock:
        if not _kill_switch_active:
            return False

        # Check auto-expiration
        if _kill_switch_status and _kill_switch_status.auto_expire_at:
            expire_at = datetime.fromisoformat(_kill_switch_status.auto_expire_at)
            if datetime.now(timezone.utc) >= expire_at:
                # Auto-expire
                _kill_switch_active = False
                _kill_switch_status = KillSwitchStatus(is_active=False)
                logger.info("kill_switch_auto_expired")
                return False

        return True


def should_bypass_governance() -> bool:
    """
    Check if governance should be bypassed.

    Alias for is_kill_switch_active() for clearer intent.

    Returns:
        True if governance checks should be skipped
    """
    return is_kill_switch_active()
