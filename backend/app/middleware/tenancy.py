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

# Paths that don't require tenant context
PUBLIC_PATHS = {
    "/health",
    "/healthz",
    "/healthz/worker_pool",
    "/metrics",
    "/version",
    "/openapi.json",
    "/docs",
    "/redoc",
}


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
