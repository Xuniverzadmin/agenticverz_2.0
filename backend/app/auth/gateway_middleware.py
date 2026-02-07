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

import asyncio
import logging
import os
import re
from typing import Callable, Optional, Sequence

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .contexts import AuthPlane, GatewayContext
from .gateway import AuthGateway, get_auth_gateway
from .gateway_types import GatewayAuthError, is_error
from .rbac_rules_loader import get_public_paths
from .customer_sandbox import try_sandbox_auth, SandboxCustomerPrincipal, is_sandbox_allowed

logger = logging.getLogger("nova.auth.gateway_middleware")

# PIN-391: Environment detection for schema-driven RBAC
_CURRENT_ENVIRONMENT = os.getenv("AOS_ENVIRONMENT", "preflight")


def _get_default_public_paths() -> list[str]:
    """
    Get default public paths from RBAC_RULES.yaml schema (PIN-391).

    Returns paths marked as PUBLIC tier for the current environment.
    Falls back to hoc_spine authority policy if schema loading fails.
    """
    try:
        return get_public_paths(environment=_CURRENT_ENVIRONMENT)
    except Exception as e:
        logger.warning("Failed to load public paths from schema, using authority fallback: %s", e)
        try:
            from app.hoc.cus.hoc_spine.authority.gateway_policy import get_public_paths as authority_paths
            return authority_paths()
        except Exception:
            return ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]


# PIN-391: Schema-driven public paths (loaded at module import)
DEFAULT_PUBLIC_PATHS = _get_default_public_paths()


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

        NOTE: If gateway is None, the singleton is looked up at request time.
        This allows configure_auth_gateway() to be called after middleware setup.
        """
        super().__init__(app)
        # Store explicit gateway, or None to use singleton at request time
        self._explicit_gateway = gateway
        self._public_paths = set(public_paths or DEFAULT_PUBLIC_PATHS)
        self._public_patterns = [re.compile(p) for p in (public_patterns or [])]

    def _get_gateway(self) -> AuthGateway:
        """Get the gateway, using singleton if not explicitly provided."""
        if self._explicit_gateway is not None:
            return self._explicit_gateway
        return get_auth_gateway()

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

        # =================================================================
        # PIN-439: Customer Sandbox Auth (local/test mode only)
        # Check sandbox auth BEFORE normal gateway authentication.
        # This allows local development and CI to simulate real customers.
        # =================================================================
        if is_sandbox_allowed():
            headers_dict = dict(request.headers)
            sandbox_principal = try_sandbox_auth(headers_dict)
            if sandbox_principal is not None:
                logger.info(f"Sandbox auth: path={path}, tenant={sandbox_principal.tenant_id}")
                # Inject sandbox context into request state
                request.state.auth_context = sandbox_principal
                request.state.is_sandbox = True
                # Continue to route handler (skip normal auth)
                return await call_next(request)

        # Extract auth headers
        authorization = request.headers.get("Authorization")
        api_key = request.headers.get("X-AOS-Key")

        # Log auth attempt at debug level
        logger.debug(f"Auth check: path={path}, has_auth={bool(authorization)}, has_key={bool(api_key)}")

        # Veil posture: if no credentials are presented, avoid revealing that a protected surface exists.
        # This is intentionally scoped to unauthenticated probes (not invalid credentials).
        if not authorization and not api_key:
            try:
                from app.hoc.cus.hoc_spine.authority.veil_policy import (
                    deny_as_404_enabled,
                    probe_rate_limit_enabled,
                    probe_rate_per_minute,
                    unauthenticated_http_status_code,
                )

                if deny_as_404_enabled():
                    if probe_rate_limit_enabled():
                        from app.hoc.cus.hoc_spine.services.rate_limiter import get_rate_limiter

                        client_ip = self._get_client_ip(request)
                        key = f"probe:no-cred:{client_ip}"
                        allowed = get_rate_limiter().allow(key, probe_rate_per_minute())
                        if not allowed:
                            # Slow brute-force enumeration without disclosing a distinct status code.
                            await asyncio.sleep(0.5)

                    return JSONResponse(status_code=unauthenticated_http_status_code(), content={"error": "not_found"})
            except Exception:
                # Veil policy must never break auth.
                pass

        # Authenticate through gateway (lookup at request time for proper init order)
        gateway = self._get_gateway()
        result = await gateway.authenticate(
            authorization_header=authorization,
            api_key_header=api_key,
        )

        # Handle errors
        if is_error(result):
            logger.warning(f"Auth failed: path={path}, error={result.error_code}")
            return self._error_response(result)

        # Inject context into request state
        request.state.auth_context = result

        # PIN-399: Trigger onboarding state transition on first human auth
        await self._maybe_advance_onboarding(result)

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
        try:
            from app.hoc.cus.hoc_spine.authority.veil_policy import deny_as_404_enabled, unauthenticated_http_status_code

            if deny_as_404_enabled():
                return JSONResponse(status_code=unauthenticated_http_status_code(), content={"error": "not_found"})
        except Exception:
            # Veil policy must never break auth.
            pass

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

    async def _maybe_advance_onboarding(self, context: GatewayContext) -> None:
        """
        PIN-399: Trigger onboarding state transition on first human auth.

        Called after successful authentication to potentially advance
        a tenant from CREATED to IDENTITY_VERIFIED.

        TRIGGER: First authenticated human request for a tenant.

        This is idempotent - if tenant is already at or past IDENTITY_VERIFIED,
        this is a no-op.
        """
        try:
            # Only trigger for human auth with tenant context
            if context.plane != AuthPlane.HUMAN:
                return

            tenant_id = getattr(context, "tenant_id", None)
            if not tenant_id:
                return

            # Import here to avoid circular dependency
            from .onboarding_transitions import (
                TransitionTrigger,
                get_onboarding_service,
            )

            service = get_onboarding_service()
            result = await service.advance_to_identity_verified(
                tenant_id=tenant_id,
                trigger=TransitionTrigger.FIRST_HUMAN_AUTH,
            )

            if result.success and not result.was_no_op:
                logger.info(
                    "onboarding_advanced_on_first_human_auth",
                    extra={
                        "tenant_id": tenant_id,
                        "from_state": result.from_state.name,
                        "to_state": result.to_state.name,
                    },
                )

        except Exception as e:
            # Onboarding transition failure should not block request
            logger.warning(f"Failed to advance onboarding state: {e}")


def get_auth_context(request: Request) -> Optional[GatewayContext]:
    """
    Get authentication context from request.

    Usage in route handlers:
        from app.auth.gateway_middleware import get_auth_context

        @app.get("/resource")
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

        @app.get("/resource")
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
