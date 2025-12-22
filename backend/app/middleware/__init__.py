# NOVA Middleware
# FastAPI middleware components

from .tenancy import TenancyMiddleware, get_tenant_id
from .tenant import (
    TenantContext,
    TenantMiddleware,
    clear_tenant_context,
    ensure_tenant_access,
    get_tenant_context,
    require_tenant,
    require_tenant_context,
    set_tenant_context,
    tenant_scoped_query,
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
