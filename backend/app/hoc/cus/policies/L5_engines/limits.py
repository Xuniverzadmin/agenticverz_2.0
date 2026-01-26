# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Phase-6 Limits derivation (code only, not stored)
# Callers: BillingProvider, enforcement middleware
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-399 Phase-6 (Billing, Plans & Limits)
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure derivation logic

"""
Phase-6 Limits — Derived from Plan (Not Stored)

PIN-399 Phase-6: Limits are derived from plan at runtime, never hand-edited.

DESIGN INVARIANTS (LOCKED):
- BILLING-002: Limits are derived, not stored

ENFORCEMENT SEMANTICS:
- Limits are evaluated at runtime
- Limits are enforced after onboarding COMPLETE
- Limits may emit warnings before enforcement

WHAT LIMITS CAN DO:
- Throttle
- Reject with explicit error
- Emit usage warnings

WHAT LIMITS MUST NOT DO:
- Mutate onboarding state
- Revoke API keys silently
- Affect auth or roles
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Limits:
    """
    Phase-6 Limits Model (Immutable, Derived).

    Limits are computed from a plan's limits_profile.
    NEVER stored directly in database.

    Attributes:
        max_requests_per_day: Maximum API requests per day
        max_active_agents: Maximum concurrent agents
        max_storage_mb: Maximum storage in megabytes
        max_monthly_cost_usd: Maximum monthly compute cost (soft limit)
        max_runs_per_day: Maximum run executions per day
        max_policies: Maximum policy rules

    INVARIANTS:
    - All limits are optional (None = unlimited)
    - Limits are derived from limits_profile at runtime
    - Limits are never directly persisted
    """

    max_requests_per_day: Optional[int] = None
    max_active_agents: Optional[int] = None
    max_storage_mb: Optional[int] = None
    max_monthly_cost_usd: Optional[float] = None
    max_runs_per_day: Optional[int] = None
    max_policies: Optional[int] = None

    def is_unlimited(self) -> bool:
        """Check if all limits are unlimited (None)."""
        return all(
            v is None
            for v in [
                self.max_requests_per_day,
                self.max_active_agents,
                self.max_storage_mb,
                self.max_monthly_cost_usd,
                self.max_runs_per_day,
                self.max_policies,
            ]
        )


# =============================================================================
# LIMITS PROFILES (Hardcoded for Mock)
# =============================================================================

# These profiles are used by MockBillingProvider.
# Real implementation will load from configuration.

LIMITS_PROFILES: dict[str, Limits] = {
    "free": Limits(
        max_requests_per_day=1000,
        max_active_agents=3,
        max_storage_mb=100,
        max_monthly_cost_usd=10.0,
        max_runs_per_day=100,
        max_policies=10,
    ),
    "pro": Limits(
        max_requests_per_day=10000,
        max_active_agents=20,
        max_storage_mb=1000,
        max_monthly_cost_usd=500.0,
        max_runs_per_day=1000,
        max_policies=100,
    ),
    "enterprise": Limits(
        max_requests_per_day=None,  # Unlimited
        max_active_agents=None,  # Unlimited
        max_storage_mb=None,  # Unlimited
        max_monthly_cost_usd=None,  # Unlimited
        max_runs_per_day=None,  # Unlimited
        max_policies=None,  # Unlimited
    ),
}

# Default limits for unknown profiles (restrictive)
DEFAULT_LIMITS = Limits(
    max_requests_per_day=100,
    max_active_agents=1,
    max_storage_mb=10,
    max_monthly_cost_usd=1.0,
    max_runs_per_day=10,
    max_policies=5,
)


def derive_limits(limits_profile: str) -> Limits:
    """
    Derive limits from a limits profile key.

    INVARIANT: This is the single source of limit derivation.

    Args:
        limits_profile: Profile key from Plan.limits_profile

    Returns:
        Limits instance (immutable)
    """
    return LIMITS_PROFILES.get(limits_profile, DEFAULT_LIMITS)


__all__ = [
    "Limits",
    "derive_limits",
    "LIMITS_PROFILES",
    "DEFAULT_LIMITS",
]
