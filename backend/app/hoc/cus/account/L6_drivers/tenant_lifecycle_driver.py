# capability_id: CAP-012
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Tenant.status
#   Writes: Tenant.status, Tenant.suspended_reason, Tenant.updated_at (via session.add, NO COMMIT)
# Database:
#   Scope: domain (account)
#   Models: Tenant
# Role: Tenant lifecycle driver — pure data access for lifecycle status operations
# Callers: tenant_lifecycle_engine.py (L5), must provide session, must own transaction boundary
# Allowed Imports: L6, L7 (models)
# Forbidden: session.commit() — L4 coordinator owns transaction boundary
# Reference: PIN-400 Phase-9 (Offboarding & Tenant Lifecycle)
# artifact_class: CODE

"""
Tenant Lifecycle Driver (L6)

Pure data access layer for tenant lifecycle status operations.
Follows tenant_driver.py pattern exactly.

All methods are pure data access — no business logic.
NO COMMIT — L4 coordinator owns transaction boundary.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session

from app.models.tenant import Tenant


class TenantLifecycleDriver:
    """
    L6 Driver for tenant lifecycle status operations.

    All methods are pure data access — no business logic.
    """

    def __init__(self, session: Session):
        self.session = session

    def fetch_tenant_status(self, tenant_id: str) -> Optional[str]:
        """
        Fetch raw tenant status from DB.

        Returns the raw VARCHAR status value, or None if tenant not found.
        """
        tenant = self.session.get(Tenant, tenant_id)
        if tenant is None:
            return None
        return tenant.status

    def update_lifecycle_status(
        self,
        tenant_id: str,
        new_status: str,
        reason: Optional[str] = None,
    ) -> Optional[str]:
        """
        Update tenant lifecycle status in DB.

        Returns the old status, or None if tenant not found.
        NO COMMIT — L4 coordinator owns transaction boundary.
        """
        tenant = self.session.get(Tenant, tenant_id)
        if tenant is None:
            return None

        old_status = tenant.status
        tenant.status = new_status
        if reason is not None:
            tenant.suspended_reason = reason
        tenant.updated_at = datetime.now(timezone.utc)
        self.session.add(tenant)
        # NO COMMIT — L4 coordinator owns transaction boundary
        return old_status


def get_tenant_lifecycle_driver(session: Session) -> TenantLifecycleDriver:
    """Get a TenantLifecycleDriver instance."""
    return TenantLifecycleDriver(session)


__all__ = [
    "TenantLifecycleDriver",
    "get_tenant_lifecycle_driver",
]
