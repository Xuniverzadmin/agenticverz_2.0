# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: FastAPI RBAC middleware for request auth
# Callers: main.py, route handlers
# Allowed Imports: None
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Auth Infrastructure

"""
RBAC Middleware with PolicyObject - M7/M8 Implementation

Policy data (RBAC_MATRIX, PolicyObject, Decision, get_policy_for_path) is
defined in app.hoc.cus.hoc_spine.authority.rbac_policy and re-exported here.
This module provides the enforcement logic (enforce()) and middleware class.

Usage:
    from app.auth.rbac_middleware import RBACMiddleware
    app.add_middleware(RBACMiddleware)
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..utils.metrics_helpers import get_or_create_counter, get_or_create_histogram
from .contexts import (
    FounderAuthContext,
    HumanAuthContext,
    MachineCapabilityContext,
    GatewayContext,
)
from .customer_sandbox import SandboxCustomerPrincipal, get_sandbox_capabilities
from .gateway_middleware import get_auth_context
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

# Policy data from hoc_spine authority (canonical source)
from app.hoc.cus.hoc_spine.authority.rbac_policy import (  # noqa: F401
    Decision,
    PolicyObject,
    RBAC_MATRIX,
    get_policy_for_path,
)

# =============================================================================
# PIN-271/273: RBACv1 ↔ RBACv2 Coexistence
# =============================================================================
#
# TERMINOLOGY (LOCKED - PIN-273):
# - RBACv1: This middleware (Enforcement Authority)
# - RBACv2: ActorContext + AuthorizationEngine (Reference Authority)
#
# COEXISTENCE INVARIANTS (MANDATORY):
# 1. RBACv2 MUST NEVER enforce while RBACv1 is active
# 2. RBACv2 MUST ALWAYS run when shadow mode is enabled
# 3. Any discrepancy MUST be observable (log + metric)
# 4. No endpoint may bypass the integration layer
# 5. Promotion is a HUMAN-GOVERNED action, not a code flag
# 6. RBACv1 and RBACv2 MUST NEVER co-decide (no hybrid decisions)
#
# PROMOTION INVARIANT (CRITICAL):
# RBACv2 may only become stricter than RBACv1 during promotion, never more permissive.
# Any v2_more_permissive discrepancy is a security risk requiring immediate investigation.
#
# =============================================================================
RBAC_V2_SHADOW_ENABLED = os.getenv("NEW_AUTH_SHADOW_ENABLED", "true").lower() == "true"
# Backward compat alias
NEW_AUTH_ENABLED = RBAC_V2_SHADOW_ENABLED

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

# PIN-271/273: RBACv1 ↔ RBACv2 comparison metrics
RBAC_V1_V2_COMPARISON = get_or_create_counter(
    "rbac_v1_v2_comparison_total",
    "Comparison between RBACv1 and RBACv2 decisions",
    ["resource", "action", "match", "discrepancy_type", "actor_type"],
)
RBAC_V2_LATENCY = get_or_create_histogram(
    "rbac_v2_latency_seconds",
    "RBACv2 AuthorizationEngine decision latency",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
)
# Backward compat aliases
AUTH_COMPARISON = RBAC_V1_V2_COMPARISON
NEW_AUTH_LATENCY = RBAC_V2_LATENCY


# RBAC_MATRIX, PolicyObject, Decision, get_policy_for_path are imported
# from app.hoc.cus.hoc_spine.authority.rbac_policy (see import block above).
# Middleware is enforcement-only — no path→resource mapping logic lives here.


# ============================================================================
# Capability Derivation from Auth Context (PIN-409 Correct Model)
# ============================================================================
#
# JWT ≠ authority. Backend decides authority.
# This function derives capabilities from request.state.auth_context
# which is set by AuthGatewayMiddleware.
#
# INVARIANT: If auth_context is None, no capabilities are granted.
# INVARIANT: Capabilities come from context type + backend state, never JWT claims.
# INVARIANT: Capabilities are centrally defined, not inline lists.
# ============================================================================


# =============================================================================
# CENTRALIZED CAPABILITY DEFINITIONS (PIN-409 Guardrail #2)
# =============================================================================
# These are the ONLY sources of capability grants.
# No inline lists. No conditional additions. Audit trail is here.
# =============================================================================

# Founder capabilities: Full control-plane access
# Reference: FounderAuthContext has no roles/scopes — type IS authority
FOUNDER_CAPABILITIES: List[str] = [
    # Traces
    "trace:read", "trace:write", "trace:delete", "trace:export",
    # Agents
    "agent:read", "agent:write", "agent:register", "agent:heartbeat", "agent:delete",
    # Runtime
    "runtime:simulate", "runtime:query", "runtime:capabilities",
    # Policy
    "policy:read", "policy:write", "policy:approve",
    # Incidents
    "incident:read", "incident:write", "incident:resolve",
    # Workers
    "worker:read", "worker:run", "worker:stream", "worker:cancel",
    # Memory
    "memory_pin:read", "memory_pin:write", "memory_pin:delete", "memory_pin:admin",
    # Tenant (founder-only)
    "tenant:read", "tenant:write", "tenant:freeze", "tenant:delete",
    # RBAC (founder-only)
    "rbac:read", "rbac:reload", "rbac:audit",
    # Cost simulation
    "costsim:read", "costsim:write", "costsim:admin",
    # Recovery
    "recovery:read", "recovery:write", "recovery:execute", "recovery:suggest",
    # Embedding
    "embedding:read", "embedding:embed", "embedding:query",
    # Killswitch
    "killswitch:read", "killswitch:activate", "killswitch:reset",
    # Integration
    "integration:read", "integration:checkpoint", "integration:resolve",
    # Cost
    "cost:read", "cost:simulate", "cost:forecast",
    # Checkpoint
    "checkpoint:read", "checkpoint:write", "checkpoint:restore",
    # Events
    "event:read", "event:subscribe", "event:publish",
    # Prometheus
    "prometheus:reload", "prometheus:query",
]

# Human (Customer) base capabilities: Standard customer access
# Reference: HumanAuthContext has no permissions field — RBAC decides
# These are granted to all authenticated human users via Clerk JWT
HUMAN_BASE_CAPABILITIES: List[str] = [
    # Traces - core visibility
    "trace:read", "trace:write",
    # Agents - register and monitor
    "agent:read", "agent:register", "agent:heartbeat",
    # Runtime - query and simulate
    "runtime:simulate", "runtime:query", "runtime:capabilities",
    # Policy - read only (write requires approval flow)
    "policy:read",
    # Incidents - read only
    "incident:read",
    # Workers - run and monitor
    "worker:read", "worker:run", "worker:stream",
    # Memory - read only
    "memory_pin:read",
    # Cost simulation - read only
    "costsim:read",
    # Recovery - read only
    "recovery:read",
    # Embedding - read and embed
    "embedding:read", "embedding:embed",
    # Killswitch - read only
    "killswitch:read",
    # Integration - read only
    "integration:read",
    # Cost - read only
    "cost:read",
    # Checkpoint - read only
    "checkpoint:read",
    # Events - read and subscribe
    "event:read", "event:subscribe",
]


def derive_capabilities_from_context(request: Request) -> List[str]:
    """
    Derive capabilities from the authenticated context.

    This is the ONLY source of authorization capabilities.
    JWT claims are NOT used for authorization.
    Capabilities are drawn from centralized constants, not inline lists.

    Returns:
        List of capability strings (e.g., ["trace:read", "trace:write"])
    """
    context = get_auth_context(request)

    if context is None:
        logger.debug("No auth context - no capabilities")
        return []

    # Founder: Full access to everything (control-plane)
    if isinstance(context, FounderAuthContext):
        logger.debug(f"Founder context - full capabilities for {context.actor_id}")
        return FOUNDER_CAPABILITIES

    # Machine: Use scopes from API key (already capability-based)
    if isinstance(context, MachineCapabilityContext):
        logger.debug(f"Machine context - scopes: {context.scopes}")
        return list(context.scopes)

    # Human (Clerk): Standard customer capabilities
    if isinstance(context, HumanAuthContext):
        logger.debug(f"Human context - base capabilities for {context.actor_id}")
        return HUMAN_BASE_CAPABILITIES

    # PIN-440: Sandbox Customer Principal (local/test mode)
    # Uses permission ceiling from customer_sandbox.py for security
    if isinstance(context, SandboxCustomerPrincipal):
        logger.debug(f"Sandbox context - tenant={context.tenant_id}, role={context.role}")
        # Use the canonical capability helper which enforces permission ceiling
        return get_sandbox_capabilities(context)

    logger.warning(f"Unknown context type: {type(context)}")
    return []


def has_capability(capabilities: List[str], required: str) -> bool:
    """
    Check if required capability exists in the list.

    Supports:
    - Exact match: "trace:read"
    - Wildcard: "*" (matches everything)
    - Resource wildcard: "trace:*" (matches trace:read, trace:write, etc.)
    """
    if "*" in capabilities:
        return True
    if required in capabilities:
        return True

    # Check resource wildcard
    parts = required.split(":")
    if len(parts) >= 2:
        resource = parts[0]
        wildcard = f"{resource}:*"
        if wildcard in capabilities:
            return True

    return False


# ============================================================================
# Role Extraction (LEGACY - kept for shadow audit comparison)
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
    logger.info(f"Auth header present: {bool(auth_header)}, starts with Bearer: {auth_header.startswith('Bearer ')}")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            # Use OIDC provider for JWT validation (with JWKS if configured)
            if OIDC_ENABLED:
                claims = validate_token(token)
                logger.info(f"OIDC claims: {list(claims.keys())}")
                logger.info(f"OIDC claim values: sub={claims.get('sub')}, roles={claims.get('roles')}, metadata={claims.get('metadata')}, public_metadata={claims.get('public_metadata')}")
                keycloak_roles = get_roles_from_token(claims)
                aos_roles = map_keycloak_roles_to_aos(keycloak_roles)
                logger.info(f"Extracted roles: keycloak={keycloak_roles}, aos={aos_roles}")
                # No implicit role assignment - if user has no roles, they have no permissions
                # Roles must come from: backend state, lifecycle, or explicit configuration
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

    PIN-409: Primary authorization uses capabilities from auth context.
    JWT contains identity only; backend decides authority.

    INVARIANT: Legacy fallback is ONLY allowed for machine tokens.
    Human requests MUST have auth_context - silent fallback is forbidden.

    Args:
        policy: The policy to evaluate
        request: The incoming request

    Returns:
        Decision with allowed status and reason
    """
    required_capability = f"{policy.resource}:{policy.action}"

    # Debug: Log auth context state for diagnosis
    auth_context = get_auth_context(request)
    context_type = type(auth_context).__name__ if auth_context else None
    logger.info(
        f"RBAC enforce: path={request.url.path} context={context_type} required={required_capability}"
    )

    # PIN-409: Primary path - derive capabilities from auth context
    # Auth context is set by AuthGatewayMiddleware (runs before RBAC)
    capabilities = derive_capabilities_from_context(request)

    # Debug: Log derived capabilities
    if capabilities:
        logger.info(f"RBAC capabilities derived: {capabilities[:5]}... (total={len(capabilities)})")

    if capabilities:
        # Capability-based authorization (correct model)
        if has_capability(capabilities, required_capability):
            logger.debug(f"Capability granted: {required_capability}")
            return Decision(
                allowed=True,
                reason="capability-granted",
                roles=[],  # No roles in capability model
                policy=policy
            )
        else:
            logger.warning(
                f"Capability denied: {required_capability} not in capabilities "
                f"(context={context_type}, path={request.url.path})"
            )
            return Decision(
                allowed=False,
                reason="no-capability",
                roles=[],
                policy=policy
            )

    # =========================================================================
    # GUARDRAIL: Prevent silent authority downgrade (PIN-409)
    # =========================================================================
    # If we reach here, auth_context is None or produced no capabilities.
    # This is ONLY acceptable for legacy machine tokens via X-Machine-Token.
    # Human requests (with Authorization: Bearer) MUST have auth_context.
    # =========================================================================

    auth_header = request.headers.get("Authorization", "")
    machine_token = request.headers.get("X-Machine-Token", "")

    if auth_header.startswith("Bearer ") and not machine_token:
        # Human JWT present but no auth_context — this is a configuration error
        # NOT a silent fallback to legacy roles
        logger.error(
            f"AUTH_CONTEXT_MISSING: Human JWT present but auth_context is None. "
            f"path={request.url.path} — check middleware ordering"
        )
        return Decision(
            allowed=False,
            reason="auth-context-missing",
            roles=[],
            policy=policy
        )

    # Legacy fallback: ONLY for machine tokens via X-Machine-Token header
    # This path is bounded and explicit — not a silent downgrade
    if machine_token:
        logger.debug(f"Legacy machine token fallback for {request.url.path}")
        roles = extract_roles_from_request(request)

        if not roles:
            return Decision(allowed=False, reason="no-credentials", roles=[], policy=policy)

        # Check each role against the RBAC matrix
        for role in roles:
            role_perms = RBAC_MATRIX.get(role, {})
            allowed_actions = role_perms.get(policy.resource, [])

            if policy.action in allowed_actions:
                return Decision(allowed=True, reason=f"legacy-role:{role}", roles=roles, policy=policy)

        return Decision(allowed=False, reason="insufficient-permissions", roles=roles, policy=policy)

    # No valid auth mechanism detected
    return Decision(allowed=False, reason="no-credentials", roles=[], policy=policy)


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
        # PIN-271/273: RBACv1 ↔ RBACv2 REFERENCE MODE COMPARISON
        #
        # INVARIANTS (enforced here):
        # - RBACv1 (this block above) is Enforcement Authority
        # - RBACv2 (this block) is Reference Authority only
        # - RBACv2 result is NEVER used for enforcement decisions
        # - All discrepancies are logged + metriced
        # - v2_more_permissive is a security alert
        # =====================================================================
        if RBAC_V2_SHADOW_ENABLED:
            try:
                v2_start = time.time()

                # Import here to avoid circular imports
                from .rbac_integration import (
                    authorize_with_v2_engine,
                    build_fallback_actor_from_v1_roles,
                    compare_decisions,
                    extract_actor_from_request,
                    log_decision_comparison,
                )

                # Extract actor using RBACv2 identity chain
                actor = await extract_actor_from_request(request)

                # Fallback: use RBACv1 roles if RBACv2 chain didn't extract
                if actor is None and decision.roles:
                    actor = build_fallback_actor_from_v1_roles(decision.roles, request)
                    if actor:
                        from .authorization import get_authorization_engine

                        engine = get_authorization_engine()
                        actor = engine.compute_permissions(actor)

                # Get RBACv2 authorization decision (Reference Mode only)
                v2_result = authorize_with_v2_engine(actor, policy)
                v2_latency_ms = (time.time() - v2_start) * 1000

                # Compare RBACv1 vs RBACv2 decisions
                comparison = compare_decisions(decision, v2_result, policy)

                # Log comparison for analysis
                log_decision_comparison(comparison, path, method)

                # Get actor type for metrics
                actor_type = actor.actor_type.value if actor else "anonymous"

                # Record comparison metrics
                RBAC_V1_V2_COMPARISON.labels(
                    resource=policy.resource,
                    action=policy.action,
                    match="yes" if comparison.match else "no",
                    discrepancy_type=comparison.discrepancy_type or "none",
                    actor_type=actor_type,
                ).inc()
                RBAC_V2_LATENCY.observe(v2_latency_ms / 1000)

                # Log detailed comparison for mismatch debugging
                # CRITICAL: v2_more_permissive is a security risk
                if not comparison.match:
                    log_level = logging.WARNING if comparison.discrepancy_type == "v2_more_permissive" else logging.INFO
                    logger.log(
                        log_level,
                        "rbac_v1_v2_discrepancy",
                        extra={
                            "path": path,
                            "method": method,
                            "v1_allowed": comparison.v1_allowed,
                            "v2_allowed": comparison.v2_allowed,
                            "v1_reason": comparison.v1_reason,
                            "v2_reason": comparison.v2_reason,
                            "discrepancy_type": comparison.discrepancy_type,
                            "actor_id": comparison.actor_id,
                            "actor_type": actor_type,
                            "resource": comparison.resource,
                            "action": comparison.action,
                            "roles": decision.roles,
                            # Security flag for v2_more_permissive
                            "security_alert": comparison.discrepancy_type == "v2_more_permissive",
                        },
                    )

            except Exception as e:
                # RBACv2 errors must not affect RBACv1 enforcement flow
                logger.warning(
                    "rbac_v2_shadow_error",
                    extra={
                        "path": path,
                        "method": method,
                        "error": str(e),
                    },
                    exc_info=True,
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
            try:
                from app.hoc.cus.hoc_spine.authority.veil_policy import unauthorized_http_status_code

                status_code = unauthorized_http_status_code()
                if status_code == 404:
                    return JSONResponse(status_code=404, content={"error": "not_found"})
            except Exception:
                # Veil policy must never break RBAC enforcement.
                pass

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
