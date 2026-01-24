# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Optimization killswitch for emergency stops
# Callers: API routes, workers
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: M10 Optimization

# C3 Kill-Switch Implementation
# Reference: C3_KILLSWITCH_ROLLBACK_MODEL.md (FROZEN)
#
# Kill-switch invariants (K-1 to K-5):
# - K-1: Kill-switch overrides all envelopes
# - K-2: Kill-switch causes immediate reversion
# - K-3: Kill-switch does not depend on predictions
# - K-4: Kill-switch does not require redeploy
# - K-5: Kill-switch is auditable
#
# If ANY invariant fails, C3 fails certification.

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, List, Optional

logger = logging.getLogger("nova.optimization.killswitch")


class KillSwitchState(str, Enum):
    """Global kill-switch state. Exactly two values. No partial states."""

    ENABLED = "enabled"  # Optimization is allowed
    DISABLED = "disabled"  # Optimization is blocked, all envelopes reverted


class KillSwitchTrigger(str, Enum):
    """What triggered the kill-switch."""

    HUMAN = "human"  # Operator action (primary)
    SYSTEM = "system"  # System integrity failure (mandatory)
    # Note: predictions/envelopes/optimization logic may NOT trigger kill-switch


class RollbackStatus(str, Enum):
    """Status of rollback operation."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class KillSwitchEvent:
    """
    Immutable audit record for kill-switch events.

    Required by C3_KILLSWITCH_ROLLBACK_MODEL.md section 8.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    triggered_by: KillSwitchTrigger = KillSwitchTrigger.HUMAN
    trigger_reason: str = ""
    activated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    active_envelopes_count: int = 0
    rollback_completed_at: Optional[datetime] = None
    rollback_status: RollbackStatus = RollbackStatus.SUCCESS


class KillSwitch:
    """
    Global, authoritative kill-switch for C3 optimization.

    Properties:
    - Global: Disables ALL envelopes (no per-envelope switches)
    - Immediate: No grace period, no batching, no retries
    - Independent: Does not require predictions or redeploy
    - Auditable: Every activation emits an audit record

    Thread-safe implementation.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._state = KillSwitchState.ENABLED
        self._events: List[KillSwitchEvent] = []
        self._on_activate_callbacks: List[Callable[[KillSwitchEvent], None]] = []

    @property
    def state(self) -> KillSwitchState:
        """Current kill-switch state."""
        with self._lock:
            return self._state

    @property
    def is_enabled(self) -> bool:
        """True if optimization is allowed."""
        return self.state == KillSwitchState.ENABLED

    @property
    def is_disabled(self) -> bool:
        """True if optimization is blocked."""
        return self.state == KillSwitchState.DISABLED

    def activate(
        self,
        reason: str,
        triggered_by: KillSwitchTrigger = KillSwitchTrigger.HUMAN,
        active_envelopes_count: int = 0,
    ) -> KillSwitchEvent:
        """
        Activate kill-switch. Immediately disables all optimization.

        Args:
            reason: Human-readable reason for activation
            triggered_by: What triggered the kill-switch
            active_envelopes_count: Number of active envelopes to revert

        Returns:
            Audit event for the activation

        Effects:
            - State changes to DISABLED
            - All active envelopes must be reverted by caller
            - No new envelopes may be applied
            - Audit record is emitted
        """
        # Capture callbacks to call outside lock (avoid deadlock)
        callbacks_to_call = []

        with self._lock:
            # Create audit event
            event = KillSwitchEvent(
                triggered_by=triggered_by,
                trigger_reason=reason,
                active_envelopes_count=active_envelopes_count,
            )

            # State transition
            self._state = KillSwitchState.DISABLED

            # Record event
            self._events.append(event)

            # Copy callbacks for invocation outside lock
            callbacks_to_call = list(self._on_activate_callbacks)

            logger.warning(
                "killswitch_activated",
                extra={
                    "event_id": event.event_id,
                    "triggered_by": triggered_by.value,
                    "reason": reason,
                    "active_envelopes": active_envelopes_count,
                },
            )

        # Notify callbacks OUTSIDE lock to avoid deadlock
        for callback in callbacks_to_call:
            try:
                callback(event)
            except Exception as e:
                logger.error(
                    "killswitch_callback_error",
                    extra={"event_id": event.event_id, "error": str(e)},
                )

        return event

    def mark_rollback_complete(
        self,
        event_id: str,
        status: RollbackStatus = RollbackStatus.SUCCESS,
    ) -> None:
        """
        Mark rollback as complete for a kill-switch event.

        Args:
            event_id: The event to update
            status: Rollback status (success, partial, failed)
        """
        with self._lock:
            for event in self._events:
                if event.event_id == event_id:
                    event.rollback_completed_at = datetime.now(timezone.utc)
                    event.rollback_status = status

                    logger.info(
                        "killswitch_rollback_complete",
                        extra={
                            "event_id": event_id,
                            "status": status.value,
                            "completed_at": event.rollback_completed_at.isoformat(),
                        },
                    )
                    return

    def rearm(self, reason: str) -> None:
        """
        Re-enable optimization. Requires EXPLICIT human action.

        Args:
            reason: Human-readable reason for rearming

        Note: No auto-rearm. No cooldown logic.
        """
        with self._lock:
            if self._state == KillSwitchState.DISABLED:
                self._state = KillSwitchState.ENABLED
                logger.warning(
                    "killswitch_rearmed",
                    extra={"reason": reason},
                )

    def on_activate(self, callback: Callable[[KillSwitchEvent], None]) -> None:
        """Register callback to be called when kill-switch activates."""
        with self._lock:
            self._on_activate_callbacks.append(callback)

    def get_events(self) -> List[KillSwitchEvent]:
        """Get all kill-switch events for audit."""
        with self._lock:
            return list(self._events)

    def get_last_event(self) -> Optional[KillSwitchEvent]:
        """Get most recent kill-switch event."""
        with self._lock:
            return self._events[-1] if self._events else None


# Global singleton instance
_killswitch: Optional[KillSwitch] = None
_killswitch_lock = threading.Lock()


def get_killswitch() -> KillSwitch:
    """Get the global kill-switch instance."""
    global _killswitch
    with _killswitch_lock:
        if _killswitch is None:
            _killswitch = KillSwitch()
        return _killswitch


def reset_killswitch_for_testing() -> None:
    """Reset kill-switch state. FOR TESTING ONLY."""
    global _killswitch
    with _killswitch_lock:
        _killswitch = KillSwitch()
