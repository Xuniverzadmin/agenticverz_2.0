"""
Auth module for AOS.

Provides RBAC integration, Clerk auth (M8+), OIDC/Keycloak (legacy),
and authentication utilities.
"""

import os

from fastapi import Header, HTTPException, status

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
    # RBAC
    "ApprovalLevel",
    "RBACError",
    "RBACResult",
    "check_approver_permission",
    "require_approval_level",
    "USE_CLERK_AUTH",
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
