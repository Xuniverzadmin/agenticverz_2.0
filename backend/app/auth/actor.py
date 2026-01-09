# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api | worker | internal
#   Execution: sync
# Role: Canonical actor model for all authorization decisions
# Callers: AuthorizationEngine, IdentityAdapters, API middleware
# Allowed Imports: (none - leaf module)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-271 (RBAC Authority Separation)

"""
ActorContext: The canonical actor model for AOS.

All authorization decisions consume this model.
No endpoint, worker, or service inspects raw JWTs ever again.

This module is a leaf in the dependency graph - it imports nothing
from the app package to prevent circular dependencies.

Usage:
    from app.auth.actor import ActorContext, ActorType, IdentitySource

    actor = ActorContext(
        actor_id="user-123",
        actor_type=ActorType.EXTERNAL_PAID,
        source=IdentitySource.CLERK,
        tenant_id="tenant-abc",
        account_id="acct-xyz",
        team_id="team-1",
        roles=frozenset({"admin"}),
        permissions=frozenset(),  # Computed by AuthorizationEngine
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Optional


class ActorType(str, Enum):
    """
    Classification of actors for policy enforcement.

    This enum is the primary policy driver - it determines
    what permissions an actor can possibly have, regardless
    of their roles.
    """

    EXTERNAL_PAID = "external_paid"  # Paying customers
    EXTERNAL_TRIAL = "external_trial"  # Beta, trial users
    INTERNAL_PRODUCT = "internal_product"  # Xuniverz, AI Console, M12 agents
    OPERATOR = "operator"  # Founders, ops team
    SYSTEM = "system"  # CI, workers, replay


class IdentitySource(str, Enum):
    """
    How the identity was established.

    This is metadata for audit/debugging - it does NOT
    affect authorization decisions.
    """

    CONSOLE = "console"  # Internal console HS256 JWT (transitional)
    CLERK = "clerk"  # Production Clerk RS256 JWT
    OIDC = "oidc"  # Keycloak/generic OIDC
    INTERNAL = "internal"  # Internal service-to-service
    SYSTEM = "system"  # CI, workers, automation
    DEV = "dev"  # Local development


@dataclass(frozen=True)
class ActorContext:
    """
    Immutable, canonical representation of an authenticated actor.

    All authorization decisions consume this model.
    No endpoint, worker, or service inspects raw JWTs ever again.

    Invariants:
    - This is the ONLY input to AuthorizationEngine
    - Once created, it cannot be modified (frozen=True)
    - Permissions are computed by AuthorizationEngine, not stored in tokens

    Enterprise Hierarchy:
    - tenant_id: Logical isolation boundary (data partition)
    - account_id: Enterprise account (parent, for billing/admin)
    - team_id: Sub-team within account (for team-level policies)

    Layer: L6 (Platform Substrate)
    """

    # Identity
    actor_id: str  # Unique identifier (e.g., "user-123", "system:ci")
    actor_type: ActorType  # Classification for policy
    source: IdentitySource  # How identity was established

    # Enterprise hierarchy (None for operators/system)
    tenant_id: Optional[str]  # Logical isolation boundary
    account_id: Optional[str]  # Enterprise account (parent)
    team_id: Optional[str]  # Sub-team within account

    # Authorization grants
    roles: FrozenSet[str]  # e.g., {"admin", "dev"}
    permissions: FrozenSet[str]  # e.g., {"read:runs", "write:agents"}

    # Metadata (non-authoritative, for display/audit only)
    email: Optional[str] = None
    display_name: Optional[str] = None

    def has_role(self, role: str) -> bool:
        """Check if actor has a specific role."""
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """
        Check if actor has a specific permission or wildcard match.

        Supports:
        - Exact match: "read:runs"
        - Global wildcard: "*"
        - Action wildcard: "read:*"
        """
        if "*" in self.permissions:
            return True
        if permission in self.permissions:
            return True

        # Check wildcard patterns: "read:*" matches "read:runs"
        parts = permission.split(":")
        if len(parts) >= 2:
            action = parts[0]
            wildcard = f"{action}:*"
            if wildcard in self.permissions:
                return True

        return False

    def is_operator(self) -> bool:
        """Check if actor has operator-level access."""
        return self.actor_type == ActorType.OPERATOR

    def is_system(self) -> bool:
        """Check if actor is a system/automation actor."""
        return self.actor_type == ActorType.SYSTEM

    def is_tenant_scoped(self) -> bool:
        """Check if actor is scoped to a specific tenant."""
        return self.tenant_id is not None

    def is_account_scoped(self) -> bool:
        """Check if actor belongs to an enterprise account."""
        return self.account_id is not None

    def is_team_scoped(self) -> bool:
        """Check if actor belongs to a specific team."""
        return self.team_id is not None

    def same_tenant(self, other: ActorContext) -> bool:
        """Check if two actors belong to the same tenant."""
        if self.tenant_id is None or other.tenant_id is None:
            return False
        return self.tenant_id == other.tenant_id

    def same_account(self, other: ActorContext) -> bool:
        """Check if two actors belong to the same account."""
        if self.account_id is None or other.account_id is None:
            return False
        return self.account_id == other.account_id

    def same_team(self, other: ActorContext) -> bool:
        """Check if two actors belong to the same team."""
        if self.team_id is None or other.team_id is None:
            return False
        return self.team_id == other.team_id

    def __repr__(self) -> str:
        """Concise representation for logging."""
        return f"Actor({self.actor_id}, type={self.actor_type.value}, tenant={self.tenant_id}, roles={set(self.roles)})"


# =============================================================================
# Predefined System Actors
# =============================================================================
# These are the canonical system actors used by CI, workers, and replay.
# They have fixed permissions and are NOT derived from roles.

SYSTEM_ACTORS: dict[str, ActorContext] = {
    "ci": ActorContext(
        actor_id="system:ci",
        actor_type=ActorType.SYSTEM,
        source=IdentitySource.SYSTEM,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"ci", "automation"}),
        permissions=frozenset({"read:*", "write:metrics", "write:traces"}),
        email=None,
        display_name="CI Pipeline",
    ),
    "worker": ActorContext(
        actor_id="system:worker",
        actor_type=ActorType.SYSTEM,
        source=IdentitySource.SYSTEM,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"machine", "worker"}),
        permissions=frozenset({"read:*", "write:runs", "write:traces"}),
        email=None,
        display_name="Background Worker",
    ),
    "replay": ActorContext(
        actor_id="system:replay",
        actor_type=ActorType.SYSTEM,
        source=IdentitySource.SYSTEM,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"replay", "readonly"}),
        permissions=frozenset({"read:*", "execute:replay"}),
        email=None,
        display_name="Replay System",
    ),
    "internal_product": ActorContext(
        actor_id="system:internal_product",
        actor_type=ActorType.INTERNAL_PRODUCT,
        source=IdentitySource.INTERNAL,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"internal", "product"}),
        permissions=frozenset({"read:*", "write:runs", "write:agents", "execute:*"}),
        email=None,
        display_name="Internal Product",
    ),
}


def get_system_actor(name: str) -> Optional[ActorContext]:
    """
    Get a predefined system actor by name.

    Args:
        name: One of "ci", "worker", "replay", "internal_product"

    Returns:
        ActorContext if found, None otherwise
    """
    return SYSTEM_ACTORS.get(name)


# =============================================================================
# Factory Functions
# =============================================================================


def create_operator_actor(
    actor_id: str,
    email: Optional[str] = None,
    display_name: Optional[str] = None,
) -> ActorContext:
    """
    Create an operator (founder/admin) actor.

    Operators have full access and are not scoped to any tenant.
    """
    return ActorContext(
        actor_id=actor_id,
        actor_type=ActorType.OPERATOR,
        source=IdentitySource.CLERK,  # Operators use Clerk auth
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"founder", "operator"}),
        permissions=frozenset({"*"}),  # Full access
        email=email,
        display_name=display_name,
    )


def create_external_actor(
    actor_id: str,
    tenant_id: str,
    account_id: Optional[str],
    team_id: Optional[str],
    roles: FrozenSet[str],
    is_paid: bool = True,
    email: Optional[str] = None,
    display_name: Optional[str] = None,
) -> ActorContext:
    """
    Create an external (customer) actor.

    External actors are always scoped to a tenant.
    Permissions are computed by AuthorizationEngine based on roles.
    """
    return ActorContext(
        actor_id=actor_id,
        actor_type=ActorType.EXTERNAL_PAID if is_paid else ActorType.EXTERNAL_TRIAL,
        source=IdentitySource.CLERK,
        tenant_id=tenant_id,
        account_id=account_id,
        team_id=team_id,
        roles=roles,
        permissions=frozenset(),  # Computed by AuthorizationEngine
        email=email,
        display_name=display_name,
    )
