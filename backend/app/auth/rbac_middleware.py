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
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..utils.metrics_helpers import get_or_create_counter, get_or_create_histogram
from .oidc_provider import (
    OIDC_ENABLED,
    TokenValidationError,
    get_roles_from_token,
    map_keycloak_roles_to_aos,
    validate_token,
)
from .shadow_audit import (
    record_shadow_audit_metric,
    shadow_aggregator,
    shadow_audit,
)

logger = logging.getLogger("nova.auth.rbac_middleware")

# Configuration
RBAC_ENFORCE = os.getenv("RBAC_ENFORCE", "false").lower() == "true"
MACHINE_SECRET_TOKEN = os.getenv("MACHINE_SECRET_TOKEN", "")
JWT_SECRET = os.getenv("JWT_SECRET", "")  # For signature verification (optional)
JWT_VERIFY_SIGNATURE = os.getenv("JWT_VERIFY_SIGNATURE", "false").lower() == "true"

# Prometheus metrics - using idempotent registration (PIN-120 PREV-1)
RBAC_DECISIONS = get_or_create_counter(
    "rbac_decisions_total", "RBAC authorization decisions", ["resource", "action", "decision", "reason"]
)
RBAC_LATENCY = get_or_create_histogram(
    "rbac_latency_seconds", "RBAC decision latency", buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
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
# PIN-169: Expanded to 14 resources with founder/operator roles
# Replace with dynamic loader from DB or config if needed
RBAC_MATRIX: Dict[str, Dict[str, List[str]]] = {
    # =========================================================================
    # FOUNDER-SCOPED ROLES (Isolated - never flow through tenant RBAC)
    # =========================================================================
    "founder": {
        # Full global access - nuclear privilege
        "memory_pin": ["read", "write", "delete", "admin"],
        "prometheus": ["reload", "query"],
        "costsim": ["read", "write", "admin"],
        "policy": ["read", "write", "approve"],
        "agent": ["read", "write", "register", "heartbeat", "delete"],
        "runtime": ["simulate", "query", "capabilities"],
        "recovery": ["read", "write", "execute", "suggest"],
        "worker": ["read", "run", "stream", "cancel"],
        "trace": ["read", "write", "delete", "export"],
        "embedding": ["read", "embed", "query"],
        "killswitch": ["read", "activate", "reset"],
        "integration": ["read", "checkpoint", "resolve"],
        "cost": ["read", "simulate", "forecast"],
        "checkpoint": ["read", "write", "restore"],
        "event": ["read", "subscribe", "publish"],
        "incident": ["read", "write", "resolve"],
        # Founder-only resources
        "tenant": ["read", "write", "freeze", "delete"],
        "rbac": ["read", "reload", "audit"],
    },
    "operator": {
        # Scoped ops access
        "memory_pin": ["read", "write"],
        "prometheus": ["reload", "query"],
        "costsim": ["read", "write"],
        "policy": ["read", "write"],
        "agent": ["read", "write", "register", "heartbeat"],
        "runtime": ["simulate", "query", "capabilities"],
        "recovery": ["read", "write", "execute"],
        "worker": ["read", "run", "stream"],
        "trace": ["read", "write", "export"],
        "embedding": ["read", "embed", "query"],
        "killswitch": ["read", "activate"],
        "integration": ["read", "checkpoint", "resolve"],
        "cost": ["read", "simulate"],
        "checkpoint": ["read", "write", "restore"],
        "event": ["read", "subscribe"],
        "incident": ["read", "write", "resolve"],
        # Operator can read tenants but not modify
        "tenant": ["read"],
        "rbac": ["read"],
    },
    # =========================================================================
    # TENANT-SCOPED ROLES
    # =========================================================================
    "infra": {
        "memory_pin": ["read", "write", "delete", "admin"],
        "prometheus": ["reload", "query"],
        "costsim": ["read", "write", "admin"],
        "policy": ["read", "write", "approve"],
        "agent": ["read", "write", "register", "heartbeat", "delete"],
        "runtime": ["simulate", "query", "capabilities"],
        "recovery": ["read", "write", "execute", "suggest"],
        "worker": ["read", "run", "stream", "cancel"],
        "trace": ["read", "write", "delete", "export"],
        "embedding": ["read", "embed", "query"],
        "killswitch": ["read", "activate", "reset"],
        "integration": ["read", "checkpoint", "resolve"],
        "cost": ["read", "simulate", "forecast"],
        "checkpoint": ["read", "write", "restore"],
        "event": ["read", "subscribe", "publish"],
        "incident": ["read", "write", "resolve"],
        "rbac": ["read"],
    },
    "admin": {
        "memory_pin": ["read", "write", "delete", "admin"],
        "prometheus": ["reload", "query"],
        "costsim": ["read", "write", "admin"],
        "policy": ["read", "write", "approve"],
        "agent": ["read", "write", "register", "heartbeat"],
        "runtime": ["simulate", "query", "capabilities"],
        "recovery": ["read", "write", "execute"],
        "worker": ["read", "run", "stream"],
        "trace": ["read", "write", "export"],
        "embedding": ["read", "embed", "query"],
        "killswitch": ["read", "activate"],
        "integration": ["read", "checkpoint", "resolve"],
        "cost": ["read", "simulate"],
        "checkpoint": ["read", "write", "restore"],
        "event": ["read", "subscribe"],
        "incident": ["read", "write"],
        "rbac": ["read"],
    },
    # MACHINE: Strictly scoped for integration/automation tokens
    # INVARIANT: Machine keys are escape risks. Lock down tightly.
    # NEVER: tenant, rbac, policy (mutations), killswitch (mutations)
    "machine": {
        "memory_pin": ["read"],  # Read only - no write for machine keys
        "prometheus": ["query"],  # Query only - no reload
        "costsim": ["read"],
        "policy": [],  # DENIED - policy mutation is admin-only
        "agent": ["read", "heartbeat"],  # No register/write - that's console action
        "runtime": ["simulate", "query", "capabilities"],  # Core machine use case
        "recovery": ["read"],  # Read only - execute requires human
        "worker": ["read", "run", "stream"],  # Run jobs - core use case
        "trace": ["read", "write"],  # Tracing is allowed
        "embedding": ["read", "embed"],  # Embedding is allowed
        "killswitch": [],  # DENIED - killswitch is human-only
        "integration": ["read"],  # Read only
        "cost": ["read"],
        "checkpoint": ["read"],  # Read only - write requires human
        "event": ["read", "subscribe"],  # No publish - that's system action
        "incident": ["read"],
        # EXPLICIT DENIALS (for clarity):
        "tenant": [],  # NEVER - tenant mutation is founder/admin only
        "rbac": [],  # NEVER - RBAC mutation is admin only
    },
    "dev": {
        "memory_pin": ["read"],
        "prometheus": ["query"],
        "costsim": ["read"],
        "policy": ["read"],
        "agent": ["read", "register", "heartbeat"],
        "runtime": ["simulate", "query", "capabilities"],
        "recovery": ["read"],
        "worker": ["read", "run", "stream"],
        "trace": ["read"],
        "embedding": ["read", "embed"],
        "killswitch": ["read"],
        "integration": ["read"],
        "cost": ["read"],
        "checkpoint": ["read"],
        "event": ["read", "subscribe"],
        "incident": ["read"],
    },
    "readonly": {
        "memory_pin": ["read"],
        "prometheus": ["query"],
        "costsim": ["read"],
        "policy": ["read"],
        "agent": ["read"],
        "runtime": ["query", "capabilities"],
        "recovery": ["read"],
        "worker": ["read"],
        "trace": ["read"],
        "embedding": ["read"],
        "killswitch": ["read"],
        "integration": ["read"],
        "cost": ["read"],
        "checkpoint": ["read"],
        "event": ["read"],
        "incident": ["read"],
    },
}


# ============================================================================
# Path to Policy Mapping
# ============================================================================


def get_policy_for_path(path: str, method: str) -> Optional[PolicyObject]:
    """
    Map request path and method to a PolicyObject.

    PIN-169: Expanded to cover all 14+ resources.
    Returns None ONLY for explicitly public paths.
    """
    # =========================================================================
    # PUBLIC PATHS (No RBAC required)
    #
    # SECURITY INVARIANTS for public paths:
    # - /health: No sensitive data, system status only
    # - /metrics: GLOBAL metrics, NO tenant_id in labels (see Prometheus section)
    # - /api/v1/auth/: Login flow, unauthenticated by definition
    # - /docs: OpenAPI spec, no sensitive data
    # =========================================================================
    PUBLIC_PATHS = [
        "/health",
        "/metrics",  # MUST remain tenant-agnostic (see security note above)
        "/api/v1/auth/",  # Login/register endpoints
        "/docs",
        "/openapi.json",
        "/redoc",
    ]

    for public_path in PUBLIC_PATHS:
        if path.startswith(public_path) or path == public_path.rstrip("/"):
            return None

    # =========================================================================
    # MEMORY PINS (/api/v1/memory/pins)
    # =========================================================================
    if path.startswith("/api/v1/memory/pins"):
        if path.endswith("/cleanup"):
            return PolicyObject(resource="memory_pin", action="admin")
        elif method == "GET":
            return PolicyObject(resource="memory_pin", action="read")
        elif method in ("POST", "PUT", "PATCH"):
            return PolicyObject(resource="memory_pin", action="write")
        elif method == "DELETE":
            return PolicyObject(resource="memory_pin", action="delete")

    # =========================================================================
    # PROMETHEUS & METRICS
    #
    # SECURITY POSTURE:
    # 1. /metrics endpoint is PUBLIC (no auth) - standard Prometheus scrape
    # 2. Metrics are GLOBAL - no tenant-scoped data in labels
    # 3. /-/reload requires "prometheus:reload" permission (infra+)
    # 4. Query endpoints require "prometheus:query" permission
    #
    # TENANT LEAKAGE: Metrics MUST NOT contain tenant_id in labels.
    # If metrics become tenant-aware, they MUST move behind RBAC.
    # =========================================================================
    if path.startswith("/-/reload") or path.startswith("/api/observability/prom-reload"):
        return PolicyObject(resource="prometheus", action="reload")

    if path.startswith("/api/v1/query") or path.startswith("/api/prometheus"):
        return PolicyObject(resource="prometheus", action="query")

    # =========================================================================
    # COSTSIM (/api/v1/costsim)
    # =========================================================================
    if path.startswith("/api/v1/costsim"):
        if method == "GET":
            return PolicyObject(resource="costsim", action="read")
        else:
            return PolicyObject(resource="costsim", action="write")

    # =========================================================================
    # POLICY (/api/v1/policy)
    # =========================================================================
    if path.startswith("/api/v1/policy"):
        if "/approve" in path or "/reject" in path:
            return PolicyObject(resource="policy", action="approve")
        elif method == "GET":
            return PolicyObject(resource="policy", action="read")
        else:
            return PolicyObject(resource="policy", action="write")

    # =========================================================================
    # AGENTS (/api/v1/agents)
    # =========================================================================
    if path.startswith("/api/v1/agents"):
        if "/heartbeat" in path:
            return PolicyObject(resource="agent", action="heartbeat")
        elif "/register" in path:
            return PolicyObject(resource="agent", action="register")
        elif method == "GET":
            return PolicyObject(resource="agent", action="read")
        elif method == "POST":
            return PolicyObject(resource="agent", action="write")
        elif method in ("PUT", "PATCH"):
            return PolicyObject(resource="agent", action="write")
        elif method == "DELETE":
            return PolicyObject(resource="agent", action="delete")

    # =========================================================================
    # RUNTIME (/api/v1/runtime)
    # =========================================================================
    if path.startswith("/api/v1/runtime"):
        if "/simulate" in path:
            return PolicyObject(resource="runtime", action="simulate")
        elif "/capabilities" in path:
            return PolicyObject(resource="runtime", action="capabilities")
        elif "/query" in path or method == "GET":
            return PolicyObject(resource="runtime", action="query")
        else:
            return PolicyObject(resource="runtime", action="query")

    # =========================================================================
    # RECOVERY (/api/v1/recovery)
    # =========================================================================
    if path.startswith("/api/v1/recovery"):
        if "/execute" in path or "/apply" in path:
            return PolicyObject(resource="recovery", action="execute")
        elif "/suggest" in path:
            return PolicyObject(resource="recovery", action="suggest")
        elif method == "GET":
            return PolicyObject(resource="recovery", action="read")
        elif method in ("POST", "PUT", "PATCH"):
            return PolicyObject(resource="recovery", action="write")

    # =========================================================================
    # WORKERS (/api/v1/workers)
    # =========================================================================
    if path.startswith("/api/v1/workers"):
        if "/run" in path or "/execute" in path:
            return PolicyObject(resource="worker", action="run")
        elif "/stream" in path:
            return PolicyObject(resource="worker", action="stream")
        elif "/cancel" in path or "/stop" in path:
            return PolicyObject(resource="worker", action="cancel")
        elif method == "GET":
            return PolicyObject(resource="worker", action="read")

    # =========================================================================
    # TRACES (/api/v1/traces)
    # =========================================================================
    if path.startswith("/api/v1/traces"):
        if "/export" in path:
            return PolicyObject(resource="trace", action="export")
        elif method == "GET":
            return PolicyObject(resource="trace", action="read")
        elif method in ("POST", "PUT", "PATCH"):
            return PolicyObject(resource="trace", action="write")
        elif method == "DELETE":
            return PolicyObject(resource="trace", action="delete")

    # =========================================================================
    # EMBEDDING (/api/v1/embedding)
    # =========================================================================
    if path.startswith("/api/v1/embedding"):
        # Check /query and /search FIRST (more specific than base /embedding)
        if "/query" in path or "/search" in path:
            return PolicyObject(resource="embedding", action="query")
        # Then check /embed endpoint (POST only) - use path.endswith to avoid matching /embedding
        elif path.endswith("/embed") and method == "POST":
            return PolicyObject(resource="embedding", action="embed")
        elif method == "GET":
            return PolicyObject(resource="embedding", action="read")
        # POST to base /embedding for embed
        elif method == "POST":
            return PolicyObject(resource="embedding", action="embed")

    # =========================================================================
    # KILLSWITCH (/v1/killswitch, /api/v1/killswitch)
    # =========================================================================
    if "/killswitch" in path:
        if "/activate" in path or "/engage" in path:
            return PolicyObject(resource="killswitch", action="activate")
        elif "/reset" in path or "/disengage" in path:
            return PolicyObject(resource="killswitch", action="reset")
        else:
            return PolicyObject(resource="killswitch", action="read")

    # =========================================================================
    # INTEGRATION (/integration, /api/v1/integration)
    # =========================================================================
    if "/integration" in path:
        # Check /resolve FIRST (more specific - appears in /checkpoints/123/resolve)
        if "/resolve" in path:
            return PolicyObject(resource="integration", action="resolve")
        elif "/checkpoint" in path:
            return PolicyObject(resource="integration", action="checkpoint")
        elif method == "GET":
            return PolicyObject(resource="integration", action="read")

    # =========================================================================
    # COST (/cost, /api/v1/cost)
    # =========================================================================
    if "/cost" in path and not "/costsim" in path:
        if "/simulate" in path:
            return PolicyObject(resource="cost", action="simulate")
        elif "/forecast" in path:
            return PolicyObject(resource="cost", action="forecast")
        else:
            return PolicyObject(resource="cost", action="read")

    # =========================================================================
    # CHECKPOINTS (/api/v1/checkpoints)
    # =========================================================================
    if path.startswith("/api/v1/checkpoints"):
        if "/restore" in path:
            return PolicyObject(resource="checkpoint", action="restore")
        elif method == "GET":
            return PolicyObject(resource="checkpoint", action="read")
        elif method in ("POST", "PUT", "PATCH"):
            return PolicyObject(resource="checkpoint", action="write")

    # =========================================================================
    # EVENTS (/api/v1/events)
    # =========================================================================
    if path.startswith("/api/v1/events"):
        if "/subscribe" in path:
            return PolicyObject(resource="event", action="subscribe")
        elif "/publish" in path and method == "POST":
            return PolicyObject(resource="event", action="publish")
        else:
            return PolicyObject(resource="event", action="read")

    # =========================================================================
    # INCIDENTS (/api/v1/incidents)
    # =========================================================================
    if path.startswith("/api/v1/incidents") or "/incidents" in path:
        if "/resolve" in path:
            return PolicyObject(resource="incident", action="resolve")
        elif method == "GET":
            return PolicyObject(resource="incident", action="read")
        elif method in ("POST", "PUT", "PATCH"):
            return PolicyObject(resource="incident", action="write")

    # =========================================================================
    # RBAC (/api/v1/rbac)
    # =========================================================================
    if path.startswith("/api/v1/rbac"):
        if "/reload" in path:
            return PolicyObject(resource="rbac", action="reload")
        elif "/audit" in path:
            return PolicyObject(resource="rbac", action="audit")
        else:
            return PolicyObject(resource="rbac", action="read")

    # =========================================================================
    # TENANTS (/api/v1/tenants)
    # =========================================================================
    if path.startswith("/api/v1/tenants"):
        if "/freeze" in path:
            return PolicyObject(resource="tenant", action="freeze")
        elif method == "GET":
            return PolicyObject(resource="tenant", action="read")
        elif method == "POST":
            return PolicyObject(resource="tenant", action="write")
        elif method == "DELETE":
            return PolicyObject(resource="tenant", action="delete")

    # =========================================================================
    # RUNS (/api/v1/runs) - Maps to worker resource
    # =========================================================================
    if path.startswith("/api/v1/runs"):
        if method == "GET":
            return PolicyObject(resource="worker", action="read")
        elif method == "POST":
            return PolicyObject(resource="worker", action="run")

    # =========================================================================
    # V1 PROXY ROUTES (/v1/chat, /v1/embeddings, /v1/status)
    # =========================================================================
    if path.startswith("/v1/"):
        # Chat/completions
        if "/chat" in path or "/completions" in path:
            return PolicyObject(resource="runtime", action="simulate")
        # Embeddings
        if "/embeddings" in path:
            return PolicyObject(resource="embedding", action="embed")
        # Status
        if "/status" in path:
            return PolicyObject(resource="runtime", action="query")
        # Policies
        if "/policies" in path:
            return PolicyObject(resource="policy", action="read")
        # Demo/replay
        if "/demo" in path or "/replay" in path:
            return PolicyObject(resource="trace", action="read")

    # =========================================================================
    # CUSTOMER ROUTES (/customer/*) - Phase 4C-2 Customer Visibility
    # PRE-RUN declarations and outcome reconciliation
    # =========================================================================
    if path.startswith("/customer/"):
        if "/pre-run" in path:
            return PolicyObject(resource="runtime", action="query")
        elif "/acknowledge" in path:
            return PolicyObject(resource="runtime", action="query")
        elif "/outcome" in path:
            return PolicyObject(resource="runtime", action="query")
        elif "/declaration" in path:
            return PolicyObject(resource="runtime", action="query")
        else:
            return PolicyObject(resource="runtime", action="query")

    # =========================================================================
    # GUARD ROUTES (/guard/*) - Customer Console
    # These are handled by console_auth, but we still map them for shadow audit
    # =========================================================================
    if path.startswith("/guard/"):
        if "/costs" in path:
            return PolicyObject(resource="cost", action="read")
        elif "/incidents" in path:
            return PolicyObject(resource="incident", action="read")
        else:
            # Default guard access
            return PolicyObject(resource="runtime", action="query")

    # =========================================================================
    # OPS ROUTES (/ops/*) - Founder Console
    # These are handled by fops_auth, but we still map them for shadow audit
    # =========================================================================
    if path.startswith("/ops/"):
        if "/cost" in path:
            return PolicyObject(resource="cost", action="read")
        elif "/customers" in path or "/tenants" in path:
            return PolicyObject(resource="tenant", action="read")
        elif "/incidents" in path:
            return PolicyObject(resource="incident", action="read")
        elif "/actions" in path:
            return PolicyObject(resource="tenant", action="write")
        else:
            # Default ops access
            return PolicyObject(resource="runtime", action="query")

    # =========================================================================
    # CATCH-ALL: Unknown paths default to runtime:query
    # This ensures no path returns None for protected routes
    # =========================================================================
    # Log unknown paths for visibility
    logger.debug(f"rbac_unknown_path: {path} {method} - defaulting to runtime:query")
    return PolicyObject(resource="runtime", action="query")


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
    machine_token = request.headers.get("X-Machine-Token") or request.headers.get("Authorization-Machine")
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
        return Decision(allowed=False, reason="no-credentials", roles=[], policy=policy)

    # Check each role against the RBAC matrix
    for role in roles:
        role_perms = RBAC_MATRIX.get(role, {})
        allowed_actions = role_perms.get(policy.resource, [])

        if policy.action in allowed_actions:
            return Decision(allowed=True, reason=f"role:{role}", roles=roles, policy=policy)

    return Decision(allowed=False, reason="insufficient-permissions", roles=roles, policy=policy)


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

        # Get policy for this path (needed for shadow audit even if RBAC disabled)
        path = request.url.path
        method = request.method
        policy = get_policy_for_path(path, method)

        # No policy = no RBAC required (public path)
        if policy is None:
            return await call_next(request)

        # Evaluate policy (always, for shadow audit)
        decision = enforce(policy, request)
        latency_ms = (time.time() - start_time) * 1000

        # Get client IP for audit
        client_ip = request.client.host if request.client else "unknown"

        # Determine principal info from decision context
        principal_type = "anonymous"
        if "machine" in decision.roles:
            principal_type = "machine"
        elif decision.roles:
            principal_type = "console"  # Has roles from JWT/header

        # Get primary role for audit
        primary_role = decision.roles[0] if decision.roles else "none"

        # =====================================================================
        # SHADOW AUDIT - Always record, regardless of enforcement mode
        # This is the data source for rollout gates
        # =====================================================================
        would_block = not decision.allowed

        # Log to shadow audit
        shadow_audit.log_decision(
            path=path,
            method=method,
            resource=policy.resource,
            action=policy.action,
            decision="allowed" if decision.allowed else "denied",
            reason=decision.reason or "policy-matched",
            roles=decision.roles,
            would_block=would_block,
            principal_type=principal_type,
            client_ip=client_ip,
            evaluation_ms=latency_ms,
        )

        # Record to aggregator (for rollout gate calculations)
        shadow_aggregator.record_decision(
            principal_type=principal_type,
            role=primary_role,
            resource=policy.resource,
            action=policy.action,
            would_block=would_block,
            reason=decision.reason or "",
        )

        # Record Prometheus metrics
        record_shadow_audit_metric(
            resource=policy.resource,
            action=policy.action,
            decision="allowed" if decision.allowed else "denied",
            would_block=would_block,
        )

        # =====================================================================
        # ENFORCEMENT - Only if RBAC_ENFORCE=true
        # =====================================================================
        if not self.enforce_rbac:
            # Shadow mode: log but allow
            return await call_next(request)

        # Record enforcement metrics
        RBAC_DECISIONS.labels(
            resource=policy.resource,
            action=policy.action,
            decision="allowed" if decision.allowed else "denied",
            reason=decision.reason or "unknown",
        ).inc()
        RBAC_LATENCY.observe(latency_ms / 1000)  # Convert back to seconds

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
                },
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "forbidden",
                    "reason": decision.reason,
                    "resource": policy.resource,
                    "action": policy.action,
                },
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
            },
        )

        return await call_next(request)


# ============================================================================
# Utility Functions
# ============================================================================


def check_permission(resource: str, action: str, request: Request, attrs: Optional[Dict[str, Any]] = None) -> Decision:
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
                    return JSONResponse(status_code=403, content={"error": "forbidden", "reason": decision.reason})
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
