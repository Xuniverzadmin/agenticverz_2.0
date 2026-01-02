# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: RBAC stub for CI/development - deterministic auth without external dependencies
# Callers: Auth middleware, API routes (when CLERK_ENABLED=false)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-271 (CI North Star), docs/infra/RBAC_STUB_DESIGN.md

"""
RBAC Stub for CI/Development

This module provides a minimal local RBAC stub that:
1. Exercises the same contract as Clerk
2. Requires no external API keys
3. Is deterministic (same input -> same output)
4. Enables all @requires_infra("Clerk") tests to run

Token Format:
    stub_<role>_<tenant>
    Example: stub_admin_tenant123

Usage:
    from app.auth.stub import parse_stub_token, StubClaims

    claims = parse_stub_token("stub_admin_test_tenant")
    if claims:
        # Use claims.sub, claims.org_id, claims.roles, claims.permissions
        pass

WARNING: This stub is for CI/development only. Never use in production.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Optional

# Environment variable to enable stub auth
AUTH_STUB_ENABLED = os.getenv("AUTH_STUB_ENABLED", "true").lower() == "true"


@dataclass
class StubClaims:
    """
    Claims structure matching Clerk's shape.

    This dataclass mirrors the claims returned by Clerk JWT tokens,
    allowing tests to use the same code paths regardless of auth provider.
    """

    sub: str  # Subject (user ID)
    org_id: str  # Organization/tenant ID
    roles: list[str] = field(default_factory=list)  # Role names
    permissions: list[str] = field(default_factory=list)  # Permission strings
    exp: int = 0  # Expiration timestamp
    iat: int = 0  # Issued at timestamp

    def __post_init__(self):
        """Set timestamps if not provided."""
        now = int(time.time())
        if self.iat == 0:
            self.iat = now
        if self.exp == 0:
            self.exp = now + 3600  # 1 hour validity


# =============================================================================
# STUB ROLE DEFINITIONS
# =============================================================================
# These must match the roles defined in docs/infra/RBAC_STUB_DESIGN.md

STUB_ROLES: dict[str, list[str]] = {
    "admin": ["*"],  # Full access
    "developer": ["read:*", "write:runs", "write:agents"],  # Normal user
    "viewer": ["read:*"],  # Read-only access
    "machine": ["read:*", "write:runs"],  # API key access
}


def parse_stub_token(token: str) -> Optional[StubClaims]:
    """
    Parse a stub token into claims.

    Stub tokens have format: stub_<role>_<tenant>
    Example: stub_admin_tenant123

    Args:
        token: The token string to parse

    Returns:
        StubClaims if token matches stub format and role is valid, None otherwise.

    Examples:
        >>> parse_stub_token("stub_admin_test_tenant")
        StubClaims(sub='stub_user_admin', org_id='test_tenant', roles=['admin'], ...)

        >>> parse_stub_token("real_jwt_token")
        None

        >>> parse_stub_token("stub_invalid_tenant")
        None  # 'invalid' is not a valid role
    """
    if not token:
        return None

    if not token.startswith("stub_"):
        return None

    parts = token.split("_", 2)
    if len(parts) != 3:
        return None

    _, role, tenant = parts

    # Validate role exists
    if role not in STUB_ROLES:
        return None

    return StubClaims(
        sub=f"stub_user_{role}",
        org_id=tenant,
        roles=[role],
        permissions=STUB_ROLES[role],
    )


def is_stub_token(token: str) -> bool:
    """
    Check if a token is a stub token without fully parsing it.

    Args:
        token: The token string to check

    Returns:
        True if token starts with 'stub_', False otherwise
    """
    return token.startswith("stub_") if token else False


def get_stub_token_for_role(role: str, tenant: str = "test_tenant") -> str:
    """
    Generate a stub token for a given role.

    This is useful for tests that need to generate auth headers.

    Args:
        role: One of 'admin', 'developer', 'viewer', 'machine'
        tenant: The tenant ID (default: 'test_tenant')

    Returns:
        A stub token string

    Raises:
        ValueError: If role is not valid

    Examples:
        >>> get_stub_token_for_role("admin")
        'stub_admin_test_tenant'

        >>> get_stub_token_for_role("developer", "my_org")
        'stub_developer_my_org'
    """
    if role not in STUB_ROLES:
        raise ValueError(f"Invalid role '{role}'. Valid roles: {list(STUB_ROLES.keys())}")
    return f"stub_{role}_{tenant}"


# =============================================================================
# CLAIMS CONVERSION
# =============================================================================


def stub_claims_to_dict(claims: StubClaims) -> dict:
    """
    Convert StubClaims to a dictionary matching Clerk JWT claims format.

    This allows downstream code to work with claims uniformly.

    Args:
        claims: StubClaims instance

    Returns:
        Dictionary with Clerk-compatible claim keys
    """
    return {
        "sub": claims.sub,
        "org_id": claims.org_id,
        "roles": claims.roles,
        "permissions": claims.permissions,
        "exp": claims.exp,
        "iat": claims.iat,
        # Additional fields that Clerk might include
        "azp": "stub_client",  # Authorized party
        "iss": "stub_issuer",  # Issuer
    }


# =============================================================================
# PERMISSION CHECKING
# =============================================================================


def stub_has_permission(claims: StubClaims, required_permission: str) -> bool:
    """
    Check if stub claims grant a required permission.

    Supports wildcard permissions ('*' grants all, 'read:*' grants all read).

    Args:
        claims: The StubClaims to check
        required_permission: The permission string required (e.g., 'read:agents')

    Returns:
        True if permission is granted, False otherwise

    Examples:
        >>> claims = parse_stub_token("stub_admin_test")
        >>> stub_has_permission(claims, "read:agents")
        True  # admin has '*'

        >>> claims = parse_stub_token("stub_viewer_test")
        >>> stub_has_permission(claims, "write:agents")
        False  # viewer only has 'read:*'
    """
    for perm in claims.permissions:
        # Full wildcard
        if perm == "*":
            return True

        # Exact match
        if perm == required_permission:
            return True

        # Prefix wildcard (e.g., 'read:*' matches 'read:agents')
        if perm.endswith(":*"):
            prefix = perm[:-1]  # 'read:'
            if required_permission.startswith(prefix):
                return True

    return False


def stub_has_role(claims: StubClaims, required_role: str) -> bool:
    """
    Check if stub claims include a required role.

    Args:
        claims: The StubClaims to check
        required_role: The role name required

    Returns:
        True if role is present, False otherwise
    """
    return required_role in claims.roles


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================


def validate_stub_or_skip(token: str) -> Optional[StubClaims]:
    """
    Validate a stub token, returning claims or None.

    This is the main integration point for middleware. It:
    1. Checks if AUTH_STUB_ENABLED is True
    2. Parses the stub token
    3. Returns claims if valid, None if not a stub token

    Args:
        token: The token to validate

    Returns:
        StubClaims if valid stub token and stub auth is enabled, None otherwise
    """
    if not AUTH_STUB_ENABLED:
        return None

    return parse_stub_token(token)
