# Layer: L3 — Boundary Adapter (Shim)
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Canonical onboarding state import surface for platform/auth + legacy callers
# Callers: app.auth.role_guard, app.models.tenant, internal engines
# Allowed Imports: HOC onboarding enum (stdlib-only)
# Reference: PIN-399

"""
OnboardingState Import Shim (Canonical = HOC)

The single source of truth for onboarding states is:
  `app.hoc.cus.account.L5_schemas.onboarding_state`

This module exists because platform/auth and legacy non-HOC modules historically
imported `app.auth.onboarding_state`. We keep that import stable while ensuring
there is exactly one state machine definition.
"""

from app.hoc.cus.account.L5_schemas.onboarding_state import (  # noqa: F401
    ONBOARDING_STATUS_NAMES,
    STATE_TRANSITIONS,
    OnboardingState,
    OnboardingStatus,
    is_at_or_past,
    is_complete,
)

__all__ = [
    "OnboardingState",
    "OnboardingStatus",
    "ONBOARDING_STATUS_NAMES",
    "STATE_TRANSITIONS",
    "is_at_or_past",
    "is_complete",
]

