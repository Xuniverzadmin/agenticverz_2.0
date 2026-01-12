# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Phase-6 Billing package exports
# Callers: Any module needing billing functionality
# Allowed Imports: L4 (billing submodules)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 Phase-6 (Billing, Plans & Limits)

"""
Phase-6 Billing Package

PIN-399 Phase-6: Billing never blocks onboarding.

This package provides:
- BillingState: Commercial state model (TRIAL, ACTIVE, PAST_DUE, SUSPENDED)
- Plan: Named contracts (not pricing logic)
- Limits: Derived from plan (not stored)
- BillingProvider: Protocol for billing operations
- MockBillingProvider: Deterministic mock implementation

DESIGN INVARIANTS (LOCKED):
- BILLING-001: Billing never blocks onboarding
- BILLING-002: Limits are derived, not stored
- BILLING-003: Billing state does not affect roles
- BILLING-004: No billing mutation without audit
- BILLING-005: Mock provider must satisfy same interface as real provider

APPLICABILITY:
    Billing logic applies ONLY when tenant.onboarding_state == COMPLETE.
"""

from app.billing.state import BillingState
from app.billing.plan import (
    Plan,
    PlanTier,
    PLAN_FREE,
    PLAN_PRO,
    PLAN_ENTERPRISE,
    DEFAULT_PLAN,
)
from app.billing.limits import (
    Limits,
    derive_limits,
    LIMITS_PROFILES,
    DEFAULT_LIMITS,
)
from app.billing.provider import (
    BillingProvider,
    MockBillingProvider,
    get_billing_provider,
    set_billing_provider,
)

# NOTE: FastAPI dependencies moved to app/api/billing_dependencies.py
# Domain packages must not export HTTP adapters (see LAYER_MODEL.md)

__all__ = [
    # State
    "BillingState",
    # Plan
    "Plan",
    "PlanTier",
    "PLAN_FREE",
    "PLAN_PRO",
    "PLAN_ENTERPRISE",
    "DEFAULT_PLAN",
    # Limits
    "Limits",
    "derive_limits",
    "LIMITS_PROFILES",
    "DEFAULT_LIMITS",
    # Provider
    "BillingProvider",
    "MockBillingProvider",
    "get_billing_provider",
    "set_billing_provider",
]
