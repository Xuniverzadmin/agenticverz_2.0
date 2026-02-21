# capability_id: CAP-012
# Layer: L5 — Domain Subdomain
# Product: system-wide
# AUDIENCE: INTERNAL
# Role: Authentication and authorization subdomain of account
# Reference: PIN-271 (RBAC Authority Separation)

"""
Account Auth Subdomain

Contains:
- L5_engines/rbac_engine.py - RBAC authorization engine (M7 Legacy)
- L5_engines/identity_adapter.py - Identity extraction adapters
"""

from app.hoc.cus.account.auth.L5_engines.rbac_engine import (
    Decision,
    PolicyConfig,
    PolicyObject,
    RBACEngine,
    check_permission,
    get_rbac_engine,
    init_rbac_engine,
    require_permission,
    # Role mapping functions
    get_max_approval_level,
    get_role_approval_level,
    map_external_role_to_aos,
    map_external_roles_to_aos,
)

from app.hoc.cus.account.auth.L5_engines.identity_adapter import (
    AuthenticationError,
    ClerkAdapter,
    DevIdentityAdapter,
    IdentityAdapter,
    SystemIdentityAdapter,
)

__all__ = [
    # RBAC Engine
    "RBACEngine",
    "PolicyObject",
    "Decision",
    "PolicyConfig",
    "get_rbac_engine",
    "init_rbac_engine",
    "check_permission",
    "require_permission",
    # Role mapping
    "get_role_approval_level",
    "get_max_approval_level",
    "map_external_role_to_aos",
    "map_external_roles_to_aos",
    # Identity adapters
    "IdentityAdapter",
    "ClerkAdapter",
    "SystemIdentityAdapter",
    "DevIdentityAdapter",
    "AuthenticationError",
]
