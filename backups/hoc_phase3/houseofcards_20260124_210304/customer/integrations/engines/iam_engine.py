# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# PHASE: W2
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: IAM engine for identity and access management
# Callers: Auth middleware, API routes
# Allowed Imports: L6, L7
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: GAP-173 (IAM Integration)
# NOTE: Renamed iam_service.py → iam_engine.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_engine.py)
#       Reclassified L4→L5 - Per HOC topology, engines are L5 (business logic)

"""
IAM Engine (GAP-173)

Provides unified IAM capabilities:
- Identity resolution from multiple providers
- Role and permission management
- Access control decisions
- Audit logging
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class IdentityProvider(str, Enum):
    """Supported identity providers."""

    CLERK = "clerk"
    AUTH0 = "auth0"
    OIDC = "oidc"
    SYSTEM = "system"  # Internal system identities
    API_KEY = "api_key"  # API key-based identities


class ActorType(str, Enum):
    """Types of actors in the system."""

    HUMAN = "human"  # Human users
    MACHINE = "machine"  # API clients, SDKs
    SYSTEM = "system"  # Internal services


@dataclass
class Identity:
    """Resolved identity from any provider."""

    identity_id: str
    provider: IdentityProvider
    actor_type: ActorType

    # Basic info
    email: Optional[str] = None
    name: Optional[str] = None

    # Organization
    tenant_id: Optional[str] = None
    account_id: Optional[str] = None
    team_ids: List[str] = field(default_factory=list)

    # Roles and permissions
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)

    # Provider-specific data
    provider_data: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    authenticated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    def has_role(self, role: str) -> bool:
        """Check if identity has a specific role."""
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """Check if identity has a specific permission."""
        return permission in self.permissions

    def has_any_role(self, roles: List[str]) -> bool:
        """Check if identity has any of the specified roles."""
        return bool(self.roles & set(roles))

    def has_all_roles(self, roles: List[str]) -> bool:
        """Check if identity has all specified roles."""
        return set(roles).issubset(self.roles)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "identity_id": self.identity_id,
            "provider": self.provider.value,
            "actor_type": self.actor_type.value,
            "email": self.email,
            "name": self.name,
            "tenant_id": self.tenant_id,
            "account_id": self.account_id,
            "team_ids": self.team_ids,
            "roles": list(self.roles),
            "permissions": list(self.permissions),
            "authenticated_at": self.authenticated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass
class AccessDecision:
    """Result of an access control decision."""

    allowed: bool
    identity: Identity
    resource: str
    action: str

    # Decision details
    reason: Optional[str] = None
    matched_rule: Optional[str] = None
    denied_permissions: List[str] = field(default_factory=list)

    # Audit
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "allowed": self.allowed,
            "identity_id": self.identity.identity_id,
            "resource": self.resource,
            "action": self.action,
            "reason": self.reason,
            "matched_rule": self.matched_rule,
            "denied_permissions": self.denied_permissions,
            "decided_at": self.decided_at.isoformat(),
        }


class IAMService:
    """
    IAM Service for identity and access management.

    Features:
    - Multi-provider identity resolution
    - Role-based access control (RBAC)
    - Permission checking
    - Access decision auditing
    """

    def __init__(self):
        self._role_permissions: Dict[str, Set[str]] = {}
        self._resource_permissions: Dict[str, Set[str]] = {}
        self._access_log: List[AccessDecision] = []
        self._setup_default_roles()

    def _setup_default_roles(self) -> None:
        """Set up default role-permission mappings."""
        self._role_permissions = {
            # Admin role
            "admin": {
                "read:*",
                "write:*",
                "delete:*",
                "manage:users",
                "manage:policies",
                "manage:integrations",
            },
            # Developer role
            "developer": {
                "read:runs",
                "write:runs",
                "read:agents",
                "write:agents",
                "read:policies",
                "read:logs",
            },
            # Viewer role
            "viewer": {
                "read:runs",
                "read:agents",
                "read:policies",
                "read:logs",
            },
            # System role (for internal services)
            "system": {
                "read:*",
                "write:*",
                "system:execute",
            },
        }

        self._resource_permissions = {
            "runs": {"read:runs", "write:runs", "delete:runs"},
            "agents": {"read:agents", "write:agents", "delete:agents"},
            "policies": {"read:policies", "write:policies", "delete:policies", "manage:policies"},
            "integrations": {"read:integrations", "write:integrations", "manage:integrations"},
            "users": {"read:users", "write:users", "manage:users"},
            "logs": {"read:logs"},
        }

    async def resolve_identity(
        self,
        provider: IdentityProvider,
        token_or_key: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[Identity]:
        """
        Resolve an identity from a token or API key.

        Args:
            provider: Identity provider type
            token_or_key: JWT token or API key
            tenant_id: Optional tenant context

        Returns:
            Identity or None if resolution fails
        """
        try:
            if provider == IdentityProvider.CLERK:
                return await self._resolve_clerk_identity(token_or_key, tenant_id)
            elif provider == IdentityProvider.API_KEY:
                return await self._resolve_api_key_identity(token_or_key, tenant_id)
            elif provider == IdentityProvider.SYSTEM:
                return self._create_system_identity(token_or_key, tenant_id)
            else:
                logger.warning(f"Unsupported identity provider: {provider}")
                return None

        except Exception as e:
            logger.error(f"Identity resolution failed for {provider}: {e}")
            return None

    async def _resolve_clerk_identity(
        self,
        token: str,
        tenant_id: Optional[str],
    ) -> Optional[Identity]:
        """Resolve identity from Clerk JWT."""
        # This would integrate with Clerk's verification API
        # For now, provide a mock implementation
        import jwt

        try:
            # Decode without verification for demo (in production, verify with Clerk's public key)
            payload = jwt.decode(token, options={"verify_signature": False})

            identity = Identity(
                identity_id=payload.get("sub", ""),
                provider=IdentityProvider.CLERK,
                actor_type=ActorType.HUMAN,
                email=payload.get("email"),
                name=payload.get("name"),
                tenant_id=tenant_id or payload.get("org_id"),
                roles=set(payload.get("roles", ["viewer"])),
                provider_data=payload,
            )

            # Expand roles to permissions
            identity.permissions = self._expand_role_permissions(identity.roles)

            return identity

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid Clerk token: {e}")
            return None

    async def _resolve_api_key_identity(
        self,
        api_key: str,
        tenant_id: Optional[str],
    ) -> Optional[Identity]:
        """Resolve identity from API key."""
        # In production, this would look up the API key in the database
        # For now, create a machine identity with basic permissions

        identity = Identity(
            identity_id=f"apikey:{api_key[:8]}",
            provider=IdentityProvider.API_KEY,
            actor_type=ActorType.MACHINE,
            tenant_id=tenant_id,
            roles={"developer"},
        )

        identity.permissions = self._expand_role_permissions(identity.roles)
        return identity

    def _create_system_identity(
        self,
        system_id: str,
        tenant_id: Optional[str],
    ) -> Identity:
        """Create a system identity for internal services."""
        identity = Identity(
            identity_id=f"system:{system_id}",
            provider=IdentityProvider.SYSTEM,
            actor_type=ActorType.SYSTEM,
            tenant_id=tenant_id,
            roles={"system"},
        )

        identity.permissions = self._expand_role_permissions(identity.roles)
        return identity

    def _expand_role_permissions(self, roles: Set[str]) -> Set[str]:
        """Expand roles into their constituent permissions."""
        permissions: Set[str] = set()
        for role in roles:
            if role in self._role_permissions:
                permissions.update(self._role_permissions[role])
        return permissions

    async def check_access(
        self,
        identity: Identity,
        resource: str,
        action: str,
    ) -> AccessDecision:
        """
        Check if an identity can perform an action on a resource.

        Args:
            identity: The requesting identity
            resource: Resource being accessed (e.g., "runs", "agents")
            action: Action being performed (e.g., "read", "write", "delete")

        Returns:
            AccessDecision
        """
        required_permission = f"{action}:{resource}"
        wildcard_permission = f"{action}:*"

        # Check for exact permission or wildcard
        has_permission = (
            required_permission in identity.permissions or
            wildcard_permission in identity.permissions
        )

        decision = AccessDecision(
            allowed=has_permission,
            identity=identity,
            resource=resource,
            action=action,
            reason="permission_granted" if has_permission else "permission_denied",
            matched_rule=required_permission if has_permission else None,
            denied_permissions=[] if has_permission else [required_permission],
        )

        # Log the decision
        self._access_log.append(decision)
        if len(self._access_log) > 10000:
            self._access_log = self._access_log[-5000:]

        if not has_permission:
            logger.warning(
                f"Access denied: {identity.identity_id} tried {action} on {resource}"
            )

        return decision

    async def grant_role(
        self,
        identity_id: str,
        role: str,
        granted_by: str,
    ) -> bool:
        """
        Grant a role to an identity.

        In production, this would update the identity provider or local database.
        """
        logger.info(f"Role {role} granted to {identity_id} by {granted_by}")
        return True

    async def revoke_role(
        self,
        identity_id: str,
        role: str,
        revoked_by: str,
    ) -> bool:
        """
        Revoke a role from an identity.

        In production, this would update the identity provider or local database.
        """
        logger.info(f"Role {role} revoked from {identity_id} by {revoked_by}")
        return True

    def define_role(
        self,
        role_name: str,
        permissions: Set[str],
    ) -> None:
        """Define or update a role's permissions."""
        self._role_permissions[role_name] = permissions
        logger.info(f"Role {role_name} defined with {len(permissions)} permissions")

    def define_resource_permissions(
        self,
        resource: str,
        permissions: Set[str],
    ) -> None:
        """Define permissions for a resource."""
        self._resource_permissions[resource] = permissions

    def get_access_log(
        self,
        identity_id: Optional[str] = None,
        resource: Optional[str] = None,
        limit: int = 100,
    ) -> List[AccessDecision]:
        """Get access decision log for auditing."""
        log = self._access_log

        if identity_id:
            log = [d for d in log if d.identity.identity_id == identity_id]
        if resource:
            log = [d for d in log if d.resource == resource]

        return log[-limit:]

    def list_roles(self) -> Dict[str, Set[str]]:
        """List all defined roles and their permissions."""
        return dict(self._role_permissions)

    def list_resources(self) -> Dict[str, Set[str]]:
        """List all resources and their required permissions."""
        return dict(self._resource_permissions)
