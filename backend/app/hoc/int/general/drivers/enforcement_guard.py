# capability_id: CAP-006
# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: worker (during step execution)
#   Execution: sync (must complete before step returns)
# Role: Guarantee enforcement check is never skipped
# Callers: runner.py step execution loop
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4
# Reference: GAP-030

"""
Module: enforcement_guard
Purpose: Guarantees enforcement is never skipped.

Context managers that ensure enforcement checks are performed.
If enforcement check is bypassed, the guard raises an error at exit.

Imports (Dependencies):
    - None (standalone)

Exports (Provides):
    - EnforcementGuard: Context manager that ensures enforcement runs
    - EnforcementSkippedError: Raised if enforcement was bypassed

Wiring Points:
    - Called from: runner.py step execution loop
    - Wraps: Each step execution to guarantee enforcement check

Acceptance Criteria:
    - [x] AC-030-01: Guard raises if enforcement skipped
    - [x] AC-030-02: Guard passes if enforcement checked
    - [x] AC-030-03: Every step uses guard (verified by wiring)
"""

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger("nova.worker.enforcement.enforcement_guard")


class EnforcementSkippedError(Exception):
    """Raised when enforcement check was bypassed."""

    def __init__(self, step_number: int, run_id: str, message: str = ""):
        self.step_number = step_number
        self.run_id = run_id
        super().__init__(
            f"Enforcement check was skipped for run={run_id}, step={step_number}. {message}"
        )


@dataclass
class EnforcementCheckpoint:
    """Record of an enforcement check."""
    checked: bool
    timestamp: Optional[str]
    enforcement_result: Optional[Any]
    policy_id: Optional[str]


class _EnforcementGuardImpl:
    """Internal implementation of enforcement guard."""

    def __init__(self, run_context: Any, step_number: int):
        self.run_context = run_context
        self.step_number = step_number
        self._enforcement_checked = False
        self._check_timestamp: Optional[str] = None
        self._enforcement_result: Optional[Any] = None
        self._policy_id: Optional[str] = None

    @property
    def run_id(self) -> str:
        """Get run_id from context."""
        return getattr(self.run_context, 'run_id', 'unknown')

    def mark_enforcement_checked(
        self,
        result: Optional[Any] = None,
        policy_id: Optional[str] = None,
    ):
        """
        Mark that enforcement check was performed.

        Must be called before the guard exits, otherwise EnforcementSkippedError
        is raised.

        Args:
            result: Optional enforcement result to record
            policy_id: Optional policy_id that triggered the result
        """
        self._enforcement_checked = True
        self._check_timestamp = datetime.now(timezone.utc).isoformat()
        self._enforcement_result = result
        self._policy_id = policy_id

        logger.debug("enforcement_guard.checked", extra={
            "run_id": self.run_id,
            "step_number": self.step_number,
            "timestamp": self._check_timestamp,
            "policy_id": policy_id,
        })

    def get_checkpoint(self) -> EnforcementCheckpoint:
        """Get enforcement checkpoint state."""
        return EnforcementCheckpoint(
            checked=self._enforcement_checked,
            timestamp=self._check_timestamp,
            enforcement_result=self._enforcement_result,
            policy_id=self._policy_id,
        )


@contextmanager
def enforcement_guard(run_context: Any, step_number: int):
    """
    Context manager that ensures enforcement check happens.

    Usage:
        with enforcement_guard(ctx, step_num) as guard:
            result = execute_step()
            enforcement_result = check_enforcement(result)
            guard.mark_enforcement_checked(enforcement_result)
        # If mark_enforcement_checked() not called, raises EnforcementSkippedError

    Args:
        run_context: Run context with run_id and other metadata
        step_number: Current step number

    Yields:
        Guard object with mark_enforcement_checked() method

    Raises:
        EnforcementSkippedError: If guard exits without enforcement being checked
    """
    guard = _EnforcementGuardImpl(run_context, step_number)

    logger.debug("enforcement_guard.entered", extra={
        "run_id": guard.run_id,
        "step_number": step_number,
    })

    try:
        yield guard
    finally:
        if not guard._enforcement_checked:
            logger.error("enforcement_guard.skipped", extra={
                "run_id": guard.run_id,
                "step_number": step_number,
            })
            raise EnforcementSkippedError(
                step_number=step_number,
                run_id=guard.run_id,
                message="mark_enforcement_checked() was not called before guard exit",
            )

        logger.debug("enforcement_guard.exited", extra={
            "run_id": guard.run_id,
            "step_number": step_number,
            "enforcement_checked": True,
        })


def require_enforcement(run_context: Any, step_number: int):
    """
    Decorator alternative for enforcement guard.

    Usage:
        @require_enforcement(ctx, step)
        def execute_step():
            ...
            return result, enforcement_checked

    Note: The decorated function must return a tuple where the second
    element indicates enforcement was checked.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with enforcement_guard(run_context, step_number) as guard:
                result, enforcement_checked = func(*args, **kwargs)
                if enforcement_checked:
                    guard.mark_enforcement_checked(result)
                return result
        return wrapper
    return decorator
