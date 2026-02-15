# Layer: L4 — hoc_spine Authority
# AUDIENCE: SHARED
# Role: Onboarding gate policy — endpoint-to-state mapping
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Callers: auth/onboarding_gate.py (shim), middleware
# Allowed Imports: HOC onboarding enum only
# Forbidden Imports: FastAPI, Starlette, DB
# Reference: PIN-399, ONBOARDING_ENDPOINT_MAP_V1.md

"""
Onboarding Gate Policy (Canonical)

Defines which onboarding state is required for each endpoint.
All paths use canonical (unversioned) form.

No `/api/v1` paths are included — live route scan confirms 0 mounted
`/api/v1/auth` routes in this environment. Auth callbacks use
canonical paths and are exempt via INFRA_PATHS.

RESOLUTION ORDER:
1. Infra paths → exempt (no gating)
2. Auth-exempt prefixes → exempt
3. Non-tenant prefixes → exempt
4. Exact path match → required state
5. Regex pattern match (first match wins) → required state
6. Default → COMPLETE (fail-safe)

This module contains NO framework imports — it is pure policy data.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingState


# =============================================================================
# EXEMPTIONS
# =============================================================================

# Paths that are part of the auth flow — no tenant context yet
AUTH_EXEMPT_PREFIXES: list[str] = [
    # No /api/v1 paths — live route scan confirms 0 mounted /api/v1/auth routes.
    # Auth callbacks are handled at canonical paths.
]

# Paths that operate outside tenant context entirely
NON_TENANT_PREFIXES: list[str] = [
    "/int/",  # Internal-only APIs (no tenant)
]

# Infrastructure paths — no auth at all
INFRA_PATHS: set[str] = {
    "/health",
    "/healthz",
    "/readyz",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
}


# =============================================================================
# ENDPOINT → STATE MAPPING (Canonical Paths)
# =============================================================================

# Exact path matches — checked first
ENDPOINT_STATE_REQUIREMENTS: dict[str, OnboardingState] = {
    # Section 2: Tenant Bootstrap (CREATED)
    "/tenant": OnboardingState.CREATED,
    "/tenant/health": OnboardingState.CREATED,
    "/tenants/self": OnboardingState.CREATED,
    "/tenants/self/status": OnboardingState.CREATED,
    "/onboarding/status": OnboardingState.CREATED,
    "/onboarding/verify": OnboardingState.CREATED,

    # Section 3: Identity Verified (IDENTITY_VERIFIED)
    # API KEY SURFACE POLICY (UC-002, closed — not deferred):
    # Both /api-keys (read) and /tenant/api-keys (write) require IDENTITY_VERIFIED.
    # Split preserves domain authority (both under api_keys/ directory)
    # while maintaining URL backward compatibility.
    # Reference: GREEN_CLOSURE_PLAN_UC001_UC002 Phase 3
    "/api-keys": OnboardingState.IDENTITY_VERIFIED,
    "/tenant/api-keys": OnboardingState.IDENTITY_VERIFIED,
    "/sdk/instructions": OnboardingState.IDENTITY_VERIFIED,
    "/onboarding/advance/api-key": OnboardingState.IDENTITY_VERIFIED,

    # Section 4: API Key Created (API_KEY_CREATED)
    "/sdk/handshake": OnboardingState.API_KEY_CREATED,
    "/sdk/register": OnboardingState.API_KEY_CREATED,
}

# Pattern matches — checked second (first match wins)
ENDPOINT_PATTERN_REQUIREMENTS: list[Tuple[re.Pattern, OnboardingState]] = [
    # Section 3: Identity Verified
    (re.compile(r"^/api-keys/[^/]+$"), OnboardingState.IDENTITY_VERIFIED),
    (re.compile(r"^/tenant/api-keys(/.*)?$"), OnboardingState.IDENTITY_VERIFIED),

    # Section 5: SDK Connected — customer console and SDK business endpoints
    (re.compile(r"^/guard(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/customer(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/policies(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/policy(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/policy-layer(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/policy-proposals(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/costsim(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/incidents(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/traces(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/activity(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/runs(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/agents(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/workers(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/runtime(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/replay(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/feedback(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/predictions(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/discovery(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/embedding(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/memory(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/tenant/usage$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/tenant/quota(/.*)?$"), OnboardingState.SDK_CONNECTED),
    (re.compile(r"^/cost(/.*)?$"), OnboardingState.SDK_CONNECTED),

    # Section 6: Complete — post-onboarding features
    (re.compile(r"^/billing(/.*)?$"), OnboardingState.COMPLETE),
    (re.compile(r"^/limits(/.*)?$"), OnboardingState.COMPLETE),
    (re.compile(r"^/org/users(/.*)?$"), OnboardingState.COMPLETE),
    (re.compile(r"^/roles(/.*)?$"), OnboardingState.COMPLETE),
    (re.compile(r"^/support(/.*)?$"), OnboardingState.COMPLETE),
    (re.compile(r"^/rbac(/.*)?$"), OnboardingState.COMPLETE),
]


# =============================================================================
# STATE RESOLUTION
# =============================================================================

def get_required_state(path: str) -> Optional[OnboardingState]:
    """
    Get the required onboarding state for a path.

    RESOLUTION ORDER:
    1. Infra paths → None (exempt)
    2. Auth-exempt prefixes → None (exempt)
    3. Non-tenant prefixes → None (exempt)
    4. Exact path match → required state
    5. Regex pattern match (first match wins) → required state
    6. Default → COMPLETE (fail-safe)

    Returns None if the path is exempt from onboarding gating.
    """
    # Step 1: Infra paths
    if path in INFRA_PATHS:
        return None

    # Step 2: Auth-exempt prefixes
    for prefix in AUTH_EXEMPT_PREFIXES:
        if path.startswith(prefix):
            return None

    # Step 3: Non-tenant prefixes
    for prefix in NON_TENANT_PREFIXES:
        if path.startswith(prefix):
            return None

    # Step 4: Exact path match
    if path in ENDPOINT_STATE_REQUIREMENTS:
        return ENDPOINT_STATE_REQUIREMENTS[path]

    # Step 5: Pattern match (first match wins)
    for pattern, state in ENDPOINT_PATTERN_REQUIREMENTS:
        if pattern.match(path):
            return state

    # Step 6: Default to COMPLETE (fail-safe)
    return OnboardingState.COMPLETE


# =============================================================================
# ACTIVATION PREDICATE (UC-002)
# =============================================================================

ACTIVATION_REQUIREMENTS = {
    "project_ready": "Tenant has at least one active project",
    "key_ready": "At least one active API key exists",
    "connector_validated": "At least one connector passed validation",
    "sdk_attested": "SDK handshake completed and persisted",
}


def check_activation_predicate(
    has_project: bool,
    has_api_key: bool,
    has_validated_connector: bool,
    has_sdk_attestation: bool,
) -> tuple[bool, list[str]]:
    """Check whether all activation conditions are met. Returns (pass, missing)."""
    missing = []
    if not has_project:
        missing.append("project_ready")
    if not has_api_key:
        missing.append("key_ready")
    if not has_validated_connector:
        missing.append("connector_validated")
    if not has_sdk_attestation:
        missing.append("sdk_attested")
    return (len(missing) == 0, missing)


__all__ = [
    "AUTH_EXEMPT_PREFIXES",
    "NON_TENANT_PREFIXES",
    "INFRA_PATHS",
    "ENDPOINT_STATE_REQUIREMENTS",
    "ENDPOINT_PATTERN_REQUIREMENTS",
    "get_required_state",
    "ACTIVATION_REQUIREMENTS",
    "check_activation_predicate",
]
