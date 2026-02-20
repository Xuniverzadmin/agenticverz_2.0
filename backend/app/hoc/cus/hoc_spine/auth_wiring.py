# capability_id: CAP-011
# Layer: L4 — HOC Spine (Wiring)
# Product: system-wide
# Temporal:
#   Trigger: startup + api
#   Execution: sync/async
# Role: Single import point for main.py auth integration — aggregates from
#       authority (pure policy) and auth shims (middleware/orchestration).
# Callers: app/main.py
# Reference: STREAMLINE_HOC_PLAN_V1.md Stream 2 Batch 2.3

"""
Auth Wiring — main.py Import Aggregator

Provides a single import surface for main.py so it never imports from
``app.auth`` directly. All policy lives in ``hoc_spine/authority/``;
middleware and startup orchestration live in ``app/auth/`` shims that
delegate to authority modules.

This module re-exports the concrete symbols main.py needs:
  - AUTH_GATEWAY_ENABLED        (from authority.gateway_policy)
  - configure_auth_gateway      (from auth.gateway_config — startup orchestration)
  - setup_auth_middleware        (from auth.gateway_config — startup orchestration)
  - RBACMiddleware              (from auth.rbac_middleware — Starlette middleware)
  - OnboardingGateMiddleware    (from auth.onboarding_gate — Starlette middleware)
  - verify_api_key              (from auth — FastAPI dependency)
"""

from __future__ import annotations

# Pure policy — no framework imports
from app.hoc.cus.hoc_spine.authority.gateway_policy import (  # noqa: F401
    AUTH_GATEWAY_ENABLED,
)

# Startup orchestration (needs FastAPI/session store/API key service)
from app.auth.gateway_config import (  # noqa: F401
    configure_auth_gateway,
    setup_auth_middleware,
)

# Middleware classes (need Starlette BaseHTTPMiddleware)
from app.auth.rbac_middleware import RBACMiddleware  # noqa: F401
from app.auth.onboarding_gate import OnboardingGateMiddleware  # noqa: F401

# FastAPI dependency (X-AOS-Key header validation)
from app.auth import verify_api_key  # noqa: F401

__all__ = [
    "AUTH_GATEWAY_ENABLED",
    "configure_auth_gateway",
    "setup_auth_middleware",
    "RBACMiddleware",
    "OnboardingGateMiddleware",
    "verify_api_key",
]
