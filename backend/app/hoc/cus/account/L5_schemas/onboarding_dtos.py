# capability_id: CAP-012
# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Onboarding DTOs for L5/L4 onboarding operations
# Callers: onboarding_engine.py (L5), onboarding_handler.py (L4)
# Allowed Imports: stdlib only
# Forbidden Imports: sqlalchemy, sqlmodel, app.db, app.models
# Reference: PIN-399 (Onboarding State Machine v1)
# artifact_class: CODE

"""
Onboarding DTOs (L5 Schema)

Pure data transfer objects for onboarding state transitions.
No DB or ORM imports.
"""

from dataclasses import dataclass


@dataclass
class OnboardingTransitionResult:
    """Result of an onboarding state transition attempt."""

    success: bool
    tenant_id: str
    from_state: str
    to_state: str
    trigger: str
    message: str
    was_no_op: bool = False


@dataclass
class OnboardingStateSnapshot:
    """Current onboarding state for a tenant."""

    tenant_id: str
    state_value: int
    state_name: str
    is_complete: bool


__all__ = [
    "OnboardingTransitionResult",
    "OnboardingStateSnapshot",
]
