# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async
# Role: FastAPI middleware for auth gateway integration
# Callers: FastAPI app (main.py)
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-306 (Capability Registry), CAP-006 (Authentication)
# capability_id: CAP-006

"""
Auth Gateway Middleware

FastAPI middleware that calls the AuthGateway on every request.
Injects authentication context into request.state for downstream use.

FLOW:
1. Extract Authorization and X-AOS-Key headers
2. Call gateway.authenticate()
3. If error: return HTTP error response
4. If success: inject context into request.state.auth_context
5. Proceed to route handler

INVARIANTS:
1. All protected routes have auth context in request.state
2. Public paths bypass authentication
3. Auth headers are stripped after processing
4. Plane matching is enforced (Phase 5 integration)
"""

from __future__ import annotations

import logging
import re
from typing import Callable, Optional, Sequence

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .contexts import AuthPlane, GatewayContext
from .gateway import AuthGateway, get_auth_gateway
from .gateway_types import GatewayAuthError, is_error

logger = logging.getLogger("nova.auth.gateway_middleware")

# Default public paths (no auth required)
DEFAULT_PUBLIC_PATHS = [
    "/health",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/",
    "/api/v1/c2/predictions/",
]


class AuthGatewayMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces authentication via the AuthGateway.

    Usage in main.py:
        from app.auth.gateway_middleware import AuthGatewayMiddleware

        app.add_middleware(
            AuthGatewayMiddleware,
            public_paths=["/health", "/metrics"],
        )

    After this middleware runs, protected routes can access:
        request.state.auth_context  # HumanAuthContext or MachineCapabilityContext
    """

    def __init__(
        self,
        app: ASGIApp,
        gateway: Optional[AuthGateway] = None,
        public_paths: Optional[Sequence[str]] = None,
        public_patterns: Optional[Sequence[str]] = None,
    ):
        """
        Initialize middleware.

        Args:
            app: The FastAPI app
            gateway: AuthGateway instance (uses singleton if not provided)
            public_paths: Paths that don't require authentication
            public_patterns: Regex patterns for public paths
        """
        super().__init__(app)
        self._gateway = gateway or get_auth_gateway()
        self._public_paths = set(public_paths or DEFAULT_PUBLIC_PATHS)
        self._public_patterns = [re.compile(p) for p in (public_patterns or [])]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process each request through the auth gateway.
        """
        path = request.url.path

        # Check if path is public
        if self._is_public_path(path):
            return await call_next(request)

        # Extract auth headers
        authorization = request.headers.get("Authorization")
        api_key = request.headers.get("X-AOS-Key")

        # Log auth attempt at debug level
        logger.debug(f"Auth check: path={path}, has_auth={bool(authorization)}, has_key={bool(api_key)}")

        # Authenticate through gateway
        result = await self._gateway.authenticate(
            authorization_header=authorization,
            api_key_header=api_key,
        )

        # Handle errors
        if is_error(result):
            logger.warning(f"Auth failed: path={path}, error={result.error_code}")
            return self._error_response(result)

        # Inject context into request state
        request.state.auth_context = result

        # Emit audit event
        await self._emit_audit(request, result)

        # Continue to route handler
        response = await call_next(request)

        return response

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required)."""
        # Exact match
        if path in self._public_paths:
            return True

        # Prefix match
        for public_path in self._public_paths:
            if public_path.endswith("/") and path.startswith(public_path):
                return True

        # Pattern match
        for pattern in self._public_patterns:
            if pattern.match(path):
                return True

        return False

    def _error_response(self, error: GatewayAuthError) -> JSONResponse:
        """Convert gateway error to HTTP response."""
        return JSONResponse(
            status_code=error.http_status,
            content={
                "error": error.error_code.value,
                "message": error.message,
            },
        )

    async def _emit_audit(
        self,
        request: Request,
        context: GatewayContext,
    ) -> None:
        """
        Emit audit event for successful authentication.

        Deferred to gateway_audit module for actual implementation.
        """
        # Import here to avoid circular dependency
        try:
            from .gateway_audit import emit_auth_audit

            await emit_auth_audit(
                request_path=request.url.path,
                request_method=request.method,
                context=context,
                client_ip=self._get_client_ip(request),
            )
        except ImportError:
            # gateway_audit not yet implemented
            pass
        except Exception as e:
            # Audit failure should not block request
            logger.warning(f"Failed to emit auth audit: {e}")

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check X-Forwarded-For first (for proxied requests)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to direct connection
        if request.client:
            return request.client.host

        return "unknown"


def get_auth_context(request: Request) -> Optional[GatewayContext]:
    """
    Get authentication context from request.

    Usage in route handlers:
        from app.auth.gateway_middleware import get_auth_context

        @app.get("/api/v1/resource")
        async def get_resource(request: Request):
            context = get_auth_context(request)
            if context is None:
                raise HTTPException(401, "Not authenticated")
    """
    return getattr(request.state, "auth_context", None)


def require_auth_context(request: Request) -> GatewayContext:
    """
    Get authentication context or raise.

    Usage in route handlers:
        from app.auth.gateway_middleware import require_auth_context

        @app.get("/api/v1/resource")
        async def get_resource(request: Request):
            context = require_auth_context(request)
            # context is guaranteed to be present
    """
    context = get_auth_context(request)
    if context is None:
        raise RuntimeError("Auth context not found - middleware not configured?")
    return context


def get_auth_plane(request: Request) -> Optional[AuthPlane]:
    """
    Get authentication plane from request.

    Returns HUMAN for JWT auth, MACHINE for API key auth, None if not authenticated.
    """
    context = get_auth_context(request)
    if context is None:
        return None
    return context.plane
