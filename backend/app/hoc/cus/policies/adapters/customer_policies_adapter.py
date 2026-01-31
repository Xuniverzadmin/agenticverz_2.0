# Layer: L2 — Adapter
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L4)
# Role: Customer policies boundary adapter (L2 → L4)
# Callers: guard_policies.py (L2)
# Allowed Imports: L4
# Forbidden Imports: L1, L2, L5, L6
# Reference: PIN-280, PIN-281 (L2 Promotion Governance)
#
# GOVERNANCE NOTE:
# This adapter is TRANSLATION ONLY. It enforces:
# - Tenant scoping (customer can only see their own policies)
# - Customer-safe schema (no internal threshold logic exposed)
# - Rate limiting (via caller context)
#
# This adapter qualifies POLICY_LIST and POLICY_DETAIL capabilities.

"""
Customer Policies Adapter (L2)

This adapter sits between L2 (guard_policies.py API) and L4 (CustomerPolicyReadService).

L2 (Guard API) → L4 (CustomerPolicyReadService)

The adapter:
1. Receives API requests with tenant context
2. Enforces tenant isolation
3. Transforms to customer-safe policy view
4. Delegates to L4 service
5. Returns customer-friendly policy constraints to L2

This is a thin translation layer - no policy evaluation logic, no direct DB access.

Reference: PIN-280 (L2 Promotion Governance), PIN-281 (Claude Task TODO)
"""

from typing import List, Optional

from pydantic import BaseModel

# L5 imports ONLY (no L6!)
from app.hoc.cus.policies.L5_engines.customer_policy_read_engine import (
    CustomerPolicyReadService,
    GuardrailSummary,
    PolicyConstraints,
    get_customer_policy_read_service,
)

# =============================================================================
# Customer-Safe DTOs (No Internal Fields)
# =============================================================================


class CustomerBudgetConstraint(BaseModel):
    """Customer-visible budget constraint."""

    limit_cents: int
    period: str  # daily, weekly, monthly
    current_usage_cents: int
    remaining_cents: int
    percentage_used: float
    reset_at: Optional[str] = None


class CustomerRateLimit(BaseModel):
    """Customer-visible rate limit."""

    requests_per_period: int
    period: str  # minute, hour, day
    current_usage: int
    remaining: int


class CustomerGuardrail(BaseModel):
    """Customer-visible guardrail configuration."""

    id: str
    name: str
    description: str
    enabled: bool
    category: str  # safety, cost, rate, content
    action_on_trigger: str  # block, warn, log


class CustomerPolicyConstraints(BaseModel):
    """Customer-visible policy constraints summary."""

    tenant_id: str
    budget: Optional[CustomerBudgetConstraint] = None
    rate_limits: List[CustomerRateLimit] = []
    guardrails: List[CustomerGuardrail] = []
    last_updated: str


# =============================================================================
# Adapter Class
# =============================================================================


class CustomerPoliciesAdapter:
    """
    Boundary adapter for customer policy constraints.

    This class provides the ONLY interface that L2 (guard_policies.py) may use
    to access policy constraint information. It enforces tenant isolation and
    transforms data to customer-safe schemas.

    INVARIANT: All methods require tenant_id for isolation.
    INVARIANT: No L6 imports - delegates to L4 only.

    PIN-280 Rule: Adapter Is Translation Only + Tenant Scoping
    """

    def __init__(self):
        """Initialize adapter with lazy L4 service loading."""
        self._service: Optional[CustomerPolicyReadService] = None

    def _get_service(self) -> CustomerPolicyReadService:
        """Get the L4 CustomerPolicyReadService (lazy loaded)."""
        if self._service is None:
            self._service = get_customer_policy_read_service()
        return self._service

    def get_policy_constraints(
        self,
        tenant_id: str,
    ) -> CustomerPolicyConstraints:
        """
        Get policy constraints for a customer.

        Enforces tenant isolation - customer can only see their own constraints.

        Args:
            tenant_id: Customer's tenant ID (REQUIRED, enforced)

        Returns:
            CustomerPolicyConstraints with customer-safe data

        Raises:
            ValueError: If tenant_id is missing

        Reference: PIN-281 Phase 4 (L4→adapter promotion)
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for get_policy_constraints")

        # Delegate to L4 service
        result: PolicyConstraints = self._get_service().get_policy_constraints(
            tenant_id=tenant_id,
        )

        # Transform L4 DTOs to adapter customer-safe DTOs
        return self._to_customer_policy_constraints(result)

    def get_guardrail_detail(
        self,
        tenant_id: str,
        guardrail_id: str,
    ) -> Optional[CustomerGuardrail]:
        """
        Get guardrail detail for a customer.

        Args:
            tenant_id: Customer's tenant ID (REQUIRED, enforced)
            guardrail_id: Guardrail ID

        Returns:
            CustomerGuardrail if found, None otherwise

        Raises:
            ValueError: If tenant_id or guardrail_id is missing

        Reference: PIN-281 Phase 4 (L4→adapter promotion)
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for get_guardrail_detail")
        if not guardrail_id:
            raise ValueError("guardrail_id is required for get_guardrail_detail")

        # Delegate to L4 service
        result: Optional[GuardrailSummary] = self._get_service().get_guardrail_detail(
            tenant_id=tenant_id,
            guardrail_id=guardrail_id,
        )

        if result is None:
            return None

        return self._to_customer_guardrail(result)

    def _to_customer_policy_constraints(self, constraints: PolicyConstraints) -> CustomerPolicyConstraints:
        """Transform L4 PolicyConstraints to adapter CustomerPolicyConstraints."""
        budget = None
        if constraints.budget:
            budget = CustomerBudgetConstraint(
                limit_cents=constraints.budget.limit_cents,
                period=constraints.budget.period,
                current_usage_cents=constraints.budget.current_usage_cents,
                remaining_cents=constraints.budget.remaining_cents,
                percentage_used=constraints.budget.percentage_used,
                reset_at=constraints.budget.reset_at,
            )

        rate_limits = [
            CustomerRateLimit(
                requests_per_period=rl.requests_per_period,
                period=rl.period,
                current_usage=rl.current_usage,
                remaining=rl.remaining,
            )
            for rl in constraints.rate_limits
        ]

        guardrails = [self._to_customer_guardrail(g) for g in constraints.guardrails]

        return CustomerPolicyConstraints(
            tenant_id=constraints.tenant_id,
            budget=budget,
            rate_limits=rate_limits,
            guardrails=guardrails,
            last_updated=constraints.last_updated,
        )

    def _to_customer_guardrail(self, guardrail: GuardrailSummary) -> CustomerGuardrail:
        """Transform L4 GuardrailSummary to adapter CustomerGuardrail."""
        return CustomerGuardrail(
            id=guardrail.id,
            name=guardrail.name,
            description=guardrail.description,
            enabled=guardrail.enabled,
            category=guardrail.category,
            action_on_trigger=guardrail.action_on_trigger,
        )


# =============================================================================
# Singleton Factory
# =============================================================================

_customer_policies_adapter_instance: Optional[CustomerPoliciesAdapter] = None


def get_customer_policies_adapter() -> CustomerPoliciesAdapter:
    """
    Get the singleton CustomerPoliciesAdapter instance.

    This is the ONLY way L2 should obtain a policies adapter.
    Direct instantiation is discouraged.

    Note: Unlike the old version that took a session parameter,
    this now uses the singleton pattern. The session is managed
    internally by the L4 service.

    Returns:
        CustomerPoliciesAdapter singleton instance

    Reference: PIN-281 (Adapter Is the Only Entry for L2)
    """
    global _customer_policies_adapter_instance
    if _customer_policies_adapter_instance is None:
        _customer_policies_adapter_instance = CustomerPoliciesAdapter()
    return _customer_policies_adapter_instance


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "CustomerPoliciesAdapter",
    "get_customer_policies_adapter",
    # DTOs for L2 convenience
    "CustomerBudgetConstraint",
    "CustomerRateLimit",
    "CustomerGuardrail",
    "CustomerPolicyConstraints",
]
