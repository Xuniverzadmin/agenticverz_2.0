# capability_id: CAP-006
# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api | worker
#   Execution: sync
# Role: Invocation context for cross-referencing side-effects
# Callers: All execution paths that produce side-effects
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2
# Reference: PIN-330

"""
Invocation Context - PIN-330 Cross-Reference Side-Effects

Provides context propagation for tagging side-effects with invocation_id.

USAGE:
    from app.auth.invocation_context import (
        get_current_invocation_id,
        set_current_invocation,
        invocation_context,
    )

    # In execution entry point:
    with invocation_context(envelope):
        # All side-effects in this context can access invocation_id
        do_work()

    # In side-effect code:
    invocation_id = get_current_invocation_id()
    if invocation_id:
        db_record.invocation_id = invocation_id

CONSTRAINTS:
- Best-effort only - missing context is not an error
- No retrofitting or refactoring required
- Context is thread-local for safety
"""

from __future__ import annotations

import contextvars
import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator, Optional

if TYPE_CHECKING:
    from app.auth.execution_envelope import ExecutionEnvelope

logger = logging.getLogger(__name__)

# Context variable for invocation tracking
_current_invocation: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_invocation_id", default=None
)

_current_envelope: contextvars.ContextVar[Optional["ExecutionEnvelope"]] = contextvars.ContextVar(
    "current_envelope", default=None
)


# =============================================================================
# CONTEXT ACCESSORS
# =============================================================================


def get_current_invocation_id() -> Optional[str]:
    """
    Get the current invocation_id for tagging side-effects.

    Returns None if not in an invocation context (best-effort).

    Usage:
        invocation_id = get_current_invocation_id()
        if invocation_id:
            record.invocation_id = invocation_id
    """
    return _current_invocation.get()


def get_current_envelope() -> Optional["ExecutionEnvelope"]:
    """
    Get the current execution envelope.

    Returns None if not in an invocation context.
    """
    return _current_envelope.get()


def get_current_tenant_id() -> Optional[str]:
    """
    Get the current tenant_id from the envelope context.

    Returns None if not in an invocation context.
    """
    envelope = _current_envelope.get()
    if envelope:
        return envelope.tenant_context.tenant_id
    return None


def get_current_capability_id() -> Optional[str]:
    """
    Get the current capability_id from the envelope context.

    Returns None if not in an invocation context.
    """
    envelope = _current_envelope.get()
    if envelope:
        return envelope.capability_id.value
    return None


# =============================================================================
# CONTEXT SETTERS (FOR ENTRY POINTS)
# =============================================================================


def set_current_invocation(invocation_id: Optional[str]) -> contextvars.Token[Optional[str]]:
    """
    Set the current invocation_id.

    Returns a token that can be used to reset the context.
    Typically used with try/finally or the context manager.
    """
    return _current_invocation.set(invocation_id)


def reset_current_invocation(token: contextvars.Token[Optional[str]]) -> None:
    """Reset the invocation context to its previous value."""
    _current_invocation.reset(token)


def set_current_envelope(envelope: Optional["ExecutionEnvelope"]) -> contextvars.Token[Optional["ExecutionEnvelope"]]:
    """
    Set the current execution envelope.

    Returns a token that can be used to reset the context.
    """
    return _current_envelope.set(envelope)


def reset_current_envelope(token: contextvars.Token[Optional["ExecutionEnvelope"]]) -> None:
    """Reset the envelope context to its previous value."""
    _current_envelope.reset(token)


# =============================================================================
# CONTEXT MANAGER
# =============================================================================


@contextmanager
def invocation_context(
    envelope: "ExecutionEnvelope",
) -> Generator["ExecutionEnvelope", None, None]:
    """
    Context manager for invocation tracking.

    All code within this context can access the invocation_id
    for tagging side-effects.

    Usage:
        envelope = ExecutionEnvelopeFactory.create_cli_envelope(...)
        with invocation_context(envelope) as env:
            # All DB writes, events, logs in here can be tagged
            result = do_work()

            # Check for mutation
            mutated, updated = detect_plan_mutation(env, new_plan)
            if mutated:
                env = updated  # Context manager yields the envelope

    Args:
        envelope: The execution envelope for this invocation

    Yields:
        The execution envelope (for mutation tracking)
    """
    invocation_token = set_current_invocation(envelope.invocation.invocation_id)
    envelope_token = set_current_envelope(envelope)

    try:
        yield envelope
    finally:
        reset_current_invocation(invocation_token)
        reset_current_envelope(envelope_token)


# =============================================================================
# LOGGING INTEGRATION
# =============================================================================


class InvocationLogFilter(logging.Filter):
    """
    Logging filter that adds invocation_id to log records.

    Usage:
        handler.addFilter(InvocationLogFilter())

    Then logs will include:
        "invocation_id": "<uuid>" (or None if not in context)
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add invocation_id to log record."""
        record.invocation_id = get_current_invocation_id()
        record.capability_id = get_current_capability_id()
        record.tenant_id = get_current_tenant_id()
        return True


# =============================================================================
# HELPER FOR SIDE-EFFECT TAGGING
# =============================================================================


def tag_with_invocation(obj: Any, field_name: str = "invocation_id") -> bool:
    """
    Tag an object with the current invocation_id if available.

    Best-effort - does nothing if:
    - Not in invocation context
    - Object doesn't have the specified field

    Args:
        obj: The object to tag (e.g., DB model, event dict)
        field_name: The field name to set

    Returns:
        True if tagged, False otherwise
    """
    invocation_id = get_current_invocation_id()
    if invocation_id is None:
        return False

    if isinstance(obj, dict):
        obj[field_name] = invocation_id
        return True

    if hasattr(obj, field_name):
        try:
            setattr(obj, field_name, invocation_id)
            return True
        except AttributeError:
            # Read-only attribute
            return False

    return False


def get_invocation_metadata() -> dict[str, Optional[str]]:
    """
    Get all invocation metadata for inclusion in side-effects.

    Returns a dict that can be merged into events, logs, etc.

    Usage:
        event_data = {
            "type": "skill_executed",
            **get_invocation_metadata(),
        }
    """
    return {
        "invocation_id": get_current_invocation_id(),
        "capability_id": get_current_capability_id(),
        "tenant_id": get_current_tenant_id(),
    }


# =============================================================================
# DECORATOR FOR AUTOMATIC TRACKING
# =============================================================================


def with_invocation_tracking(func):
    """
    Decorator that ensures invocation context is available.

    If already in a context, uses existing.
    If not, logs a warning (does not fail).

    Usage:
        @with_invocation_tracking
        def perform_db_write(data):
            # invocation_id is available via get_current_invocation_id()
            pass
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if get_current_invocation_id() is None:
            logger.debug(
                f"Function {func.__name__} called without invocation context",
                extra={"function": func.__name__},
            )
        return func(*args, **kwargs)

    return wrapper
