"""
RBAC Middleware with PolicyObject - M7/M8 Implementation

Provides request-level authorization using PolicyObject pattern.
Integrates with JWT claims, machine tokens, and Keycloak OIDC.

Features:
- PolicyObject-based authorization
- Machine token support
- JWT role extraction with JWKS validation (Keycloak)
- Feature flag toggle (RBAC_ENFORCE)
- Prometheus metrics

Usage:
    # In FastAPI app startup
    from app.auth.rbac_middleware import RBACMiddleware

    app.add_middleware(RBACMiddleware)
"""

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .oidc_provider import (
    OIDC_ENABLED,
    TokenValidationError,
    get_roles_from_token,
    map_keycloak_roles_to_aos,
    validate_token,
)

logger = logging.getLogger("nova.auth.rbac_middleware")

# Configuration
RBAC_ENFORCE = os.getenv("RBAC_ENFORCE", "false").lower() == "true"
MACHINE_SECRET_TOKEN = os.getenv("MACHINE_SECRET_TOKEN", "")
JWT_SECRET = os.getenv("JWT_SECRET", "")  # For signature verification (optional)
JWT_VERIFY_SIGNATURE = os.getenv("JWT_VERIFY_SIGNATURE", "false").lower() == "true"

# Prometheus metrics
RBAC_DECISIONS = Counter(
    "rbac_decisions_total",
    "RBAC authorization decisions",
    ["resource", "action", "decision", "reason"]
)
RBAC_LATENCY = Histogram(
    "rbac_latency_seconds",
    "RBAC decision latency",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
)


# ============================================================================
# Policy Objects
# ============================================================================

@dataclass
class PolicyObject:
    """
    Represents an authorization policy for a resource action.

    Attributes:
        resource: Resource type (e.g., "memory_pin", "prometheus")
        action: Action type (e.g., "read", "write", "delete", "admin")
        attrs: Optional additional attributes for context-aware decisions
    """
    resource: str
    action: str
    attrs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    """
    Result of an authorization decision.

    Attributes:
        allowed: Whether the action is permitted
        reason: Human-readable reason for the decision
        roles: Roles that contributed to the decision
        policy: The policy that was evaluated
    """
    allowed: bool
    reason: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    policy: Optional[PolicyObject] = None


# ============================================================================
# RBAC Matrix
# ============================================================================

# Role -> Resource -> Actions mapping
# Replace with dynamic loader from DB or config if needed
RBAC_MATRIX: Dict[str, Dict[str, List[str]]] = {
    "infra": {
        "memory_pin": ["read", "write", "delete", "admin"],
        "prometheus": ["reload", "query"],
        "costsim": ["read", "write", "admin"],
        "policy": ["read", "write", "approve"],
    },
    "admin": {
        "memory_pin": ["read", "write", "delete", "admin"],
        "prometheus": ["reload", "query"],
        "costsim": ["read", "write", "admin"],
        "policy": ["read", "write", "approve"],
    },
    "machine": {
        "memory_pin": ["read", "write"],
        "prometheus": ["reload"],
        "costsim": ["read"],
        "policy": ["read"],
    },
    "dev": {
        "memory_pin": ["read"],
        "prometheus": ["query"],
        "costsim": ["read"],
        "policy": ["read"],
    },
    "readonly": {
        "memory_pin": ["read"],
        "prometheus": ["query"],
        "costsim": ["read"],
        "policy": ["read"],
    },
}


# ============================================================================
# Path to Policy Mapping
# ============================================================================

def get_policy_for_path(path: str, method: str) -> Optional[PolicyObject]:
    """
    Map request path and method to a PolicyObject.

    Returns None for paths that don't require RBAC.
    """
    # Memory pins
    if path.startswith("/api/v1/memory/pins"):
        if path.endswith("/cleanup"):
            return PolicyObject(resource="memory_pin", action="admin")
        elif method == "GET":
            return PolicyObject(resource="memory_pin", action="read")
        elif method in ("POST", "PUT", "PATCH"):
            return PolicyObject(resource="memory_pin", action="write")
        elif method == "DELETE":
            return PolicyObject(resource="memory_pin", action="delete")

    # Prometheus reload
    if path.startswith("/-/reload") or path.startswith("/api/observability/prom-reload"):
        return PolicyObject(resource="prometheus", action="reload")

    # Prometheus query
    if path.startswith("/api/v1/query") or path.startswith("/api/prometheus"):
        return PolicyObject(resource="prometheus", action="query")

    # CostSim
    if path.startswith("/api/v1/costsim"):
        if method == "GET":
            return PolicyObject(resource="costsim", action="read")
        else:
            return PolicyObject(resource="costsim", action="write")

    # Policy API
    if path.startswith("/api/v1/policy"):
        if "/approve" in path or "/reject" in path:
            return PolicyObject(resource="policy", action="approve")
        elif method == "GET":
            return PolicyObject(resource="policy", action="read")
        else:
            return PolicyObject(resource="policy", action="write")

    # No RBAC required for this path
    return None


# ============================================================================
# Role Extraction
# ============================================================================

def extract_roles_from_request(request: Request) -> List[str]:
    """
    Extract roles from request headers.

    Checks in order:
    1. X-Machine-Token header (returns ["machine"] if valid)
    2. Authorization: Bearer <JWT> (validates with OIDC if configured)
    3. X-Roles header (comma-separated, for testing)

    Returns empty list if no valid credentials.
    """
    # Check machine token
    machine_token = (
        request.headers.get("X-Machine-Token") or
        request.headers.get("Authorization-Machine")
    )
    if machine_token and MACHINE_SECRET_TOKEN and machine_token == MACHINE_SECRET_TOKEN:
        logger.debug("Machine token authenticated")
        return ["machine"]

    # Check JWT
    auth_header = request.headers.get("Authorization", "") or ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            # Use OIDC provider for JWT validation (with JWKS if configured)
            if OIDC_ENABLED:
                claims = validate_token(token)
                keycloak_roles = get_roles_from_token(claims)
                aos_roles = map_keycloak_roles_to_aos(keycloak_roles)
                logger.debug(f"OIDC JWT validated, roles: {aos_roles} (from {keycloak_roles})")
                return aos_roles
            else:
                # Fallback: decode without verification (legacy mode)
                if JWT_VERIFY_SIGNATURE and JWT_SECRET:
                    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                else:
                    payload = jwt.decode(token, options={"verify_signature": False})

                roles = payload.get("roles", [])
                if isinstance(roles, str):
                    roles = [roles]
                logger.debug(f"JWT roles extracted (legacy): {roles}")
                return roles

        except TokenValidationError as e:
            logger.warning(f"OIDC token validation failed: {e.message} ({e.error_code})")
            return []
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return []
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return []

    # Check X-Roles header (for testing/dev only)
    roles_header = request.headers.get("X-Roles", "")
    if roles_header:
        roles = [r.strip() for r in roles_header.split(",") if r.strip()]
        logger.debug(f"X-Roles header roles: {roles}")
        return roles

    return []


# ============================================================================
# Enforcement
# ============================================================================

def enforce(policy: PolicyObject, request: Request) -> Decision:
    """
    Evaluate a policy against the request.

    Args:
        policy: The policy to evaluate
        request: The incoming request

    Returns:
        Decision with allowed status and reason
    """
    roles = extract_roles_from_request(request)

    if not roles:
        return Decision(
            allowed=False,
            reason="no-credentials",
            roles=[],
            policy=policy
        )

    # Check each role against the RBAC matrix
    for role in roles:
        role_perms = RBAC_MATRIX.get(role, {})
        allowed_actions = role_perms.get(policy.resource, [])

        if policy.action in allowed_actions:
            return Decision(
                allowed=True,
                reason=f"role:{role}",
                roles=roles,
                policy=policy
            )

    return Decision(
        allowed=False,
        reason="insufficient-permissions",
        roles=roles,
        policy=policy
    )


# ============================================================================
# Middleware
# ============================================================================

class RBACMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware for RBAC enforcement.

    Evaluates policies for protected paths and returns 403 if denied.
    Controlled by RBAC_ENFORCE environment variable.
    """

    def __init__(self, app: ASGIApp, enforce_rbac: Optional[bool] = None):
        super().__init__(app)
        self.enforce_rbac = enforce_rbac if enforce_rbac is not None else RBAC_ENFORCE

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Skip RBAC if disabled
        if not self.enforce_rbac:
            return await call_next(request)

        # Get policy for this path
        path = request.url.path
        method = request.method
        policy = get_policy_for_path(path, method)

        # No policy = no RBAC required
        if policy is None:
            return await call_next(request)

        # Enforce policy
        decision = enforce(policy, request)
        latency = time.time() - start_time

        # Record metrics
        RBAC_DECISIONS.labels(
            resource=policy.resource,
            action=policy.action,
            decision="allowed" if decision.allowed else "denied",
            reason=decision.reason or "unknown"
        ).inc()
        RBAC_LATENCY.observe(latency)

        if not decision.allowed:
            logger.warning(
                "rbac_denied",
                extra={
                    "path": path,
                    "method": method,
                    "resource": policy.resource,
                    "action": policy.action,
                    "reason": decision.reason,
                    "roles": decision.roles,
                }
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "forbidden",
                    "reason": decision.reason,
                    "resource": policy.resource,
                    "action": policy.action,
                }
            )

        logger.debug(
            "rbac_allowed",
            extra={
                "path": path,
                "method": method,
                "resource": policy.resource,
                "action": policy.action,
                "reason": decision.reason,
                "roles": decision.roles,
            }
        )

        return await call_next(request)


# ============================================================================
# Utility Functions
# ============================================================================

def check_permission(
    resource: str,
    action: str,
    request: Request,
    attrs: Optional[Dict[str, Any]] = None
) -> Decision:
    """
    Programmatic permission check (for use in route handlers).

    Example:
        decision = check_permission("memory_pin", "write", request)
        if not decision.allowed:
            raise HTTPException(status_code=403, detail=decision.reason)
    """
    policy = PolicyObject(resource=resource, action=action, attrs=attrs or {})
    return enforce(policy, request)


def require_permission(resource: str, action: str):
    """
    Decorator for requiring specific permissions.

    Example:
        @require_permission("memory_pin", "admin")
        async def admin_endpoint(request: Request):
            ...
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            if RBAC_ENFORCE:
                decision = check_permission(resource, action, request)
                if not decision.allowed:
                    return JSONResponse(
                        status_code=403,
                        content={"error": "forbidden", "reason": decision.reason}
                    )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
