# Tenant Context Middleware (M6)
"""
Tenant context propagation for multi-tenancy isolation.

This middleware:
1. Extracts tenant_id from request headers/tokens
2. Propagates tenant context through the request lifecycle
3. Ensures tenant-scoped queries
4. Provides audit context for status_history
"""

from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("nova.middleware.tenant")

# Context variable for tenant context
_tenant_context: ContextVar[Optional["TenantContext"]] = ContextVar("tenant_context", default=None)


@dataclass
class TenantContext:
    """
    Tenant context for the current request.

    Propagated through the request lifecycle via contextvars.
    """

    tenant_id: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None

    # Permissions (populated from token/header)
    permissions: Dict[str, Any] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = {}

    def has_permission(self, permission: str) -> bool:
        """Check if tenant has a specific permission."""
        return bool(self.permissions.get(permission, False))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
        }


def get_tenant_context() -> Optional[TenantContext]:
    """Get the current tenant context."""
    return _tenant_context.get()


def set_tenant_context(context: TenantContext) -> None:
    """Set the current tenant context."""
    _tenant_context.set(context)


def clear_tenant_context() -> None:
    """Clear the current tenant context."""
    _tenant_context.set(None)


def require_tenant_context() -> TenantContext:
    """
    Get the current tenant context, raising if not set.

    Use this in endpoints that require tenant isolation.
    """
    context = get_tenant_context()
    if context is None:
        raise HTTPException(status_code=401, detail="Tenant context required")
    return context


def get_tenant_id() -> Optional[str]:
    """Get the current tenant ID, or None if not in tenant context."""
    context = get_tenant_context()
    return context.tenant_id if context else None


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tenant context propagation.

    Extracts tenant_id from:
    1. X-Tenant-ID header
    2. Authorization token (JWT claim)
    3. Query parameter (for testing only)

    Sets tenant context for the request lifecycle.
    """

    # Header names
    TENANT_ID_HEADER = "X-Tenant-ID"
    USER_ID_HEADER = "X-User-ID"
    CORRELATION_ID_HEADER = "X-Correlation-ID"

    # Paths that don't require tenant context
    EXEMPT_PATHS = {
        "/health",
        "/health/ready",
        "/health/live",
        "/metrics",
        "/docs",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next):
        """Process request and set tenant context."""
        # Skip exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Extract tenant context from headers
        tenant_id = request.headers.get(self.TENANT_ID_HEADER)
        user_id = request.headers.get(self.USER_ID_HEADER)
        correlation_id = request.headers.get(self.CORRELATION_ID_HEADER) or request_id

        # For testing: allow tenant_id in query params
        if not tenant_id:
            tenant_id = request.query_params.get("tenant_id")

        # Create tenant context if tenant_id is present
        if tenant_id:
            context = TenantContext(
                tenant_id=tenant_id,
                user_id=user_id,
                request_id=request_id,
                correlation_id=correlation_id,
            )
            set_tenant_context(context)

            logger.debug(f"Tenant context set: tenant_id={tenant_id}, user_id={user_id}, request_id={request_id}")

        try:
            # Store request_id in request state for logging
            request.state.request_id = request_id
            request.state.tenant_id = tenant_id

            response = await call_next(request)

            # Add correlation headers to response
            response.headers["X-Request-ID"] = request_id
            if correlation_id:
                response.headers["X-Correlation-ID"] = correlation_id

            return response

        finally:
            # Clear tenant context after request
            clear_tenant_context()


def tenant_scoped_query(query, tenant_id: Optional[str] = None):
    """
    Add tenant scope to a SQLModel query.

    Usage:
        query = select(Run)
        query = tenant_scoped_query(query, tenant_id)

    Args:
        query: SQLModel select query
        tenant_id: Tenant ID to scope to (uses context if None)

    Returns:
        Query with tenant_id filter applied
    """
    if tenant_id is None:
        tenant_id = get_tenant_id()

    if tenant_id:
        # Assumes the model has a tenant_id column
        query = query.where(query.column_descriptions[0]["entity"].tenant_id == tenant_id)

    return query


def ensure_tenant_access(entity_tenant_id: Optional[str], action: str = "access") -> None:
    """
    Ensure the current tenant can access an entity.

    Raises HTTPException if tenant doesn't have access.

    Args:
        entity_tenant_id: Tenant ID of the entity
        action: Description of the action for error message
    """
    context = get_tenant_context()

    # No context means public access (for now)
    if context is None:
        return

    # Entity has no tenant (global resource)
    if entity_tenant_id is None:
        return

    # Check tenant match
    if entity_tenant_id != context.tenant_id:
        logger.warning(f"Tenant access denied: context={context.tenant_id}, entity={entity_tenant_id}, action={action}")
        raise HTTPException(status_code=403, detail=f"Access denied: cannot {action} resource from another tenant")


# Decorator for tenant-required endpoints
def require_tenant(func):
    """
    Decorator to require tenant context for an endpoint.

    Usage:
        @router.get("/runs")
        @require_tenant
        async def list_runs():
            context = get_tenant_context()
            ...
    """

    async def wrapper(*args, **kwargs):
        require_tenant_context()
        return await func(*args, **kwargs)

    return wrapper
