# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Phase-6 Billing State enum
# Callers: BillingProvider, Tenant model (when extended), billing middleware
# Allowed Imports: None (foundational enum)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 Phase-6 (Billing, Plans & Limits)

"""
Phase-6 Billing State — Commercial State Model

PIN-399 Phase-6: Billing never blocks onboarding.

DESIGN INVARIANTS (LOCKED):
- BILLING-001: Billing never blocks onboarding
- BILLING-002: Limits are derived, not stored
- BILLING-003: Billing state does not affect roles
- BILLING-004: No billing mutation without audit
- BILLING-005: Mock provider must satisfy same interface as real provider

APPLICABILITY GATE:
    Billing logic is evaluated ONLY IF tenant.onboarding_state == COMPLETE.
    Before COMPLETE:
    - Billing APIs return neutral placeholders
    - Limits are not enforced
    - Usage is tracked but not blocked

This enum is the single source of truth for billing states.
"""

from enum import Enum


class BillingState(Enum):
    """
    Phase-6 Billing States (Tenant-scoped).

    States represent the commercial standing of a tenant.
    NOT tied to any specific payment gateway.

    SEMANTICS (LOCKED):
    - TRIAL: Default after onboarding COMPLETE
    - ACTIVE: Valid paid plan
    - PAST_DUE: Payment issue, grace period active
    - SUSPENDED: Usage blocked, data intact

    No other states allowed in v1.
    """

    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"

    @classmethod
    def from_string(cls, value: str) -> "BillingState":
        """
        Parse state from string (case-insensitive).

        Raises ValueError if unknown state.
        """
        normalized = value.lower().strip()
        for state in cls:
            if state.value == normalized:
                return state
        valid = [s.value for s in cls]
        raise ValueError(f"Unknown billing state: {value}. Valid: {valid}")

    @classmethod
    def default(cls) -> "BillingState":
        """
        Return the default state for tenants completing onboarding.

        Per PHASE_6_BILLING_LIMITS.md: TRIAL is default after COMPLETE.
        """
        return cls.TRIAL

    def allows_usage(self) -> bool:
        """
        Check if this billing state allows product usage.

        Returns:
            True if tenant can use the product
        """
        return self != BillingState.SUSPENDED

    def is_in_good_standing(self) -> bool:
        """
        Check if tenant is in good commercial standing.

        Returns:
            True if TRIAL or ACTIVE
        """
        return self in (BillingState.TRIAL, BillingState.ACTIVE)


__all__ = ["BillingState"]
