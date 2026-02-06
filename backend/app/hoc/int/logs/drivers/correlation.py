# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: any (api|worker|scheduler|external)
#   Execution: sync
# Role: Correlation ID generation and context propagation
# Callers: Any layer requiring request tracing
# Allowed Imports: None (pure utilities + stdlib)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-264 (Phase-S Error Capture, Section 1.2)

"""
Correlation ID Utilities — Phase-S Track 1.2

One request/workflow must be traceable across:
- API layer
- Domain engine
- Worker
- Decision emission

Design Principles:
- Thread-safe: Uses contextvars for async-safe propagation
- Immutable IDs: Once generated, correlation IDs never change
- Hierarchical: Can create child spans for sub-operations
- Lightweight: No external dependencies
"""

import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Generator, Optional

# Context variable for the current correlation context
_correlation_context: ContextVar[Optional["CorrelationContext"]] = ContextVar("correlation_context", default=None)


def generate_correlation_id(prefix: str = "req") -> str:
    """
    Generate a unique correlation ID.

    Format: {prefix}_{timestamp}_{random}
    Example: req_20260101_a1b2c3d4e5f6

    Args:
        prefix: ID prefix (e.g., "req" for request, "run" for workflow run)

    Returns:
        Unique correlation ID string
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = uuid.uuid4().hex[:12]
    return f"{prefix}_{timestamp}_{random_part}"


def get_current_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.

    Returns:
        Current correlation ID or None if not set
    """
    ctx = _correlation_context.get()
    return ctx.correlation_id if ctx else None


def get_current_span_id() -> Optional[str]:
    """
    Get the current span ID from context.

    Returns:
        Current span ID or None if not set
    """
    ctx = _correlation_context.get()
    return ctx.span_id if ctx else None


@dataclass(frozen=True)
class CorrelationContext:
    """
    Immutable correlation context for request tracing.

    Holds the correlation ID and optional span ID for
    hierarchical tracing within a single request/workflow.

    Attributes:
        correlation_id: Root trace ID (same for entire request)
        span_id: Current operation span (changes for sub-operations)
        parent_span_id: Parent span for hierarchical tracing
        component: Current component name
        started_at: When this context was created
    """

    correlation_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    component: Optional[str] = None
    started_at: datetime = None  # type: ignore

    def __post_init__(self) -> None:
        # Workaround for frozen dataclass with default factory
        if self.started_at is None:
            object.__setattr__(self, "started_at", datetime.now(timezone.utc))

    def child(self, component: Optional[str] = None) -> "CorrelationContext":
        """
        Create a child context for a sub-operation.

        The correlation_id stays the same, but a new span_id is created.

        Args:
            component: Optional component name for the child span

        Returns:
            New CorrelationContext with same correlation_id, new span_id
        """
        return CorrelationContext(
            correlation_id=self.correlation_id,
            span_id=f"span_{uuid.uuid4().hex[:8]}",
            parent_span_id=self.span_id,
            component=component,
        )

    @classmethod
    def create(
        cls,
        correlation_id: Optional[str] = None,
        component: Optional[str] = None,
    ) -> "CorrelationContext":
        """
        Create a new correlation context.

        Args:
            correlation_id: Optional existing correlation ID to reuse
            component: Optional component name

        Returns:
            New CorrelationContext instance
        """
        return cls(
            correlation_id=correlation_id or generate_correlation_id(),
            span_id=f"span_{uuid.uuid4().hex[:8]}",
            component=component,
        )


@contextmanager
def correlation_scope(
    correlation_id: Optional[str] = None,
    component: Optional[str] = None,
) -> Generator[CorrelationContext, None, None]:
    """
    Context manager for establishing a correlation scope.

    Usage:
        with correlation_scope(correlation_id="req_123") as ctx:
            # All code here has access to ctx.correlation_id
            do_something()

        # Or auto-generate:
        with correlation_scope(component="api.users") as ctx:
            print(f"Request ID: {ctx.correlation_id}")

    Args:
        correlation_id: Optional existing correlation ID
        component: Optional component name

    Yields:
        CorrelationContext for the scope
    """
    # Check if we're already in a correlation scope
    parent_ctx = _correlation_context.get()

    if parent_ctx and not correlation_id:
        # Create child context
        ctx = parent_ctx.child(component)
    else:
        # Create new root context
        ctx = CorrelationContext.create(
            correlation_id=correlation_id,
            component=component,
        )

    # Set the context
    token = _correlation_context.set(ctx)
    try:
        yield ctx
    finally:
        # Restore previous context
        _correlation_context.reset(token)


@contextmanager
def child_span(component: Optional[str] = None) -> Generator[CorrelationContext, None, None]:
    """
    Create a child span within the current correlation scope.

    Usage:
        with correlation_scope() as root:
            with child_span("database") as db_span:
                # db_span.parent_span_id == root.span_id
                do_database_work()

    Args:
        component: Optional component name for the child span

    Yields:
        CorrelationContext for the child span

    Raises:
        RuntimeError: If called outside a correlation scope
    """
    parent_ctx = _correlation_context.get()
    if parent_ctx is None:
        raise RuntimeError(
            "child_span() must be called within a correlation_scope(). "
            "Use correlation_scope() first to establish a root context."
        )

    ctx = parent_ctx.child(component)
    token = _correlation_context.set(ctx)
    try:
        yield ctx
    finally:
        _correlation_context.reset(token)


def with_correlation(
    correlation_id: Optional[str] = None,
) -> CorrelationContext:
    """
    Get or create a correlation context.

    If already in a scope, returns current context.
    Otherwise creates a new context (but doesn't set it as current).

    This is useful for decorators and async code where context
    managers are awkward.

    Args:
        correlation_id: Optional correlation ID to use

    Returns:
        Current or new CorrelationContext
    """
    current = _correlation_context.get()
    if current:
        return current
    return CorrelationContext.create(correlation_id=correlation_id)


def inject_correlation(
    correlation_id: str,
    component: Optional[str] = None,
) -> CorrelationContext:
    """
    Inject a correlation ID into the current context.

    Used when receiving a correlation ID from an external source
    (e.g., HTTP header, message queue).

    Args:
        correlation_id: Correlation ID from external source
        component: Optional component name

    Returns:
        The new CorrelationContext (also set as current)
    """
    ctx = CorrelationContext.create(
        correlation_id=correlation_id,
        component=component,
    )
    _correlation_context.set(ctx)
    return ctx


def clear_correlation() -> None:
    """
    Clear the current correlation context.

    Use with caution - typically only needed in tests or
    when explicitly ending a request scope.
    """
    _correlation_context.set(None)
