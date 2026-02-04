# Layer: L5 — Domain Engines
# Product: system-wide
# AUDIENCE: INTERNAL
# Role: Auth domain engines for account subdomain

"""
Auth L5 Engines

- rbac_engine.py - RBAC authorization engine (M7 Legacy)
- identity_adapter.py - Identity extraction adapters
"""

from app.hoc.cus.account.auth.L5_engines.rbac_engine import (
    Decision,
    PolicyConfig,
    PolicyObject,
    RBACEngine,
    check_permission,
    get_policy_for_path,
    get_rbac_engine,
    init_rbac_engine,
    require_permission,
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
    "RBACEngine",
    "PolicyObject",
    "Decision",
    "PolicyConfig",
    "get_rbac_engine",
    "init_rbac_engine",
    "check_permission",
    "require_permission",
    "get_policy_for_path",
    "get_role_approval_level",
    "get_max_approval_level",
    "map_external_role_to_aos",
    "map_external_roles_to_aos",
    "IdentityAdapter",
    "ClerkAdapter",
    "SystemIdentityAdapter",
    "DevIdentityAdapter",
    "AuthenticationError",
]
