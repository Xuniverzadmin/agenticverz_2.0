# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Onboarding state enum mirror + helpers (pure stdlib, no DB imports)
# Callers: onboarding_engine.py (L5), onboarding_handler.py (L4), call sites (L2)
# Allowed Imports: stdlib only
# Forbidden Imports: sqlalchemy, sqlmodel, app.db, app.models
# Reference: PIN-399 (Onboarding State Machine v1)
# artifact_class: CODE

"""
Onboarding State Enum Mirror (L5 Schema)

Mirrors app.auth.onboarding_state.OnboardingState for L5/L4 use.
Pure stdlib — no DB or ORM imports.

States: CREATED(0) -> IDENTITY_VERIFIED(1) -> API_KEY_CREATED(2) -> SDK_CONNECTED(3) -> COMPLETE(4)
"""

from enum import IntEnum


class OnboardingStatus(IntEnum):
    """
    L5 mirror of OnboardingState.

    Monotonic: states only increase, never decrease.
    Integer values enable simple comparison: current >= target.
    """

    CREATED = 0
    IDENTITY_VERIFIED = 1
    API_KEY_CREATED = 2
    SDK_CONNECTED = 3
    COMPLETE = 4


ONBOARDING_STATUS_NAMES: dict[int, str] = {s.value: s.name for s in OnboardingStatus}


def is_at_or_past(current: int, target: int) -> bool:
    """Check if current state is at or past the target state."""
    return current >= target


def is_complete(state: int) -> bool:
    """Check if onboarding is complete."""
    return state >= OnboardingStatus.COMPLETE.value


__all__ = [
    "OnboardingStatus",
    "ONBOARDING_STATUS_NAMES",
    "is_at_or_past",
    "is_complete",
]
