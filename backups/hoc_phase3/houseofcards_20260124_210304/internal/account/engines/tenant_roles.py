# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Phase-5 Tenant Role enum and permission derivation
# Callers: require_role dependency, tenant_members model, role guard
# Allowed Imports: None (foundational enum)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 Phase-5 (Post-Onboarding Permissions & Roles)

"""
Phase-5 Tenant Roles — Post-Onboarding Authority Model

PIN-399 Phase-5: Roles do not exist until onboarding is COMPLETE.

DESIGN INVARIANTS (LOCKED):
- ROLE-001: Roles do not exist before onboarding COMPLETE
- ROLE-002: Permissions are derived, not stored
- ROLE-003: Human roles never affect machine scopes
- ROLE-004: Console origin never grants authority
- ROLE-005: Role enforcement never mutates state

ROLE HIERARCHY:
    OWNER  → Full control of tenant
    ADMIN  → Manage config, users
    MEMBER → Operate product
    VIEWER → Read-only

MACHINE AUTHORITY:
    Machine contexts (API keys) BYPASS this system entirely.
    They use scope-based authorization, not roles.

This enum is the single source of truth for Phase-5 tenant roles.
"""

from enum import IntEnum
from typing import FrozenSet


class TenantRole(IntEnum):
    """
    Phase-5 Tenant Roles (Human-only, Tenant-scoped).

    Roles are ordered by privilege level.
    Higher value = more privileged.
    Comparison operators work naturally: VIEWER < MEMBER < ADMIN < OWNER

    INVARIANTS:
    - Every tenant has at least one OWNER
    - Roles only exist after onboarding COMPLETE
    - Roles are tenant-scoped (no cross-tenant roles)
    """

    VIEWER = 1   # Read-only access
    MEMBER = 2   # Operate product (runs, policies)
    ADMIN = 3    # Manage config, users, api keys
    OWNER = 4    # Full control of tenant

    @classmethod
    def from_string(cls, value: str) -> "TenantRole":
        """
        Parse role from string (case-insensitive).

        Raises ValueError if unknown role.
        """
        normalized = value.upper().strip()
        try:
            return cls[normalized]
        except KeyError:
            valid = [r.name for r in cls]
            raise ValueError(f"Unknown tenant role: {value}. Valid: {valid}")

    def display_name(self) -> str:
        """Human-readable role name."""
        return self.name.capitalize()


# =============================================================================
# PERMISSION DERIVATION (Code Only — No DB Storage)
# =============================================================================

# Permission vocabulary (action:resource format)
# These are derived from roles, NEVER stored in database.

# Read permissions
PERM_RUNS_READ = "runs:read"
PERM_POLICIES_READ = "policies:read"
PERM_AGENTS_READ = "agents:read"
PERM_INCIDENTS_READ = "incidents:read"
PERM_REPORTS_READ = "reports:read"
PERM_USERS_READ = "users:read"
PERM_API_KEYS_READ = "api_keys:read"
PERM_TENANT_READ = "tenant:read"
PERM_BILLING_READ = "billing:read"

# Write permissions
PERM_RUNS_WRITE = "runs:write"
PERM_POLICIES_WRITE = "policies:write"
PERM_AGENTS_WRITE = "agents:write"

# Manage permissions
PERM_USERS_MANAGE = "users:manage"
PERM_API_KEYS_MANAGE = "api_keys:manage"
PERM_TENANT_WRITE = "tenant:write"
PERM_BILLING_MANAGE = "billing:manage"


# Role → Permissions mapping (derived at runtime, not stored)
# INVARIANT: No wildcard permissions stored in DB.
# Wildcards exist only in code-level derivation.

ROLE_PERMISSIONS: dict[TenantRole, FrozenSet[str]] = {
    TenantRole.VIEWER: frozenset({
        PERM_RUNS_READ,
        PERM_POLICIES_READ,
        PERM_AGENTS_READ,
        PERM_INCIDENTS_READ,
        PERM_REPORTS_READ,
        PERM_TENANT_READ,
    }),

    TenantRole.MEMBER: frozenset({
        # All VIEWER permissions
        PERM_RUNS_READ,
        PERM_POLICIES_READ,
        PERM_AGENTS_READ,
        PERM_INCIDENTS_READ,
        PERM_REPORTS_READ,
        PERM_TENANT_READ,
        # Plus write permissions
        PERM_RUNS_WRITE,
        PERM_POLICIES_WRITE,
        PERM_AGENTS_WRITE,
    }),

    TenantRole.ADMIN: frozenset({
        # All MEMBER permissions
        PERM_RUNS_READ,
        PERM_POLICIES_READ,
        PERM_AGENTS_READ,
        PERM_INCIDENTS_READ,
        PERM_REPORTS_READ,
        PERM_TENANT_READ,
        PERM_RUNS_WRITE,
        PERM_POLICIES_WRITE,
        PERM_AGENTS_WRITE,
        # Plus management permissions
        PERM_USERS_READ,
        PERM_USERS_MANAGE,
        PERM_API_KEYS_READ,
        PERM_API_KEYS_MANAGE,
        PERM_TENANT_WRITE,
        PERM_BILLING_READ,
    }),

    TenantRole.OWNER: frozenset({
        # All ADMIN permissions
        PERM_RUNS_READ,
        PERM_POLICIES_READ,
        PERM_AGENTS_READ,
        PERM_INCIDENTS_READ,
        PERM_REPORTS_READ,
        PERM_TENANT_READ,
        PERM_RUNS_WRITE,
        PERM_POLICIES_WRITE,
        PERM_AGENTS_WRITE,
        PERM_USERS_READ,
        PERM_USERS_MANAGE,
        PERM_API_KEYS_READ,
        PERM_API_KEYS_MANAGE,
        PERM_TENANT_WRITE,
        PERM_BILLING_READ,
        # Plus billing management (owner-only)
        PERM_BILLING_MANAGE,
    }),
}


def get_permissions_for_role(role: TenantRole) -> FrozenSet[str]:
    """
    Derive permissions from role.

    INVARIANT: Permissions are DERIVED, not stored.
    This function is the single source of permission derivation.

    Args:
        role: The tenant role

    Returns:
        FrozenSet of permission strings
    """
    return ROLE_PERMISSIONS.get(role, frozenset())


def role_has_permission(role: TenantRole, permission: str) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: The tenant role
        permission: Permission string (e.g., "runs:write")

    Returns:
        True if role has the permission
    """
    return permission in get_permissions_for_role(role)


def role_subsumes(higher: TenantRole, lower: TenantRole) -> bool:
    """
    Check if a higher role subsumes (includes all permissions of) a lower role.

    Args:
        higher: The potentially higher role
        lower: The potentially lower role

    Returns:
        True if higher >= lower in privilege hierarchy
    """
    return higher >= lower


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Role enum
    "TenantRole",
    # Permission derivation
    "get_permissions_for_role",
    "role_has_permission",
    "role_subsumes",
    # Permission constants (for type-safe usage)
    "PERM_RUNS_READ",
    "PERM_RUNS_WRITE",
    "PERM_POLICIES_READ",
    "PERM_POLICIES_WRITE",
    "PERM_AGENTS_READ",
    "PERM_AGENTS_WRITE",
    "PERM_INCIDENTS_READ",
    "PERM_REPORTS_READ",
    "PERM_USERS_READ",
    "PERM_USERS_MANAGE",
    "PERM_API_KEYS_READ",
    "PERM_API_KEYS_MANAGE",
    "PERM_TENANT_READ",
    "PERM_TENANT_WRITE",
    "PERM_BILLING_READ",
    "PERM_BILLING_MANAGE",
    # Role → Permissions mapping
    "ROLE_PERMISSIONS",
]
