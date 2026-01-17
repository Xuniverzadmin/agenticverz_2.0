# Layer: L4 — Domain Engines
# Product: system-wide
# Role: Tenant domain exports
# Reference: docs/architecture/contracts/AUTHORITY_CONTRACT.md

"""
Tenant Domain

Provides:
- TenantState: Enum of valid tenant states
- TenantStateResolver: Derives tenant state from account/user readiness
- require_tenant_ready: Gate function for auth middleware
"""

from app.domain.tenants.state_resolver import (
    TenantState,
    TenantStateResolver,
    require_tenant_ready,
    require_tenant_active,
)

__all__ = [
    "TenantState",
    "TenantStateResolver",
    "require_tenant_ready",
    "require_tenant_active",
]
