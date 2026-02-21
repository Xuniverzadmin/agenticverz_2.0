# capability_id: CAP-012
# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Role: Billing enforcement gate
# Product: system-wide
# Temporal:
#   Trigger: request
#   Execution: sync
# Callers: FastAPI middleware, route dependencies
# Allowed Imports: L4 (bridges, state, limits)
# Forbidden Imports: L1, L5, L6 (must route through L4)
# Reference: PIN-401 Track A (Production Wiring), PIN-520 Phase 1


"""
Billing Gate Middleware

Enforces billing state and limits at request boundaries.

DESIGN RULES:
- Pure wiring - no new billing logic
- Calls existing provider methods via L4 bridge
- Respects BILLING-001 (never blocks onboarding)
- Respects BILLING-003 (doesn't affect roles)

ENFORCEMENT SURFACE:
- SDK execution paths (usage counting)
- Resource creation endpoints

EXEMPT PATHS:
- Health/metrics
- Auth endpoints
- Founder endpoints
- Onboarding endpoints (BILLING-001)
- Docs

PIN-520 Phase 1: Routes billing provider access through L4 account bridge.
"""

from dataclasses import dataclass
from typing import Optional
from fastapi import Request, HTTPException
import logging

from app.billing.state import BillingState
from app.billing.plan import Plan
from app.billing.limits import Limits
# PIN-520 Phase 1: Route through L4 bridge instead of direct L5 import
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.account_bridge import (
    get_account_bridge,
)
from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingState

logger = logging.getLogger(__name__)


def _get_billing_provider():
    """Get billing provider via L4 bridge (PIN-520 compliance)."""
    bridge = get_account_bridge()
    return bridge.billing_provider_capability()


# Paths exempt from billing enforcement
EXEMPT_PREFIXES: tuple[str, ...] = (
    "/health",
    "/metrics",
    "/fdr/",
    "/docs",
    "/openapi.json",
    "/redoc",
)


@dataclass
class BillingContext:
    """
    Billing context for a request.

    Attributes:
        tenant_id: The tenant identifier
        billing_state: Current billing state
        plan: Current plan
        limits: Derived limits
        allows_usage: Whether billing allows usage
        is_applicable: Whether billing is applicable (onboarding complete)
        is_exempt: Whether this path is exempt
    """

    tenant_id: str
    billing_state: BillingState
    plan: Plan
    limits: Limits
    allows_usage: bool
    is_applicable: bool
    is_exempt: bool


def is_exempt_path(path: str) -> bool:
    """Check if path is exempt from billing enforcement."""
    return path.startswith(EXEMPT_PREFIXES)


class BillingGate:
    """
    Billing enforcement gate (ASGI middleware).

    Checks billing state and limits at the middleware level.

    Usage:
        app.add_middleware(BillingGate)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive, send)
        path = request.url.path

        # Check exemption
        if is_exempt_path(path):
            await self.app(scope, receive, send)
            return

        # Get tenant_id
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            await self.app(scope, receive, send)
            return

        # Check onboarding state - BILLING-001: billing never blocks onboarding
        onboarding_state = getattr(request.state, "onboarding_state", None)
        if onboarding_state is None or onboarding_state != OnboardingState.COMPLETE:
            await self.app(scope, receive, send)
            return

        # Get billing state
        provider = _get_billing_provider()
        billing_state = provider.get_billing_state(tenant_id)

        # Check if usage is allowed
        if not billing_state.allows_usage():
            logger.warning(
                f"Billing gate blocked request for tenant {tenant_id} "
                f"(billing_state={billing_state.name})"
            )
            response = {
                "error": "billing_suspended",
                "billing_state": billing_state.name,
                "message": f"Usage not allowed in {billing_state.name} billing state",
                "next_action": "contact_support",
            }
            await self._send_error(send, 402, response)
            return

        await self.app(scope, receive, send)

    async def _send_error(self, send, status_code: int, body: dict):
        """Send JSON error response."""
        import json

        body_bytes = json.dumps(body).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(body_bytes)).encode()],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body_bytes,
        })


# =============================================================================
# FASTAPI DEPENDENCIES
# =============================================================================


def check_billing(request: Request) -> BillingContext:
    """
    FastAPI dependency: Get billing context for current request.

    Returns BillingContext with state, plan, and limits.
    Does NOT raise - caller decides how to handle.

    BILLING-001: Returns neutral context if onboarding not complete.
    """
    from app.billing.plan import DEFAULT_PLAN
    from app.billing.limits import DEFAULT_LIMITS

    path = request.url.path

    # Check exemption
    if is_exempt_path(path):
        return BillingContext(
            tenant_id="",
            billing_state=BillingState.TRIAL,
            plan=DEFAULT_PLAN,
            limits=DEFAULT_LIMITS,
            allows_usage=True,
            is_applicable=False,
            is_exempt=True,
        )

    # Get tenant_id
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        return BillingContext(
            tenant_id="unknown",
            billing_state=BillingState.TRIAL,
            plan=DEFAULT_PLAN,
            limits=DEFAULT_LIMITS,
            allows_usage=True,
            is_applicable=False,
            is_exempt=False,
        )

    # Check onboarding state - BILLING-001
    onboarding_state = getattr(request.state, "onboarding_state", None)
    is_applicable = (
        onboarding_state is not None
        and onboarding_state == OnboardingState.COMPLETE
    )

    if not is_applicable:
        return BillingContext(
            tenant_id=tenant_id,
            billing_state=BillingState.TRIAL,
            plan=DEFAULT_PLAN,
            limits=DEFAULT_LIMITS,
            allows_usage=True,
            is_applicable=False,
            is_exempt=False,
        )

    # Get real billing context
    provider = _get_billing_provider()
    billing_state = provider.get_billing_state(tenant_id)
    plan = provider.get_plan(tenant_id)
    limits = provider.get_limits(plan)

    return BillingContext(
        tenant_id=tenant_id,
        billing_state=billing_state,
        plan=plan,
        limits=limits,
        allows_usage=billing_state.allows_usage(),
        is_applicable=True,
        is_exempt=False,
    )


def require_billing_active(request: Request) -> BillingContext:
    """
    FastAPI dependency: Require billing allows usage.

    Raises HTTP 402 if billing state is SUSPENDED.
    """
    context = check_billing(request)

    if context.is_exempt or not context.is_applicable:
        return context

    if not context.allows_usage:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "billing_suspended",
                "billing_state": context.billing_state.name,
                "next_action": "contact_support",
            },
        )

    return context


def check_billing_limit(
    context: BillingContext,
    limit_name: str,
    current_value: float,
) -> Optional[dict]:
    """
    Check if a specific limit is exceeded.

    Returns error dict if exceeded, None otherwise.

    Args:
        context: Billing context
        limit_name: Name of limit attribute (e.g., "max_requests_per_day")
        current_value: Current usage value

    Returns:
        Error dict if exceeded, None otherwise
    """
    if not context.is_applicable:
        return None  # Limits not enforced during onboarding

    limit_value = getattr(context.limits, limit_name, None)

    if limit_value is None:
        return None  # Unlimited

    if current_value > limit_value:
        return {
            "error": "limit_exceeded",
            "limit": limit_name,
            "current_value": current_value,
            "allowed_value": limit_value,
            "plan": context.plan.name,
            "billing_state": context.billing_state.name,
        }

    return None


__all__ = [
    "BillingGate",
    "BillingContext",
    "check_billing",
    "require_billing_active",
    "check_billing_limit",
    "is_exempt_path",
    "EXEMPT_PREFIXES",
]
