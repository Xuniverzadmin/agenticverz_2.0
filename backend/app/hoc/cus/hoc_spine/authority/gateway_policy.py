# capability_id: CAP-011
# Layer: L4 — hoc_spine Authority
# AUDIENCE: SHARED
# Role: Gateway public-path policy — canonical path exemptions for auth gateway
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Callers: auth/gateway_config.py, middleware
# Allowed Imports: None (pure policy)
# Forbidden Imports: FastAPI, Starlette, DB
# Reference: CAP-006, PIN-391

"""
Gateway Public-Path Policy (Canonical)

Defines which request paths are exempt from authentication.
All paths use canonical (unversioned) form.

No `/api/v1` paths are included — live route scan confirms 0 mounted
`/api/v1/auth` routes in this environment.

This module contains NO framework imports — it is pure policy data.
"""

from __future__ import annotations

import os

# Feature flag (env-based, no framework dependency)
AUTH_GATEWAY_ENABLED: bool = os.getenv("AUTH_GATEWAY_ENABLED", "true").lower() == "true"


# ============================================================================
# Public Path Exemptions (Canonical)
# ============================================================================
#
# Paths listed here bypass authentication entirely.
# PIN-391: These should ultimately come from RBAC_RULES.yaml.
#
# INVARIANTS:
# - /health, /metrics: system probes, no sensitive data
# - /docs, /openapi.json: OpenAPI spec, no sensitive data
# ============================================================================

PUBLIC_PATHS: list[str] = [
    # System health & observability
    "/health",
    "/healthz",
    "/metrics",
    # OpenAPI / documentation
    "/docs",
    "/redoc",
    "/openapi.json",
    # Debug endpoints (PIN-444)
    "/__debug/openapi_nocache",
    "/__debug/openapi_inspect",
    # -----------------------------------------------------------------------
    # SDSR preflight public paths (canonical)
    # -----------------------------------------------------------------------
    "/policy-proposals",
    "/policy-proposals/",
    "/cost/",
    "/cost/summary",
    "/cost/by-feature",
    "/cost/by-model",
    "/cost/anomalies",
    "/cost/dashboard",
    "/cost/by-user",
    "/cost/projection",
    "/cost/budgets",
    "/policy-layer/",
    "/feedback",
    "/feedback/",
    "/predictions",
    "/predictions/",
    "/recovery/",
    "/discovery",
    "/discovery/",
    "/tenants/",
    "/traces",
    "/traces/",
    "/guard/",
    "/guard/logs",
    "/guard/logs/",
    "/logs/",
    "/agents/",
    "/ops/",
    "/ops/actions/audit",
    "/ops/actions/audit/",
    "/status_history",
    "/status_history/",
    "/integration/",
    "/billing/status",
    "/rbac/audit",
    "/rbac/audit/",
    # "/cus/" removed — PR2: CUS endpoints require gateway auth (PIN-578)
    # -----------------------------------------------------------------------
    # Founder routes (FOPS auth via gateway, PIN-336/398)
    # -----------------------------------------------------------------------
    "/fdr/",
    "/platform/",
    # -----------------------------------------------------------------------
    # SDK endpoints (API key auth at route level, PIN-399)
    # -----------------------------------------------------------------------
    "/sdk/",
    # -----------------------------------------------------------------------
    # Onboarding endpoints (gateway auth at route level, PIN-399)
    # -----------------------------------------------------------------------
    "/onboarding/",
    # -----------------------------------------------------------------------
    # Stagetest evidence console (TODO: Re-enable auth)
    # -----------------------------------------------------------------------
    "/hoc/api/stagetest/",
    # -----------------------------------------------------------------------
    # Legacy 410 routes (must be public to return 410 without auth)
    # -----------------------------------------------------------------------
    "/dashboard",
    "/operator",
    "/operator/",
    "/demo",
    "/demo/",
    "/simulation",
    "/simulation/",
]

PUBLIC_PATTERNS: list[str] = [
    # Static assets
    r"^/static/.*",
    # OpenAPI
    r"^/openapi\.json$",
]


def get_public_paths() -> list[str]:
    """Return the canonical public path exemption list."""
    return list(PUBLIC_PATHS)


def get_public_patterns() -> list[str]:
    """Return the canonical public pattern list."""
    return list(PUBLIC_PATTERNS)


def get_gateway_policy_config() -> dict:
    """
    Return kwargs for AuthGatewayMiddleware initialization.

    This is the canonical source of gateway public-path policy.
    """
    return {
        "public_paths": get_public_paths(),
        "public_patterns": get_public_patterns(),
    }


__all__ = [
    "AUTH_GATEWAY_ENABLED",
    "PUBLIC_PATHS",
    "PUBLIC_PATTERNS",
    "get_public_paths",
    "get_public_patterns",
    "get_gateway_policy_config",
]
