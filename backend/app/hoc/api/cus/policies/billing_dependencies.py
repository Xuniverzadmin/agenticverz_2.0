# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Role: Phase-6 Billing FastAPI dependencies
# Product: system-wide
# Temporal:
#   Trigger: request
#   Execution: sync
# Callers: API endpoints needing billing context
# Allowed Imports: L4 (bridges, auth.onboarding_state)
# Forbidden Imports: L1, L5, L6 (must route through L4)
# Reference: PIN-399 Phase-6 (Billing, Plans & Limits), PIN-520 Phase 1


"""
Phase-6 Billing Dependencies — FastAPI Integration

Provides dependencies for accessing billing context in API endpoints.

APPLICABILITY GATE:
    Billing is evaluated ONLY when tenant.onboarding_state == COMPLETE.
    Before COMPLETE, these dependencies return neutral placeholders.

DESIGN INVARIANTS:
- BILLING-001: Billing never blocks onboarding
- BILLING-003: Billing state does not affect roles

PIN-520 Phase 1: Routes billing provider access through L4 account bridge.
"""

from dataclasses import dataclass
from typing import Optional
from fastapi import Request, HTTPException

from app.billing.state import BillingState
from app.billing.plan import Plan, DEFAULT_PLAN
from app.billing.limits import Limits, DEFAULT_LIMITS
# PIN-520 Phase 1: Route through L4 bridge instead of direct L5 import
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.account_bridge import (
    get_account_bridge,
)
from app.auth.onboarding_state import OnboardingState
from app.schemas.response import wrap_dict


def _get_billing_provider():
    """Get billing provider via L4 bridge (PIN-520 compliance)."""
    bridge = get_account_bridge()
    return bridge.billing_provider_capability()


@dataclass
class BillingContext:
    """
    Billing context for a request.

    Provides billing state, plan, and limits for the current tenant.
    Returns neutral values if onboarding is not complete.

    Attributes:
        tenant_id: The tenant identifier
        billing_state: Current billing state (TRIAL if not complete)
        plan: Current plan (FREE if not complete)
        limits: Derived limits
        is_applicable: True if billing logic applies (onboarding complete)
    """

    tenant_id: str
    billing_state: BillingState
    plan: Plan
    limits: Limits
    is_applicable: bool

    def allows_usage(self) -> bool:
        """Check if current billing state allows product usage."""
        if not self.is_applicable:
            return True  # Billing doesn't block during onboarding
        return self.billing_state.allows_usage()


def get_billing_context(request: Request) -> BillingContext:
    """
    FastAPI dependency: Get billing context for current request.

    APPLICABILITY:
    - Returns neutral context if onboarding is not COMPLETE
    - Returns full billing context if onboarding is COMPLETE

    Usage:
        @router.get("/billing/status")
        async def get_status(billing: BillingContext = Depends(get_billing_context)):
            return {"state": billing.billing_state.value}
    """
    # Get tenant_id from request state (set by auth middleware)
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant context required")

    # Get onboarding state from request state
    onboarding_state = getattr(request.state, "onboarding_state", None)

    # Check if billing is applicable
    is_applicable = (
        onboarding_state is not None
        and onboarding_state == OnboardingState.COMPLETE
    )

    if not is_applicable:
        # Return neutral placeholders (BILLING-001: billing never blocks onboarding)
        return BillingContext(
            tenant_id=tenant_id,
            billing_state=BillingState.TRIAL,
            plan=DEFAULT_PLAN,
            limits=DEFAULT_LIMITS,
            is_applicable=False,
        )

    # Get real billing context via L4 bridge (PIN-520)
    provider = _get_billing_provider()
    billing_state = provider.get_billing_state(tenant_id)
    plan = provider.get_plan(tenant_id)
    limits = provider.get_limits(plan)

    return BillingContext(
        tenant_id=tenant_id,
        billing_state=billing_state,
        plan=plan,
        limits=limits,
        is_applicable=True,
    )


def require_billing_active(request: Request) -> BillingContext:
    """
    FastAPI dependency: Require billing state allows usage.

    Raises HTTP 402 if billing state is SUSPENDED.

    Usage:
        @router.post("/runs")
        async def create_run(billing: BillingContext = Depends(require_billing_active)):
            # Billing state is verified to allow usage
            ...
    """
    context = get_billing_context(request)

    if not context.allows_usage():
        raise HTTPException(
            status_code=402,
            detail={
                "error": "billing_suspended",
                "billing_state": context.billing_state.value,
                "next_action": "contact_support",
            },
        )

    return context


def check_limit(
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
        Error dict if limit exceeded, None otherwise
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
            "billing_state": context.billing_state.value,
        }

    return None


__all__ = [
    "BillingContext",
    "get_billing_context",
    "require_billing_active",
    "check_limit",
]
