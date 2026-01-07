# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api | cli
#   Execution: sync
# Role: Optional ergonomic decorator over ExecutionKernel
# Callers: HTTP route handlers, CLI commands
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2
# Reference: PIN-337

"""
@governed Decorator - PIN-337 Optional Ergonomic Wrapper

This decorator provides convenient syntax for routing execution
through the ExecutionKernel.

IMPORTANT:
- This decorator is OPTIONAL, not required
- CI does NOT enforce decorator presence
- CI enforces KERNEL usage (semantic), not syntax
- The decorator is CONVENIENCE, the kernel is PHYSICS
"""

from __future__ import annotations

import functools
import inspect
import logging
from typing import Any, Callable, Optional, TypeVar

from app.governance.kernel import (
    ExecutionKernel,
    InvocationContext,
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def governed(
    capability: str,
    execution_vector: str = "HTTP",
    extract_tenant: Optional[Callable[..., str]] = None,
    extract_subject: Optional[Callable[..., str]] = None,
    reason: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Decorator that routes execution through the ExecutionKernel.

    Usage:
        @governed(capability="CAP-019", execution_vector="HTTP_ADMIN")
        @app.post("/admin/retry")
        async def retry_run(payload: RetryRequest):
            # Business logic here
            ...

    Args:
        capability: The capability ID (e.g., "CAP-019")
        execution_vector: Where execution is coming from (HTTP, CLI, SDK, etc.)
        extract_tenant: Optional callable to extract tenant_id from args/kwargs
        extract_subject: Optional callable to extract subject from args/kwargs
        reason: Optional reason for the execution

    Returns:
        Decorated function that routes through kernel

    IMPORTANT:
        - This decorator is OPTIONAL
        - CI does not enforce decorator presence
        - CI enforces kernel usage (semantic check)
    """

    def decorator(func: F) -> F:
        is_async = inspect.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Extract context from arguments
                tenant_id = _extract_tenant_id(args, kwargs, extract_tenant)
                subject = _extract_subject(args, kwargs, extract_subject)

                context = InvocationContext(
                    subject=subject,
                    tenant_id=tenant_id,
                )

                # Route through kernel
                result = await ExecutionKernel.invoke_async(
                    capability_id=capability,
                    execution_vector=execution_vector,
                    context=context,
                    work=lambda: func(*args, **kwargs),
                    reason=reason,
                )

                return result.result

            return async_wrapper  # type: ignore
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Extract context from arguments
                tenant_id = _extract_tenant_id(args, kwargs, extract_tenant)
                subject = _extract_subject(args, kwargs, extract_subject)

                context = InvocationContext(
                    subject=subject,
                    tenant_id=tenant_id,
                )

                # Route through kernel
                result = ExecutionKernel.invoke(
                    capability_id=capability,
                    execution_vector=execution_vector,
                    context=context,
                    work=lambda: func(*args, **kwargs),
                    reason=reason,
                )

                return result.result

            return sync_wrapper  # type: ignore

    return decorator


def _extract_tenant_id(
    args: tuple,
    kwargs: dict,
    extractor: Optional[Callable[..., str]],
) -> str:
    """Extract tenant_id from function arguments."""
    if extractor:
        try:
            return extractor(*args, **kwargs)
        except Exception:
            pass

    # Try common patterns
    if "tenant_id" in kwargs:
        return str(kwargs["tenant_id"])

    # Look for objects with tenant_id attribute
    for arg in args:
        if hasattr(arg, "tenant_id"):
            return str(arg.tenant_id)

    # Look in kwargs values
    for value in kwargs.values():
        if hasattr(value, "tenant_id"):
            return str(value.tenant_id)

    return "unknown"


def _extract_subject(
    args: tuple,
    kwargs: dict,
    extractor: Optional[Callable[..., str]],
) -> str:
    """Extract subject from function arguments."""
    if extractor:
        try:
            return extractor(*args, **kwargs)
        except Exception:
            pass

    # Try common patterns
    if "user_id" in kwargs:
        return str(kwargs["user_id"])
    if "subject" in kwargs:
        return str(kwargs["subject"])

    # Look for objects with user_id attribute
    for arg in args:
        if hasattr(arg, "user_id"):
            return str(arg.user_id)

    # Default for admin routes
    return "founder"
