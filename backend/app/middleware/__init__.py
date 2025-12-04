# NOVA Middleware
# FastAPI middleware components

from .tenancy import TenancyMiddleware, get_tenant_id
from .tenant import (
    TenantContext,
    TenantMiddleware,
    get_tenant_context,
    set_tenant_context,
    clear_tenant_context,
    require_tenant_context,
    ensure_tenant_access,
    tenant_scoped_query,
    require_tenant,
)

__all__ = [
    # Legacy
    "TenancyMiddleware",
    "get_tenant_id",
    # New M6 tenant context
    "TenantContext",
    "TenantMiddleware",
    "get_tenant_context",
    "set_tenant_context",
    "clear_tenant_context",
    "require_tenant_context",
    "ensure_tenant_access",
    "tenant_scoped_query",
    "require_tenant",
]
