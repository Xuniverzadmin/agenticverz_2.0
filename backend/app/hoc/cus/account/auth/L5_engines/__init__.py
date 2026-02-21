# capability_id: CAP-012
# Layer: L5 — Domain Engines
# Product: system-wide
# AUDIENCE: INTERNAL
# Role: Auth domain engines for account subdomain

"""
Auth L5 Engines

- rbac_engine.py - RBAC authorization engine (M7 Legacy)
- identity_adapter.py - Identity extraction adapters
- invocation_safety.py - Invocation safety layer (CAP-020, CAP-021)
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

from app.hoc.cus.account.auth.L5_engines.invocation_safety import (
    # Core types
    SafetyFlag,
    Severity,
    SafetyCheckResult,
    InvocationSafetyContext,
    InvocationSafetyResult,
    # Check functions
    check_identity_resolved,
    check_impersonation_declared,
    check_rate_limit,
    check_plan_injection,
    compute_plan_hash,
    run_safety_checks,
    # Hook classes
    CLISafetyHook,
    SDKSafetyHook,
    # Singletons
    cli_safety_hook,
    sdk_safety_hook,
    # Metrics
    emit_safety_metrics,
    emit_safety_audit_event,
    SafetyCheckTimer,
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
    "get_role_approval_level",
    "get_max_approval_level",
    "map_external_role_to_aos",
    "map_external_roles_to_aos",
    # Identity Adapters
    "IdentityAdapter",
    "ClerkAdapter",
    "SystemIdentityAdapter",
    "DevIdentityAdapter",
    "AuthenticationError",
    # Invocation Safety (CAP-020, CAP-021)
    "SafetyFlag",
    "Severity",
    "SafetyCheckResult",
    "InvocationSafetyContext",
    "InvocationSafetyResult",
    "check_identity_resolved",
    "check_impersonation_declared",
    "check_rate_limit",
    "check_plan_injection",
    "compute_plan_hash",
    "run_safety_checks",
    "CLISafetyHook",
    "SDKSafetyHook",
    "cli_safety_hook",
    "sdk_safety_hook",
    "emit_safety_metrics",
    "emit_safety_audit_event",
    "SafetyCheckTimer",
]
