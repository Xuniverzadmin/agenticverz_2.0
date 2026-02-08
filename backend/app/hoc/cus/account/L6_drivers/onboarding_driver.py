# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Data Access:
#   Reads: Tenant.onboarding_state
#   Writes: Tenant.onboarding_state (via session.add, NO COMMIT)
# Database:
#   Scope: domain (account)
#   Models: Tenant
# Role: Onboarding driver — pure data access for onboarding state operations
# Callers: onboarding_engine.py (L5), must provide session, must own transaction boundary
# Allowed Imports: L7 (models)
# Forbidden: session.commit() — L4 coordinator owns transaction boundary
# Reference: PIN-399 (Onboarding State Machine v1)
# artifact_class: CODE

"""
Onboarding Driver (L6)

Pure data access layer for tenant onboarding state operations.
Follows tenant_lifecycle_driver.py pattern.

All methods are pure data access — no business logic.
NO COMMIT — L4 coordinator owns transaction boundary.
"""

from __future__ import annotations

from typing import Optional

from sqlmodel import Session


class OnboardingDriver:
    """
    L6 Driver for tenant onboarding state operations.

    All methods are pure data access — no business logic.
    """

    def __init__(self, session: Session):
        self.session = session

    def fetch_onboarding_state(self, tenant_id: str) -> Optional[int]:
        """
        Fetch raw tenant onboarding_state from DB.

        Returns the int state value, or None if tenant not found.
        """
        from app.models.tenant import Tenant

        tenant = self.session.get(Tenant, tenant_id)
        if tenant is None:
            return None
        return tenant.onboarding_state

    def write_onboarding_state(self, tenant_id: str, new_state: int) -> Optional[int]:
        """
        Write tenant onboarding_state to DB.

        Returns the old state value, or None if tenant not found.
        NO COMMIT — L4 coordinator owns transaction boundary.
        """
        from app.models.tenant import Tenant

        tenant = self.session.get(Tenant, tenant_id)
        if tenant is None:
            return None

        old_state = tenant.onboarding_state
        tenant.onboarding_state = new_state
        self.session.add(tenant)
        # NO COMMIT — L4 coordinator owns transaction boundary
        return old_state


def get_onboarding_driver(session: Session) -> OnboardingDriver:
    """Get an OnboardingDriver instance."""
    return OnboardingDriver(session)


__all__ = [
    "OnboardingDriver",
    "get_onboarding_driver",
]
