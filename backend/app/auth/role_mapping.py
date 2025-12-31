# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Role-to-permission mapping engine
# Callers: RBAC engine, services
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Auth System

"""
Role Mapping - M7-M28 RBAC Integration (PIN-169)

ONE-WAY MAPPING ONLY: Console roles → RBAC roles
M7 RBAC roles are CANONICAL. M28 roles are presentation aliases.

INVARIANTS:
1. This mapping is ONE-WAY. Never invert.
2. If M28 invents authority, the invariant is broken.
3. Founder roles NEVER flow through tenant RBAC.

Created: 2025-12-25
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger("nova.auth.role_mapping")


# ============================================================================
# M28 Console Roles (Source - Presentation Layer)
# ============================================================================


class CustomerRole(str, Enum):
    """Customer Console roles (M28)."""

    OWNER = "OWNER"
    ADMIN = "ADMIN"
    DEV = "DEV"
    VIEWER = "VIEWER"


class FounderRole(str, Enum):
    """Founder Ops Console roles (M28)."""

    FOUNDER = "FOUNDER"
    OPERATOR = "OPERATOR"


# ============================================================================
# M7 RBAC Roles (Target - Canonical Authority)
# ============================================================================


class RBACRole(str, Enum):
    """
    Canonical RBAC roles (M7).

    These are the SOURCE OF TRUTH for authorization.
    All other role systems map TO these, never FROM these.
    """

    # Tenant-scoped roles
    ADMIN = "admin"  # Full tenant control
    INFRA = "infra"  # Ops + policy within tenant
    DEV = "dev"  # Build + runtime
    READONLY = "readonly"  # Read-only access
    MACHINE = "machine"  # Machine/integration token

    # Founder-scoped roles (ISOLATED - never flow through tenant RBAC)
    FOUNDER = "founder"  # Global non-tenant access
    OPERATOR = "operator"  # Scoped ops access


# ============================================================================
# ONE-WAY Role Mapping (M28 → M7)
# ============================================================================

# Customer Console roles → M7 RBAC roles (single canonical role each)
CUSTOMER_TO_RBAC: Dict[CustomerRole, RBACRole] = {
    CustomerRole.OWNER: RBACRole.ADMIN,  # Full tenant control
    CustomerRole.ADMIN: RBACRole.INFRA,  # Ops + policy within tenant
    CustomerRole.DEV: RBACRole.DEV,  # Build + runtime
    CustomerRole.VIEWER: RBACRole.READONLY,  # Read-only
}

# Founder Console roles → M7 RBAC roles (ISOLATED PATH)
# NOTE: These terminate early and NEVER flow through tenant RBAC
FOUNDER_TO_RBAC: Dict[FounderRole, RBACRole] = {
    FounderRole.FOUNDER: RBACRole.FOUNDER,  # Global, non-tenant
    FounderRole.OPERATOR: RBACRole.OPERATOR,  # Scoped ops
}


# ============================================================================
# Principal Model (Phase 2.5 - Identity Separation)
# ============================================================================


class PrincipalType(str, Enum):
    """Type of principal making the request."""

    CONSOLE = "console"  # Customer Console user
    FOPS = "fops"  # Founder Ops user
    MACHINE = "machine"  # Machine/integration token
    ANONYMOUS = "anonymous"  # No identity


@dataclass
class Principal:
    """
    Unified identity model extracted from request.

    X-AOS-Key → principal_type = "machine", principal_id = key_fingerprint
    Console JWT → principal_type = "console", principal_id = user_id
    FOPS JWT → principal_type = "fops", principal_id = founder_id
    """

    principal_id: str
    principal_type: PrincipalType
    tenant_id: Optional[str] = None  # None for founder paths
    source_token_type: str = "unknown"  # jwt, api_key, machine_token


# ============================================================================
# AuthContext Model (Phase 3 - Complete Auth Context)
# ============================================================================


@dataclass
class AuthContext:
    """
    Complete auth context for every request.

    INVARIANT: Every request has exactly one AuthContext.
    INVARIANT: Founders have tenant_id = None (enforced, not trusted).
    """

    principal_id: str
    principal_type: PrincipalType
    tenant_id: Optional[str]
    effective_roles: List[RBACRole] = field(default_factory=list)
    source_token_type: str = "unknown"
    # Shadow audit fields
    original_console_role: Optional[str] = None
    mapping_source: str = "unknown"

    def is_founder(self) -> bool:
        """Check if this is a founder context."""
        return self.principal_type == PrincipalType.FOPS

    def is_tenant_scoped(self) -> bool:
        """Check if this context is scoped to a tenant."""
        return self.tenant_id is not None

    def has_role(self, role: RBACRole) -> bool:
        """Check if context has a specific role."""
        return role in self.effective_roles


# ============================================================================
# Mapping Functions
# ============================================================================


def map_customer_role_to_rbac(customer_role: CustomerRole) -> RBACRole:
    """
    Map a Customer Console role to a SINGLE canonical RBAC role.

    INVARIANT: This is one-way. Never invert this mapping.
    If M28 invents authority, the invariant is broken.

    Args:
        customer_role: The M28 Customer Console role

    Returns:
        The canonical M7 RBAC role
    """
    rbac_role = CUSTOMER_TO_RBAC.get(customer_role)
    if rbac_role is None:
        logger.warning(f"Unknown customer role: {customer_role}, defaulting to readonly")
        return RBACRole.READONLY
    return rbac_role


def map_founder_role_to_rbac(founder_role: FounderRole) -> RBACRole:
    """
    Map a Founder Console role to a SINGLE canonical RBAC role.

    NOTE: Founder roles are ISOLATED and NEVER flow through tenant RBAC.
    The auth path terminates early for founders.

    Args:
        founder_role: The M28 Founder Console role

    Returns:
        The canonical M7 RBAC role (founder or operator)
    """
    rbac_role = FOUNDER_TO_RBAC.get(founder_role)
    if rbac_role is None:
        logger.warning(f"Unknown founder role: {founder_role}, defaulting to operator")
        return RBACRole.OPERATOR
    return rbac_role


def map_console_role_string(role_str: str, is_founder: bool = False) -> RBACRole:
    """
    Map a role string to RBAC role.

    Args:
        role_str: The role string (e.g., "OWNER", "ADMIN")
        is_founder: Whether this is a founder role

    Returns:
        The canonical M7 RBAC role
    """
    if is_founder:
        try:
            founder_role = FounderRole(role_str)
            return map_founder_role_to_rbac(founder_role)
        except ValueError:
            logger.warning(f"Invalid founder role string: {role_str}")
            return RBACRole.OPERATOR
    else:
        try:
            customer_role = CustomerRole(role_str)
            return map_customer_role_to_rbac(customer_role)
        except ValueError:
            logger.warning(f"Invalid customer role string: {role_str}")
            return RBACRole.READONLY


# ============================================================================
# Founder Isolation Guard
# ============================================================================


class FounderIsolationError(Exception):
    """Raised when founder context leaks into tenant scope."""

    pass


def guard_founder_isolation(ctx: AuthContext) -> None:
    """
    Founder paths must NEVER touch tenant data accidentally.

    MANDATORY: Founder access is nuclear privilege. Treat like root.

    Raises:
        FounderIsolationError: If founder has tenant_id set
    """
    if ctx.principal_type == PrincipalType.FOPS:
        if ctx.tenant_id is not None:
            logger.error(
                "founder_isolation_violation",
                extra={
                    "principal_id": ctx.principal_id,
                    "tenant_id": ctx.tenant_id,
                    "roles": [r.value for r in ctx.effective_roles],
                },
            )
            raise FounderIsolationError(
                f"SECURITY: Founder principal {ctx.principal_id} leaked into tenant context {ctx.tenant_id}"
            )


# ============================================================================
# Role Hierarchy Helpers
# ============================================================================


def get_role_hierarchy() -> Dict[RBACRole, int]:
    """
    Get role hierarchy levels (higher = more privileged).

    Used for checking if one role subsumes another.
    """
    return {
        RBACRole.READONLY: 10,
        RBACRole.DEV: 20,
        RBACRole.MACHINE: 25,
        RBACRole.INFRA: 30,
        RBACRole.ADMIN: 40,
        RBACRole.OPERATOR: 50,
        RBACRole.FOUNDER: 100,
    }


def role_subsumes(higher: RBACRole, lower: RBACRole) -> bool:
    """
    Check if a higher role subsumes a lower role.

    Args:
        higher: The potentially higher role
        lower: The potentially lower role

    Returns:
        True if higher role subsumes lower role
    """
    hierarchy = get_role_hierarchy()
    return hierarchy.get(higher, 0) >= hierarchy.get(lower, 0)


# ============================================================================
# AuthContext Builder
# ============================================================================


def build_auth_context(
    principal_id: str,
    principal_type: PrincipalType,
    tenant_id: Optional[str] = None,
    console_role: Optional[str] = None,
    source_token_type: str = "unknown",
    mapping_source: str = "unknown",
) -> AuthContext:
    """
    Build an AuthContext from request data.

    This is the SINGLE ENTRY POINT for creating auth contexts.
    It maps console roles to RBAC roles and enforces founder isolation.

    Args:
        principal_id: Unique identifier for the principal
        principal_type: Type of principal (console, fops, machine, anonymous)
        tenant_id: Tenant ID (MUST be None for founders)
        console_role: Original console role string (e.g., "OWNER", "FOUNDER")
        source_token_type: Type of auth token (jwt, api_key, machine_token)
        mapping_source: Where the role came from (console_auth, fops_auth, etc.)

    Returns:
        AuthContext with mapped RBAC roles

    Raises:
        FounderIsolationError: If founder has tenant_id set
    """
    effective_roles: List[RBACRole] = []

    if principal_type == PrincipalType.FOPS:
        # Founder path - map founder role
        if console_role:
            rbac_role = map_console_role_string(console_role, is_founder=True)
        else:
            rbac_role = RBACRole.OPERATOR  # Default for founders
        effective_roles = [rbac_role]

    elif principal_type == PrincipalType.CONSOLE:
        # Customer path - map customer role
        if console_role:
            rbac_role = map_console_role_string(console_role, is_founder=False)
        else:
            rbac_role = RBACRole.READONLY  # Default for customers
        effective_roles = [rbac_role]

    elif principal_type == PrincipalType.MACHINE:
        # Machine token - gets machine role
        effective_roles = [RBACRole.MACHINE]

    else:
        # Anonymous - readonly only
        effective_roles = [RBACRole.READONLY]

    ctx = AuthContext(
        principal_id=principal_id,
        principal_type=principal_type,
        tenant_id=tenant_id,
        effective_roles=effective_roles,
        source_token_type=source_token_type,
        original_console_role=console_role,
        mapping_source=mapping_source,
    )

    # Enforce founder isolation
    guard_founder_isolation(ctx)

    logger.debug(
        f"Built auth context: principal={principal_id}, type={principal_type.value}, "
        f"roles={[r.value for r in effective_roles]}, tenant={tenant_id}"
    )

    return ctx


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Enums
    "CustomerRole",
    "FounderRole",
    "RBACRole",
    "PrincipalType",
    # Dataclasses
    "Principal",
    "AuthContext",
    # Mapping functions
    "map_customer_role_to_rbac",
    "map_founder_role_to_rbac",
    "map_console_role_string",
    # Context builder
    "build_auth_context",
    # Mappings (for testing/inspection)
    "CUSTOMER_TO_RBAC",
    "FOUNDER_TO_RBAC",
    # Guards
    "guard_founder_isolation",
    "FounderIsolationError",
    # Hierarchy
    "get_role_hierarchy",
    "role_subsumes",
]
