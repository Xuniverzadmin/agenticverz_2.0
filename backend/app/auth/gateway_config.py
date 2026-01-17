# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: startup
#   Execution: sync
# Role: Gateway configuration and initialization
# Callers: main.py lifespan
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-306 (Capability Registry), CAP-006 (Authentication)
# capability_id: CAP-006

"""
Gateway Configuration

Configures and initializes the Auth Gateway with all dependencies.
Called during application startup to wire together:
- Session revocation store (Redis)
- API key validation service (Database)
- Gateway singleton

This module provides a single entry point for gateway setup.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

    from .gateway import AuthGateway

logger = logging.getLogger("nova.auth.gateway_config")

# Feature flags
AUTH_GATEWAY_ENABLED = os.getenv("AUTH_GATEWAY_ENABLED", "true").lower() == "true"


async def configure_auth_gateway() -> "AuthGateway":
    """
    Configure and return the auth gateway.

    Call this during application startup (in lifespan).
    Returns the configured gateway singleton.

    Usage in main.py:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            gateway = await configure_auth_gateway()
            app.state.auth_gateway = gateway
            yield
    """
    from .api_key_service import get_api_key_service
    from .gateway import configure_auth_gateway as _configure
    from .session_store import get_session_store

    # Initialize session store
    session_store = None
    try:
        session_store = get_session_store()
        # Test connection by checking a dummy session
        is_revoked = await session_store.is_revoked("test_session_init")
        logger.info(
            "session_store_initialized",
            extra={"status": "connected", "test_result": is_revoked},
        )
    except Exception as e:
        logger.warning(f"Session store initialization failed: {e}")
        session_store = None

    # Initialize API key service
    api_key_service = None
    try:
        api_key_service = get_api_key_service()
        logger.info("api_key_service_initialized")
    except Exception as e:
        logger.warning(f"API key service initialization failed: {e}")
        api_key_service = None

    # Configure gateway with dependencies
    gateway = _configure(
        session_store=session_store,
        api_key_service=api_key_service,
    )

    logger.info(
        "auth_gateway_configured",
        extra={
            "session_store": "enabled" if session_store else "disabled",
            "api_key_service": "enabled" if api_key_service else "disabled",
        },
    )

    return gateway


def get_gateway_middleware_config() -> dict:
    """
    Get configuration for AuthGatewayMiddleware.

    Returns kwargs for middleware initialization.

    NOTE (PIN-391): Public paths should ultimately come from RBAC_RULES.yaml
    via get_public_paths(). This hardcoded list exists for backward compatibility.

    NOTE: Legacy/deprecated routes (410 handlers) are NOT listed here.
    Those belong in app/api/legacy_routes.py per layer separation rules.
    """
    return {
        "public_paths": [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            # Auth endpoints (self-service)
            "/api/v1/auth/",
            # C2 Predictions (public advisory)
            "/api/v1/c2/predictions/",
            # =================================================================
            # REMOVED: /api/v1/activity - SDSR should use customer API
            # Customer Activity API at /api/v1/customer/activity requires auth
            # =================================================================
            # =================================================================
            # REMOVED: /api/v1/incidents - now requires auth via unified facade
            # Customer Incidents API at /api/v1/incidents requires auth
            # =================================================================
            # =================================================================
            # SDSR Logs/Traces API (PIN-407)
            # REMOVED from public paths - traces MUST require authentication
            # PIN-409: JWT proves identity, backend decides authority
            # Auth context must be set for capability-based authorization
            # =================================================================
            # "/api/v1/traces",   # REMOVED - requires auth
            # "/api/v1/traces/",  # REMOVED - requires auth
            # "/api/v1/logs",     # REMOVED - requires auth
            # "/api/v1/logs/",    # REMOVED - requires auth
            # =================================================================
            # SDSR Policy Proposals API (PIN-373)
            # Used for preflight SDSR validation.
            # =================================================================
            "/api/v1/policy-proposals",
            "/api/v1/policy-proposals/",
            # =================================================================
            # SDSR Cost Intelligence API (PIN-427)
            # Used for preflight SDSR validation of cost panels.
            # =================================================================
            "/cost/",
            "/cost/summary",
            "/cost/by-feature",
            "/cost/by-model",
            "/cost/anomalies",
            "/cost/dashboard",
            "/cost/by-user",
            "/cost/projection",
            "/cost/budgets",
            # =================================================================
            # SDSR Policy Layer API (PIN-427)
            # Used for preflight SDSR validation of policy panels.
            # =================================================================
            "/policy-layer/",
            # =================================================================
            # SDSR Feedback/Predictions API (PIN-427)
            # Used for preflight SDSR validation of signal panels.
            # =================================================================
            "/api/v1/feedback",
            "/api/v1/feedback/",
            "/api/v1/predictions",
            "/api/v1/predictions/",
            # =================================================================
            # SDSR Recovery API (PIN-427)
            # Used for preflight SDSR validation of recovery panels.
            # =================================================================
            "/api/v1/recovery/",
            # =================================================================
            # SDSR Discovery API (PIN-427)
            # Used for preflight SDSR validation of discovery panels.
            # =================================================================
            "/api/v1/discovery",
            "/api/v1/discovery/",
            # =================================================================
            # SDSR Tenant API (PIN-427)
            # Used for preflight SDSR validation of tenant panels.
            # =================================================================
            "/api/v1/tenants/",
            # =================================================================
            # SDSR Traces API (PIN-427)
            # Used for preflight SDSR validation of logs panels.
            # =================================================================
            "/api/v1/traces",
            "/api/v1/traces/",
            "/api/v1/runtime/traces",
            "/api/v1/runtime/traces/",
            # =================================================================
            # SDSR Guard API (PIN-427)
            # Used for preflight SDSR validation of guard panels.
            # =================================================================
            "/api/v1/guard/",
            "/guard/logs",
            "/guard/logs/",
            # =================================================================
            # SDSR Agents API (PIN-427)
            # Used for preflight SDSR validation of agent panels.
            # =================================================================
            "/api/v1/agents/",
            # =================================================================
            # SDSR Ops API (PIN-427)
            # Used for preflight SDSR validation of ops panels.
            # =================================================================
            "/api/v1/ops/",
            "/ops/actions/audit",
            "/ops/actions/audit/",
            # =================================================================
            # SDSR Status/Integration API (PIN-427)
            # Used for preflight SDSR validation of status panels.
            # =================================================================
            "/status_history",
            "/status_history/",
            "/integration/",
            "/billing/status",
            # =================================================================
            # SDSR RBAC Audit API (PIN-427)
            # Used for preflight SDSR validation of audit panels.
            # =================================================================
            "/api/v1/rbac/audit",
            "/api/v1/rbac/audit/",
            # =================================================================
            # SDSR Customer Activity API (PIN-427)
            # Used for preflight SDSR validation of customer panels.
            # =================================================================
            "/api/v1/customer/",
            # =================================================================
            # FOUNDER ROUTES (PIN-336, PIN-398)
            # PIN-398: Founder routes now go through the gateway for FOPS auth.
            # Gateway routes FOPS tokens (iss=agenticverz-fops) to FounderAuthContext.
            # Route handlers use verify_fops_token which checks isinstance().
            # =================================================================
            "/founder/",  # Contract review, evidence review (FOPS auth via gateway)
            # "/ops/",  # PIN-398: REMOVED - now goes through gateway for FOPS auth
            "/platform/",  # Platform health (founder-only)
            # =================================================================
            # SDK ENDPOINTS (PIN-399)
            # Auth handled by API key gateway at route level.
            # =================================================================
            "/sdk/",
            # =================================================================
            # ONBOARDING ENDPOINTS (PIN-399)
            # Auth handled by gateway at route level.
            # =================================================================
            "/api/v1/onboarding/",
            # =================================================================
            # HEALTHZ ENDPOINT (Kubernetes liveness probe)
            # =================================================================
            "/healthz",
            # =================================================================
            # LEGACY ROUTES (PIN-153)
            # These routes return 410 Gone - must be public to return 410
            # without auth. Route handlers return intentional 410 responses.
            # =================================================================
            "/dashboard",
            "/operator",
            "/operator/",
            "/demo",
            "/demo/",
            "/simulation",
            "/simulation/",
            "/api/v1/operator",
            "/api/v1/operator/",
        ],
        "public_patterns": [
            # Static assets
            r"^/static/.*",
            # OpenAPI
            r"^/openapi\.json$",
        ],
    }


def setup_auth_middleware(app: "FastAPI") -> None:
    """
    Add auth gateway middleware to FastAPI app.

    Call this during app setup, BEFORE RBAC middleware.

    NOTE: Gateway is NOT passed explicitly here. The middleware will
    look up the singleton at request time, allowing configure_auth_gateway()
    to be called in lifespan after middleware setup.

    Usage:
        from app.auth.gateway_config import setup_auth_middleware

        # In main.py, after app creation:
        setup_auth_middleware(app)
    """
    if not AUTH_GATEWAY_ENABLED:
        logger.info("auth_gateway_disabled", extra={"reason": "AUTH_GATEWAY_ENABLED=false"})
        return

    from .gateway_middleware import AuthGatewayMiddleware

    config = get_gateway_middleware_config()

    # Don't pass gateway - middleware will use singleton at request time
    # This allows configure_auth_gateway() in lifespan to properly inject api_key_service
    app.add_middleware(
        AuthGatewayMiddleware,
        **config,
    )

    logger.info("auth_gateway_middleware_added")
