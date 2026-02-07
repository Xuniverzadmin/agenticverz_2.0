# Layer: L3 — Boundary Adapter (Shim)
# Product: system-wide
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async
# Role: Onboarding gate middleware — policy from hoc_spine/authority/onboarding_policy.py
# Callers: FastAPI app (main.py)
# Reference: PIN-399, ONBOARDING_ENDPOINT_MAP_V1.md

"""
Onboarding Gate Middleware — Shim

Policy (endpoint-to-state mapping) is defined in
app.hoc.cus.hoc_spine.authority.onboarding_policy.
This module provides the middleware class that uses that policy.
"""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.auth.onboarding_state import OnboardingState
from app.hoc.cus.hoc_spine.authority.onboarding_policy import get_required_state  # noqa: F401

logger = logging.getLogger("nova.auth.onboarding_gate")


class OnboardingGateMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces onboarding state requirements.

    MUST run AFTER AuthGatewayMiddleware (needs tenant context).
    Policy tables are in hoc_spine/authority/onboarding_policy.py.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        path = request.url.path
        required_state = get_required_state(path)

        if required_state is None:
            return await call_next(request)

        auth_context = getattr(request.state, "auth_context", None)
        if auth_context is None:
            return await call_next(request)

        tenant_id = getattr(auth_context, "tenant_id", None)
        if tenant_id is None:
            return await call_next(request)

        current_state = await self._get_tenant_state(tenant_id)

        if current_state >= required_state:
            return await call_next(request)

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
        """Get the current onboarding state for a tenant from DB."""
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
            return OnboardingState.CREATED


def is_founder_authenticated(request: Request) -> bool:
    """Check if request is founder-authenticated via FOPS token."""
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context is None:
        return False
    return getattr(auth_context, "is_founder", False) and not getattr(auth_context, "tenant_id", None)
