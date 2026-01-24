# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Onboarding state enum and constants
# Callers: OnboardingGateMiddleware, Tenant model, onboarding endpoints
# Allowed Imports: None (foundational enum)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 (Onboarding State Machine v1)

"""
Onboarding State Machine - Shared Enum

PIN-399: Linear, monotonic onboarding state machine.

States:
    CREATED → IDENTITY_VERIFIED → API_KEY_CREATED → SDK_CONNECTED → COMPLETE

Design Invariants (from ONBOARDING_STATE_MACHINE_V1.md):
- ONBOARD-001: Onboarding state is the sole authority for bootstrap permissions
- ONBOARD-002: Roles and plans do not apply before COMPLETE
- ONBOARD-003: Founders and customers follow identical state transitions
- ONBOARD-004: No endpoint may infer onboarding progress
- ONBOARD-005: API keys are onboarding artifacts, not permissions

This enum is the single source of truth for onboarding states.
No duplicate definitions allowed elsewhere.
"""

from enum import IntEnum


class OnboardingState(IntEnum):
    """
    Monotonic onboarding state machine.

    States only increase, never decrease.
    Comparison operators work naturally: CREATED < IDENTITY_VERIFIED

    Integer values enable:
    - Simple comparison: current_state >= required_state
    - Database storage as integer
    - Clear ordering semantics
    """

    CREATED = 0
    IDENTITY_VERIFIED = 1
    API_KEY_CREATED = 2
    SDK_CONNECTED = 3
    COMPLETE = 4

    @classmethod
    def from_string(cls, value: str) -> "OnboardingState":
        """
        Parse state from string (case-insensitive).

        Raises ValueError if unknown state.
        """
        normalized = value.upper().strip()
        try:
            return cls[normalized]
        except KeyError:
            valid = [s.name for s in cls]
            raise ValueError(f"Unknown onboarding state: {value}. Valid: {valid}")

    @classmethod
    def default(cls) -> "OnboardingState":
        """Return the default state for new tenants."""
        return cls.CREATED


# State transition triggers (for documentation/reference)
# These are the events that cause state advancement
STATE_TRANSITIONS = {
    OnboardingState.CREATED: {
        "next": OnboardingState.IDENTITY_VERIFIED,
        "trigger": "Successful Clerk-authenticated request",
    },
    OnboardingState.IDENTITY_VERIFIED: {
        "next": OnboardingState.API_KEY_CREATED,
        "trigger": "First API key created",
    },
    OnboardingState.API_KEY_CREATED: {
        "next": OnboardingState.SDK_CONNECTED,
        "trigger": "First successful SDK-authenticated call",
    },
    OnboardingState.SDK_CONNECTED: {
        "next": OnboardingState.COMPLETE,
        "trigger": "Explicit finalize or automatic promotion",
    },
    OnboardingState.COMPLETE: {
        "next": None,  # Terminal state
        "trigger": None,
    },
}
