# Layer: L3 — Boundary Adapter (Shim)
# Product: system-wide
# Temporal:
#   Trigger: startup
#   Execution: sync
# Role: Gateway configuration — policy from hoc_spine/authority/gateway_policy.py
# Callers: main.py lifespan
# Reference: PIN-306, CAP-006

"""
Gateway Configuration — Shim

Public-path policy is defined in app.hoc.cus.hoc_spine.authority.gateway_policy.
This module provides startup orchestration (configure_auth_gateway, setup_auth_middleware)
and re-exports the policy constants.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI
    from .gateway import AuthGateway

from app.hoc.cus.hoc_spine.authority.gateway_policy import (  # noqa: F401
    AUTH_GATEWAY_ENABLED,
    get_gateway_policy_config,
)

logger = logging.getLogger("nova.auth.gateway_config")


async def configure_auth_gateway() -> "AuthGateway":
    """Configure and return the auth gateway (startup orchestration)."""
    from .api_key_service import get_api_key_service
    from .gateway import configure_auth_gateway as _configure
    from .session_store import get_session_store

    session_store = None
    try:
        session_store = get_session_store()
        is_revoked = await session_store.is_revoked("test_session_init")
        logger.info(
            "session_store_initialized",
            extra={"status": "connected", "test_result": is_revoked},
        )
    except Exception as e:
        logger.warning(f"Session store initialization failed: {e}")
        session_store = None

    api_key_service = None
    try:
        api_key_service = get_api_key_service()
        logger.info("api_key_service_initialized")
    except Exception as e:
        logger.warning(f"API key service initialization failed: {e}")
        api_key_service = None

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
    """Delegate to canonical authority policy."""
    return get_gateway_policy_config()


def setup_auth_middleware(app: "FastAPI") -> None:
    """Add auth gateway middleware to FastAPI app."""
    if not AUTH_GATEWAY_ENABLED:
        logger.info("auth_gateway_disabled", extra={"reason": "AUTH_GATEWAY_ENABLED=false"})
        return

    from .gateway_middleware import AuthGatewayMiddleware

    config = get_gateway_middleware_config()
    app.add_middleware(AuthGatewayMiddleware, **config)
    logger.info("auth_gateway_middleware_added")
