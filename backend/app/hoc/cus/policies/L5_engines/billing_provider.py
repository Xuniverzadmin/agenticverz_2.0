# Layer: L5 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: runtime
#   Execution: sync
# Role: Phase-6 BillingProvider protocol and MockBillingProvider
# Callers: billing middleware, billing APIs, runtime enforcement
# Allowed Imports: L4 (billing.state, billing.plan, billing.limits)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 Phase-6 (Billing, Plans & Limits)

"""
Phase-6 Billing Provider — Interface and Mock Implementation

PIN-399 Phase-6: Mock provider must satisfy same interface as real provider.

DESIGN INVARIANTS (LOCKED):
- BILLING-005: Mock provider must satisfy same interface as real provider

IMPLEMENTATION CONSTRAINTS:
- Hardcoded plan assignment
- Hardcoded limits
- Deterministic behavior
- No network calls
- No external dependencies

This ensures zero refactor when Stripe/etc is added later.
"""

from typing import Protocol, Optional
import logging

from app.billing.state import BillingState
from app.billing.plan import Plan, DEFAULT_PLAN, PLAN_FREE, PLAN_PRO, PLAN_ENTERPRISE
from app.billing.limits import Limits, derive_limits

logger = logging.getLogger(__name__)


class BillingProvider(Protocol):
    """
    Phase-6 Billing Provider Protocol.

    All billing providers (mock and real) must implement this interface.

    This protocol is LOCKED per BILLING-005.
    """

    def get_billing_state(self, tenant_id: str) -> BillingState:
        """
        Get the billing state for a tenant.

        Args:
            tenant_id: The tenant identifier

        Returns:
            BillingState enum value
        """
        ...

    def get_plan(self, tenant_id: str) -> Plan:
        """
        Get the plan for a tenant.

        Args:
            tenant_id: The tenant identifier

        Returns:
            Plan instance
        """
        ...

    def get_limits(self, plan: Plan) -> Limits:
        """
        Derive limits from a plan.

        INVARIANT: Limits are derived, not stored (BILLING-002).

        Args:
            plan: The tenant's plan

        Returns:
            Limits instance
        """
        ...

    def is_limit_exceeded(
        self, tenant_id: str, limit_name: str, current_value: float
    ) -> bool:
        """
        Check if a specific limit is exceeded.

        Args:
            tenant_id: The tenant identifier
            limit_name: Name of the limit to check (e.g., "max_requests_per_day")
            current_value: Current usage value

        Returns:
            True if limit is exceeded
        """
        ...


class MockBillingProvider:
    """
    Phase-6 Mock Billing Provider.

    Implements BillingProvider protocol with hardcoded, deterministic behavior.

    IMPLEMENTATION CONSTRAINTS:
    - No network calls
    - No database access (uses in-memory state)
    - Deterministic results
    - Static configuration

    This mock is behavior-compatible with future real providers.
    """

    def __init__(self) -> None:
        """Initialize mock provider with in-memory state."""
        # In-memory state for testing (not persistent)
        self._tenant_states: dict[str, BillingState] = {}
        self._tenant_plans: dict[str, Plan] = {}

    def get_billing_state(self, tenant_id: str) -> BillingState:
        """
        Get the billing state for a tenant.

        Mock behavior: Returns TRIAL for unknown tenants (default after COMPLETE).
        """
        return self._tenant_states.get(tenant_id, BillingState.default())

    def get_plan(self, tenant_id: str) -> Plan:
        """
        Get the plan for a tenant.

        Mock behavior: Returns FREE plan for unknown tenants.
        """
        return self._tenant_plans.get(tenant_id, DEFAULT_PLAN)

    def get_limits(self, plan: Plan) -> Limits:
        """
        Derive limits from a plan.

        Uses limits_profile to look up static limits.
        """
        return derive_limits(plan.limits_profile)

    def is_limit_exceeded(
        self, tenant_id: str, limit_name: str, current_value: float
    ) -> bool:
        """
        Check if a specific limit is exceeded.

        Args:
            tenant_id: The tenant identifier
            limit_name: Name of the limit (e.g., "max_requests_per_day")
            current_value: Current usage value

        Returns:
            True if limit is exceeded, False otherwise
        """
        plan = self.get_plan(tenant_id)
        limits = self.get_limits(plan)

        # Get the limit value by name
        limit_value = getattr(limits, limit_name, None)

        # None means unlimited
        if limit_value is None:
            return False

        return current_value > limit_value

    # ==========================================================================
    # Mock-specific methods (for testing only, not part of protocol)
    # ==========================================================================

    def set_billing_state(self, tenant_id: str, state: BillingState) -> None:
        """
        Set billing state for a tenant (mock/test only).

        INVARIANT: Real provider would use audit trail (BILLING-004).
        """
        logger.info(
            f"MockBillingProvider: Setting billing state for {tenant_id} to {state.value}"
        )
        self._tenant_states[tenant_id] = state

    def set_plan(self, tenant_id: str, plan: Plan) -> None:
        """
        Set plan for a tenant (mock/test only).

        INVARIANT: Real provider would use audit trail (BILLING-004).
        """
        logger.info(
            f"MockBillingProvider: Setting plan for {tenant_id} to {plan.id}"
        )
        self._tenant_plans[tenant_id] = plan

    def reset(self) -> None:
        """Reset all mock state (for testing)."""
        self._tenant_states.clear()
        self._tenant_plans.clear()


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global mock provider instance
# In production, this would be replaced with a real provider
_billing_provider: Optional[BillingProvider] = None


def get_billing_provider() -> BillingProvider:
    """
    Get the billing provider instance.

    Returns MockBillingProvider by default.
    Can be replaced for testing or production.
    """
    global _billing_provider
    if _billing_provider is None:
        _billing_provider = MockBillingProvider()
    return _billing_provider


def set_billing_provider(provider: BillingProvider) -> None:
    """
    Set the billing provider instance.

    Used for testing or to swap in a real provider.
    """
    global _billing_provider
    _billing_provider = provider


__all__ = [
    "BillingProvider",
    "MockBillingProvider",
    "get_billing_provider",
    "set_billing_provider",
]
