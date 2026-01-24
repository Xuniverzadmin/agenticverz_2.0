# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Phase-6 Plan model (abstract, no DB persistence)
# Callers: BillingProvider, limits derivation
# Allowed Imports: L4 (billing.state)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 Phase-6 (Billing, Plans & Limits)

"""
Phase-6 Plan Model — Named Contracts (Not Pricing Logic)

PIN-399 Phase-6: Plans are named contracts, not pricing logic.

EXPLICIT NON-GOALS:
- No prices
- No currency
- No billing cycle assumptions
- No gateway IDs
- No subscriptions
- No coupons / proration / invoices
- No taxes

Those come in future phases, if ever.

This module defines the abstract Plan model used for limit derivation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PlanTier(Enum):
    """
    Plan tier hierarchy.

    Tiers represent capability levels, not prices.
    """

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

    @classmethod
    def from_string(cls, value: str) -> "PlanTier":
        """Parse tier from string (case-insensitive)."""
        normalized = value.lower().strip()
        for tier in cls:
            if tier.value == normalized:
                return tier
        valid = [t.value for t in cls]
        raise ValueError(f"Unknown plan tier: {value}. Valid: {valid}")


@dataclass(frozen=True)
class Plan:
    """
    Phase-6 Plan Model (Immutable).

    Plans define what a tenant is entitled to, not what they pay.

    Attributes:
        id: Unique plan identifier (e.g., "free-v1", "pro-v1")
        name: Human-readable name (e.g., "Free", "Pro")
        tier: Capability tier (FREE, PRO, ENTERPRISE)
        limits_profile: Key for deriving limits (e.g., "free", "pro", "enterprise")
        description: Optional human-readable description

    INVARIANTS:
    - Plans are immutable after creation
    - Plans do not contain pricing information
    - Plans do not reference gateway IDs
    - Limits are derived from limits_profile, not stored on the plan
    """

    id: str
    name: str
    tier: PlanTier
    limits_profile: str
    description: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate plan on creation."""
        if not self.id:
            raise ValueError("Plan id cannot be empty")
        if not self.name:
            raise ValueError("Plan name cannot be empty")
        if not self.limits_profile:
            raise ValueError("Plan limits_profile cannot be empty")


# =============================================================================
# HARDCODED PLANS (Mock Implementation)
# =============================================================================

# These plans are hardcoded for the mock provider.
# Real implementation will load from configuration or database.

PLAN_FREE = Plan(
    id="free-v1",
    name="Free",
    tier=PlanTier.FREE,
    limits_profile="free",
    description="Free tier with basic limits",
)

PLAN_PRO = Plan(
    id="pro-v1",
    name="Pro",
    tier=PlanTier.PRO,
    limits_profile="pro",
    description="Pro tier with elevated limits",
)

PLAN_ENTERPRISE = Plan(
    id="enterprise-v1",
    name="Enterprise",
    tier=PlanTier.ENTERPRISE,
    limits_profile="enterprise",
    description="Enterprise tier with custom limits",
)

# Default plan for new tenants after onboarding COMPLETE
DEFAULT_PLAN = PLAN_FREE


__all__ = [
    "PlanTier",
    "Plan",
    "PLAN_FREE",
    "PLAN_PRO",
    "PLAN_ENTERPRISE",
    "DEFAULT_PLAN",
]
