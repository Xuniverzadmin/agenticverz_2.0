"""
Auth module for AOS.

Provides Clerk-based authentication (the ONLY human auth path) and
authorization utilities.

Reference: AUTH_DESIGN.md
- AUTH-HUMAN-001: All human users authenticate via Clerk (RS256 JWKS)
- AUTH-HUMAN-002: No other human authentication mechanism exists
- AUTH-MACHINE-001: Machine clients authenticate via API Key
"""

import os

from fastapi import Header, HTTPException, status

# Authorization Choke Point (PIN-271, I-AUTH-001)
# This is the SINGLE entry point for all authorization decisions
from .authorization_choke import (
    M7_LEGACY_RESOURCES,
    M28_NATIVE_RESOURCES,
    AuthorizationDecision,
    AuthorizationSource,
    AuthzPhase,
    authorize_action,
    can_access,
    get_authz_phase,
    is_strict_mode,
    require_permission,
)
from .clerk_provider import (
    ClerkAuthError,
    ClerkAuthProvider,
    ClerkUser,
    get_clerk_provider,
    get_user_roles_from_clerk,
)
from .jwt_auth import (
    JWTAuthDependency,
    JWTConfig,
    TokenPayload,
    create_dev_token,
    get_jwt_auth,
)
from .jwt_auth import (
    verify_token as verify_jwt_token,
)
from .oidc_provider import (
    OIDC_ENABLED,
    OIDCError,
    TokenValidationError,
    get_roles_from_token,
    get_user_info_from_token,
    map_keycloak_roles_to_aos,
    validate_and_extract,
    validate_token,
)
from .rbac import (
    USE_CLERK_AUTH,
    ApprovalLevel,
    RBACError,
    RBACResult,
    check_approver_permission,
    require_approval_level,
)

# M7-M28 RBAC Integration (PIN-169)
from .role_mapping import (
    AuthContext,
    CustomerRole,
    FounderIsolationError,
    FounderRole,
    Principal,
    PrincipalType,
    RBACRole,
    build_auth_context,
    guard_founder_isolation,
    map_console_role_string,
    map_customer_role_to_rbac,
    map_founder_role_to_rbac,
    role_subsumes,
)
from .shadow_audit import (
    ROLLOUT_GATES,
    SHADOW_AUDIT_ENABLED,
    ShadowAuditAggregator,
    ShadowAuditEvent,
    ShadowAuditLogger,
    record_shadow_audit_metric,
    shadow_aggregator,
    shadow_audit,
)

# =============================================================================
# PIN-271 Auth Migration (2026-02-04)
# =============================================================================
# RBAC Engine and Identity Adapter moved to canonical location:
#   from app.hoc.cus.account.auth import RBACEngine, ClerkAdapter, ...
#
# Old paths DELETED (no shims):
#   - app.auth.rbac_engine (DELETED)
#   - app.auth.identity_adapter (DELETED)

# STUB AUTHENTICATION REMOVED
# Reference: AUTH_DESIGN.md (AUTH-HUMAN-004)
# Stub tokens are not valid in any environment.

# M21 Tenant Auth - DISABLED for beta stage
# from .tenant_auth import (
#     TenantContext,
#     get_tenant_context,
#     require_permission,
#     require_worker_access,
#     verify_api_key_with_fallback,
#     hash_api_key,
# )

# API Key configuration
AOS_API_KEY = os.getenv("AOS_API_KEY", "")


async def verify_api_key(x_aos_key: str = Header(..., alias="X-AOS-Key")):
    """
    Verify the API key from X-AOS-Key header.
    Rejects all requests without a valid key.
    """
    if not AOS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server misconfigured: AOS_API_KEY not set"
        )

    if x_aos_key != AOS_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    return x_aos_key


__all__ = [
    # Authorization Choke Point (PIN-271, I-AUTH-001)
    # This is the SINGLE entry point for all authorization decisions
    "AuthorizationDecision",
    "AuthorizationSource",
    "AuthzPhase",
    "M7_LEGACY_RESOURCES",
    "M28_NATIVE_RESOURCES",
    "authorize_action",
    "can_access",
    "get_authz_phase",
    "is_strict_mode",
    "require_permission",
    # RBAC
    "ApprovalLevel",
    "RBACError",
    "RBACResult",
    "check_approver_permission",
    "require_approval_level",
    "USE_CLERK_AUTH",
    # M7-M28 Role Mapping (PIN-169)
    "AuthContext",
    "CustomerRole",
    "FounderRole",
    "FounderIsolationError",
    "Principal",
    "PrincipalType",
    "RBACRole",
    "build_auth_context",
    "guard_founder_isolation",
    "map_console_role_string",
    "map_customer_role_to_rbac",
    "map_founder_role_to_rbac",
    "role_subsumes",
    # Shadow Audit (PIN-169)
    "SHADOW_AUDIT_ENABLED",
    "ROLLOUT_GATES",
    "ShadowAuditEvent",
    "ShadowAuditLogger",
    "ShadowAuditAggregator",
    "shadow_audit",
    "shadow_aggregator",
    "record_shadow_audit_metric",
    # Clerk Auth (M8+)
    "ClerkAuthProvider",
    "ClerkAuthError",
    "ClerkUser",
    "get_clerk_provider",
    "get_user_roles_from_clerk",
    # API Key (Simple env-based)
    "verify_api_key",
    "AOS_API_KEY",
    # Tenant Auth (M21) - DISABLED for beta stage
    # "TenantContext",
    # "get_tenant_context",
    # "require_permission",
    # "require_worker_access",
    # "verify_api_key_with_fallback",
    # "hash_api_key",
    # OIDC (Legacy - Keycloak)
    "OIDC_ENABLED",
    "OIDCError",
    "TokenValidationError",
    "validate_token",
    "validate_and_extract",
    "get_roles_from_token",
    "get_user_info_from_token",
    "map_keycloak_roles_to_aos",
    # JWT Auth (M8)
    "JWTConfig",
    "JWTAuthDependency",
    "get_jwt_auth",
    "verify_jwt_token",
    "TokenPayload",
    "create_dev_token",
]
