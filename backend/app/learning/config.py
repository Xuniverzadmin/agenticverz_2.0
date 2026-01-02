# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Learning system configuration
# Callers: learning/*
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: C5 Learning

"""
C5 Learning Configuration.

CRITICAL: LEARNING_ENABLED defaults to False.
Learning must be explicitly enabled by operator.

Reference: CI-C5-5, PIN-232
"""

import logging
import os
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger("nova.learning.config")

# Default OFF - learning must be explicitly enabled
# This is checked by CI-C5-5 (check_disable_flag.sh)
_LEARNING_ENABLED: bool = False


def learning_enabled() -> bool:
    """
    Check if learning is enabled.

    Returns:
        bool: True if learning is enabled, False otherwise.

    CI-C5-5 Requirement:
        - This function must exist
        - Must return False by default
        - Must be checkable at runtime
    """
    global _LEARNING_ENABLED
    # Allow runtime override via environment
    env_override = os.environ.get("LEARNING_ENABLED", "").lower()
    if env_override in ("true", "1", "yes"):
        return True
    if env_override in ("false", "0", "no"):
        return False
    return _LEARNING_ENABLED


def set_learning_enabled(enabled: bool) -> None:
    """
    Set learning enabled state.

    Args:
        enabled: Whether to enable learning.

    Note:
        This is for runtime toggling by operators.
        Should emit audit event when changed.
    """
    global _LEARNING_ENABLED
    old_value = _LEARNING_ENABLED
    _LEARNING_ENABLED = enabled

    if old_value != enabled:
        logger.info(
            "learning_toggle",
            extra={
                "old_value": old_value,
                "new_value": enabled,
                "source": "runtime",
            },
        )


# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


def require_learning_enabled(func: F) -> F:
    """
    Decorator that skips function execution when learning is disabled.

    Usage:
        @require_learning_enabled
        def observe_rollbacks():
            ...  # Only runs if learning is enabled

    Returns:
        None if learning is disabled, otherwise the function result.

    CI-C5-5 Requirement:
        - Guard pattern must exist in S1 entry points
        - When disabled, no observation or suggestion generation
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Optional[Any]:
        if not learning_enabled():
            logger.info(
                "learning_disabled_skip",
                extra={
                    "function": func.__name__,
                    "func_module": func.__module__,  # Renamed to avoid LogRecord conflict
                },
            )
            return None
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
