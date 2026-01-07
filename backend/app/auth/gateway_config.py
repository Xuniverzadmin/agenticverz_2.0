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
            # FOUNDER ROUTES (PIN-336)
            # These routes use dedicated FOPS auth via verify_fops_token.
            # Gateway is bypassed; route handlers enforce FOPS token/key auth.
            # =================================================================
            "/founder/",  # Contract review, evidence review
            "/ops/",  # Ops console actions (freeze, throttle, override)
            "/platform/",  # Platform health (founder-only)
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

    Usage:
        from app.auth.gateway_config import setup_auth_middleware

        # In main.py, after app creation:
        setup_auth_middleware(app)
    """
    if not AUTH_GATEWAY_ENABLED:
        logger.info("auth_gateway_disabled", extra={"reason": "AUTH_GATEWAY_ENABLED=false"})
        return

    from .gateway import get_auth_gateway
    from .gateway_middleware import AuthGatewayMiddleware

    config = get_gateway_middleware_config()
    gateway = get_auth_gateway()

    app.add_middleware(
        AuthGatewayMiddleware,
        gateway=gateway,
        **config,
    )

    logger.info("auth_gateway_middleware_added")
