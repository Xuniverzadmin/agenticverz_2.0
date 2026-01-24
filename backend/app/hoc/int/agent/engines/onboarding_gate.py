# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Role: Middleware to enforce onboarding state requirements per endpoint
# Product: system-wide
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async
# Callers: FastAPI app (main.py)
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-399 (Onboarding State Machine v1), ONBOARDING_ENDPOINT_MAP_V1.md


"""
Onboarding Gate Middleware

PIN-399: Enforces onboarding state requirements for all endpoints.

FLOW:
1. Get tenant_id from auth context (set by AuthGatewayMiddleware)
2. Look up tenant's onboarding_state from database
3. Compare against required_state for this endpoint
4. If insufficient: return 403 with structured error
5. If sufficient: proceed to route handler

DESIGN INVARIANTS:
- State is the sole authority (ONBOARD-001)
- No RBAC coupling - this middleware does NOT check permissions
- Founders and customers follow identical rules (ONBOARD-003)
- Unclassified endpoints default to COMPLETE (fail-safe)

RESOLUTION ORDER (must be documented and enforced):
1. Exact path match (ENDPOINT_STATE_REQUIREMENTS)
2. Regex pattern match (ENDPOINT_PATTERN_REQUIREMENTS, first match wins)
3. Default → COMPLETE
"""

from __future__ import annotations

import logging
import re
from typing import Callable, Optional, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .onboarding_state import OnboardingState

logger = logging.getLogger("nova.auth.onboarding_gate")


# =============================================================================
# EXEMPTIONS (Refined per user mandate)
# =============================================================================

# Paths that are part of the auth flow itself - no tenant context yet
AUTH_EXEMPT_PREFIXES = [
    "/api/v1/auth/",  # Auth flow (Clerk callbacks, etc.)
]

# Paths that operate outside tenant context entirely
NON_TENANT_PREFIXES = [
    "/int/",  # Internal-only APIs (no tenant)
]

# Infra paths - no auth at all
INFRA_PATHS = {
    "/health",
    "/healthz",
    "/readyz",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
}


# =============================================================================
# ENDPOINT → STATE MAPPING
# =============================================================================

# Exact path matches - checked first
# Derived from: docs/architecture/ONBOARDING_ENDPOINT_MAP_V1.md
ENDPOINT_STATE_REQUIREMENTS: dict[str, OnboardingState] = {
    # -------------------------------------------------------------------------
    # Section 2: Tenant Bootstrap (CREATED)
    # -------------------------------------------------------------------------
    "/api/v1/tenant": OnboardingState.CREATED,
    "/api/v1/tenant/health": OnboardingState.CREATED,
    "/api/v1/tenants/self": OnboardingState.CREATED,
    "/api/v1/tenants/self/status": OnboardingState.CREATED,
    "/api/v1/onboarding/status": OnboardingState.CREATED,
    "/api/v1/onboarding/verify": OnboardingState.CREATED,

    # -------------------------------------------------------------------------
    # Section 3: Identity Verified (IDENTITY_VERIFIED)
    # -------------------------------------------------------------------------
    "/api/v1/api-keys": OnboardingState.IDENTITY_VERIFIED,
    "/sdk/instructions": OnboardingState.IDENTITY_VERIFIED,
    "/api/v1/onboarding/advance/api-key": OnboardingState.IDENTITY_VERIFIED,

    # -------------------------------------------------------------------------
    # Section 4: API Key Created (API_KEY_CREATED)
    # -------------------------------------------------------------------------
    "/sdk/handshake": OnboardingState.API_KEY_CREATED,
    "/sdk/register": OnboardingState.API_KEY_CREATED,
}


# Pattern matches - checked second (first match wins)
# Order matters: more specific patterns should come first
ENDPOINT_PATTERN_REQUIREMENTS: list[Tuple[re.Pattern, OnboardingState]] = [
    # -------------------------------------------------------------------------
    # Section 3: Identity Verified (IDENTITY_VERIFIED)
    # -------------------------------------------------------------------------
    (re.compile(r"^/api/v1/api-keys/[^/]+$"), OnboardingState.IDENTITY_VERIFIED),

    # -------------------------------------------------------------------------
    # Section 5: SDK Connected (SDK_CONNECTED)
    # Customer console and SDK business endpoints
    # -------------------------------------------------------------------------
    (re.compile(r"^/guard(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/customer(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/policies(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/policy(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/policy-layer(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/policy-proposals(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/costsim(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/incidents(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/traces(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/activity(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/runs(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/agents(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/workers(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/runtime(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/replay(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/feedback(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/predictions(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/discovery(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/embedding(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/memory(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/tenant/usage$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/api/v1/tenant/quota(/.*)?$"), OnboardingState.SDK_CONNECTED),
    # Cost Intelligence endpoints - OBSERVER READ (HISAR-AUTH-001)
    # Note: Router is at /cost/* not /api/v1/cost/*
    (re.compile(r"^/cost(/.*)?$"), OnboardingState.SDK_CONNECTED),

    # -------------------------------------------------------------------------
    # Section 6: Complete (COMPLETE)
    # Post-onboarding features
    # -------------------------------------------------------------------------
    (re.compile(r"^/api/v1/billing(/.*)?$"), OnboardingState.COMPLETE),
    (re.compile(r"^/api/v1/limits(/.*)?$"), OnboardingState.COMPLETE),
    (re.compile(r"^/api/v1/org/users(/.*)?$"), OnboardingState.COMPLETE),
    (re.compile(r"^/api/v1/roles(/.*)?$"), OnboardingState.COMPLETE),
    (re.compile(r"^/api/v1/support(/.*)?$"), OnboardingState.COMPLETE),
    (re.compile(r"^/api/v1/rbac(/.*)?$"), OnboardingState.COMPLETE),
]


# =============================================================================
# STATE RESOLUTION
# =============================================================================

def get_required_state(path: str) -> Optional[OnboardingState]:
    """
    Get the required onboarding state for a path.

    RESOLUTION ORDER (documented per mandate):
    1. Check if path is exempt (infra, auth, non-tenant) → returns None
    2. Exact path match → returns matched state
    3. Regex pattern match (first match wins) → returns matched state
    4. Default → COMPLETE (fail-safe for unclassified endpoints)

    Returns:
        OnboardingState if path requires gating, None if exempt
    """
    # Step 1a: Infra paths - no gating
    if path in INFRA_PATHS:
        return None

    # Step 1b: Auth exempt prefixes - no gating
    for prefix in AUTH_EXEMPT_PREFIXES:
        if path.startswith(prefix):
            return None

    # Step 1c: Non-tenant prefixes - no gating
    for prefix in NON_TENANT_PREFIXES:
        if path.startswith(prefix):
            return None

    # Step 2: Exact path match
    if path in ENDPOINT_STATE_REQUIREMENTS:
        return ENDPOINT_STATE_REQUIREMENTS[path]

    # Step 3: Pattern match (first match wins)
    for pattern, state in ENDPOINT_PATTERN_REQUIREMENTS:
        if pattern.match(path):
            return state

    # Step 4: Default to COMPLETE (fail-safe)
    # Per ONBOARDING_ENDPOINT_MAP_V1.md Section 10:
    # "Any endpoint not listed above is implicitly forbidden until classified"
    return OnboardingState.COMPLETE


# =============================================================================
# MIDDLEWARE
# =============================================================================

class OnboardingGateMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces onboarding state requirements.

    MUST run AFTER AuthGatewayMiddleware (needs tenant context).

    If a request has a tenant_id, onboarding gate applies unless explicitly
    classified as exempt. This rule prevents accidentally exempting future
    endpoints just because they "sound internal".

    Usage in main.py:
        from app.auth.onboarding_gate import OnboardingGateMiddleware

        # Order matters: OnboardingGate added BEFORE Auth (runs after)
        app.add_middleware(OnboardingGateMiddleware)
        app.add_middleware(AuthGatewayMiddleware, ...)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process each request through the onboarding gate.
        """
        path = request.url.path

        # Get required state for this path
        required_state = get_required_state(path)

        # If exempt, proceed
        if required_state is None:
            return await call_next(request)

        # Get auth context (set by AuthGatewayMiddleware)
        auth_context = getattr(request.state, "auth_context", None)
        if auth_context is None:
            # No auth context = public path or auth failed earlier
            # Let the route handler deal with it
            return await call_next(request)

        # Get tenant_id from auth context
        tenant_id = getattr(auth_context, "tenant_id", None)
        if tenant_id is None:
            # No tenant = can't check onboarding state
            # This shouldn't happen for authenticated requests
            # but we proceed and let the endpoint handle it
            return await call_next(request)

        # Look up tenant's current onboarding state
        current_state = await self._get_tenant_state(tenant_id)

        # Check if sufficient (monotonic comparison)
        if current_state >= required_state:
            return await call_next(request)

        # Insufficient state - return structured error
        # Per ONBOARDING_STATE_MACHINE_V1.md Section 6 (Failure Semantics)
        logger.warning(
            "Onboarding state violation: tenant=%s current=%s required=%s endpoint=%s",
            tenant_id,
            current_state.name,
            required_state.name,
            path,
        )

        return JSONResponse(
            status_code=403,
            content={
                "error": "onboarding_state_violation",
                "current_state": current_state.name,
                "required_state": required_state.name,
                "endpoint": path,
            },
        )

    async def _get_tenant_state(self, tenant_id: str) -> OnboardingState:
        """
        Get the current onboarding state for a tenant.

        Queries the database for Tenant.onboarding_state.
        Returns CREATED if tenant not found (fail-safe).
        """
        try:
            from ..db import get_session
            from ..models.tenant import Tenant

            session = next(get_session())
            try:
                tenant = session.get(Tenant, tenant_id)
                if tenant is None:
                    logger.warning("Tenant not found for onboarding check: %s", tenant_id)
                    return OnboardingState.CREATED

                return OnboardingState(tenant.onboarding_state)
            finally:
                session.close()

        except Exception as e:
            logger.error("Failed to get tenant onboarding state: %s", e)
            # Fail-safe: assume CREATED (most restrictive)
            return OnboardingState.CREATED


# =============================================================================
# FOUNDER/FOPS EXEMPTION HANDLING
# =============================================================================

def is_founder_authenticated(request: Request) -> bool:
    """
    Check if request is founder-authenticated via FOPS token.

    NOTE: Per ONBOARD-003, founders follow the same state transitions.
    However, FOPS-authenticated requests operate outside tenant context
    entirely and are not subject to onboarding gating.

    This function is NOT used by the middleware directly.
    The /ops/* paths should go through separate FOPS authentication
    that doesn't set a tenant_id, thus naturally bypassing onboarding checks.
    """
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context is None:
        return False

    # FOPS requests don't have tenant_id
    return getattr(auth_context, "is_founder", False) and not getattr(auth_context, "tenant_id", None)
