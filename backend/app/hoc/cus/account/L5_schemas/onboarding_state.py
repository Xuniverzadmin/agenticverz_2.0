# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Onboarding state enum + transition metadata (stdlib only)
# Callers: onboarding_engine.py (L5), hoc_spine onboarding_policy (L4), middleware gates, onboarding endpoints
# Allowed Imports: stdlib only
# Forbidden Imports: sqlalchemy, sqlmodel, app.db, app.models, fastapi
# Reference: PIN-399 (Onboarding State Machine v1)
# artifact_class: CODE

"""
Onboarding State Machine — Canonical (HOC)

PIN-399: Linear, monotonic onboarding state machine.

States:
    CREATED → IDENTITY_VERIFIED → API_KEY_CREATED → SDK_CONNECTED → COMPLETE

Design Invariants (from ONBOARDING_STATE_MACHINE_V1.md):
- ONBOARD-001: Onboarding state is the sole authority for bootstrap permissions
- ONBOARD-002: Roles and plans do not apply before COMPLETE
- ONBOARD-003: Founders and customers follow identical state transitions
- ONBOARD-004: No endpoint may infer onboarding progress
- ONBOARD-005: API keys are onboarding artifacts, not permissions

This module is the single source of truth for onboarding states in HOC.
"""

from __future__ import annotations

from enum import IntEnum


class OnboardingState(IntEnum):
    """Monotonic onboarding state machine (forward-only)."""

    CREATED = 0
    IDENTITY_VERIFIED = 1
    API_KEY_CREATED = 2
    SDK_CONNECTED = 3
    COMPLETE = 4

    @classmethod
    def from_string(cls, value: str) -> "OnboardingState":
        normalized = value.upper().strip()
        try:
            return cls[normalized]
        except KeyError:
            valid = [s.name for s in cls]
            raise ValueError(f"Unknown onboarding state: {value}. Valid: {valid}")

    @classmethod
    def default(cls) -> "OnboardingState":
        return cls.CREATED


# Back-compat alias for modules that used the earlier "mirror" naming.
OnboardingStatus = OnboardingState


ONBOARDING_STATUS_NAMES: dict[int, str] = {s.value: s.name for s in OnboardingState}


def is_at_or_past(current: int, target: int) -> bool:
    return current >= target


def is_complete(state: int) -> bool:
    return state >= OnboardingState.COMPLETE.value


# Transition triggers (documentation/reference only).
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


__all__ = [
    "OnboardingState",
    "OnboardingStatus",
    "ONBOARDING_STATUS_NAMES",
    "STATE_TRANSITIONS",
    "is_at_or_past",
    "is_complete",
]

