# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Role: Tenant context injection middleware
# Product: system-wide
# Temporal:
#   Trigger: api (every request)
#   Execution: sync
# Callers: main.py middleware chain
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Core Security

# Tenancy Middleware
# Enforces tenant_id on all requests and provides tenant context


import logging
import os
from typing import Callable

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("nova.middleware.tenancy")

# Header name for tenant identification
TENANT_HEADER = os.getenv("TENANT_HEADER", "X-Tenant-Id")


def _get_tenant_bypass_paths() -> set[str]:
    """
    Get paths that don't require tenant context (PIN-391).

    These are infrastructure/system paths that are inherently tenant-agnostic.
    Uses RBAC schema PUBLIC paths as base, plus infrastructure-specific paths.
    """
    try:
        from app.auth.rbac_rules_loader import get_public_paths

        environment = os.getenv("AOS_ENVIRONMENT", "preflight")
        schema_paths = set(get_public_paths(environment=environment))

        # Add infrastructure-specific paths not in RBAC schema
        # These are health/version endpoints that exist outside API layer
        infra_paths = {
            "/healthz",
            "/healthz/worker_pool",
            "/version",
        }
        return schema_paths | infra_paths
    except Exception as e:
        logger.warning("Failed to load tenant bypass paths from schema, using fallback: %s", e)
        # Fallback for resilience
        return {
            "/health",
            "/healthz",
            "/healthz/worker_pool",
            "/metrics",
            "/version",
            "/openapi.json",
            "/docs",
            "/redoc",
        }


# PIN-391: Schema-driven tenant bypass paths
PUBLIC_PATHS = _get_tenant_bypass_paths()


class TenancyMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce multi-tenancy on all requests.

    Extracts tenant_id from header and attaches to request.state.
    Rejects requests without valid tenant_id (except public paths).
    """

    def __init__(self, app, enforce: bool = True):
        """Initialize tenancy middleware.

        Args:
            app: FastAPI application
            enforce: If True, reject requests without tenant_id.
                     If False, allow but log warning.
        """
        super().__init__(app)
        self.enforce = enforce

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path

        # Skip public paths
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        # Extract tenant from header
        tenant_id = request.headers.get(TENANT_HEADER)

        if not tenant_id:
            if self.enforce:
                logger.warning("missing_tenant_id", extra={"path": path, "method": request.method})
                raise HTTPException(status_code=401, detail=f"Missing required header: {TENANT_HEADER}")
            else:
                # Default tenant for development/migration
                tenant_id = "default"
                logger.debug("using_default_tenant", extra={"path": path})

        # Attach tenant to request state for use in handlers
        request.state.tenant_id = tenant_id

        # Process request
        response = await call_next(request)

        # Add tenant to response headers for debugging
        response.headers["X-Tenant-Id"] = tenant_id

        return response


def get_tenant_id(request: Request) -> str:
    """Get tenant_id from request state.

    Use this in route handlers to access the current tenant.

    Args:
        request: FastAPI request object

    Returns:
        Tenant ID string

    Raises:
        HTTPException: If tenant_id not set (middleware not applied)
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=500, detail="Tenant context not available")
    return tenant_id
