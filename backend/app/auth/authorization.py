# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api | worker | internal
#   Execution: sync
# Role: Single source of truth for all authorization decisions
# Callers: API middleware, services, workers
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-271 (RBAC Authority Separation), PERMISSION_TAXONOMY_V1.md

"""
AuthorizationEngine: The single source of truth for authorization.

All authorization decisions flow through this engine.
No JWT logic. No identity provider logic. No HTTP logic.
Consumes ActorContext, evaluates against policy.

Invariants:
- Input is ONLY ActorContext (from actor.py)
- No framework imports (FastAPI, etc.)
- No identity parsing
- Same rules in all environments (prod, CI, dev)

Usage:
    from app.auth.authorization import get_authorization_engine, authorize

    engine = get_authorization_engine()
    result = engine.authorize(actor, "runs", "write")

    if not result.allowed:
        raise HTTPException(403, result.reason)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Set

from app.auth.actor import ActorContext, ActorType

logger = logging.getLogger("nova.auth.authorization")


class Decision(str, Enum):
    """Authorization decision types."""

    ALLOW = "allow"
    DENY = "deny"
    ABSTAIN = "abstain"  # No opinion, let next check decide


@dataclass(frozen=True)
class AuthorizationResult:
    """
    Result of an authorization check.

    Immutable and includes full context for audit/debugging.
    """

    allowed: bool
    decision: Decision
    reason: str
    actor: ActorContext
    resource: str
    action: str

    def raise_if_denied(self) -> None:
        """
        Raise HTTPException if denied.

        This is the ONLY place where HTTP logic appears,
        and it's opt-in by the caller.
        """
        if not self.allowed:
            # Import here to keep module HTTP-free by default
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail=f"Denied: {self.reason}")

    def __repr__(self) -> str:
        status = "ALLOWED" if self.allowed else "DENIED"
        return f"AuthResult({status}: {self.action}:{self.resource} for {self.actor.actor_id})"


class AuthorizationEngine:
    """
    Core authorization engine.

    Single source of truth for all authorization decisions.
    No JWT logic. No identity provider logic.
    Consumes ActorContext, evaluates against policy.

    Evaluation Order:
    1. Check ActorType restrictions (what this type of actor can ever do)
    2. Check tenant isolation (actors can't access other tenants)
    3. Check operator bypass (operators skip tenant checks)
    4. Check permission grants (from roles)
    5. Deny by default

    Layer: L4 (Domain Engine)
    """

    # =========================================================================
    # Role → Permissions mapping (from PERMISSION_TAXONOMY_V1.md)
    # =========================================================================
    ROLE_PERMISSIONS: Dict[str, Set[str]] = {
        # Operator roles
        "founder": {"*"},
        "operator": {"read:*", "write:*", "delete:*", "admin:*"},
        # Enterprise roles
        "admin": {
            "read:*",
            "write:*",
            "delete:*",
            "admin:account",
            "admin:team",
            "admin:members",
            "read:billing:account",
            "write:billing:account",
        },
        "team_admin": {
            "read:*",
            "write:*",
            "admin:team",
            "admin:members:team",
        },
        "developer": {
            "read:*",
            "write:runs",
            "write:agents",
            "write:skills",
            "execute:*",
        },
        "viewer": {
            "read:*",
            "audit:*",
        },
        # System roles
        "machine": {
            "read:*",
            "write:runs",
            "write:traces",
            "write:metrics",
            "execute:*",
        },
        "ci": {
            "read:*",
            "write:metrics",
            "write:traces",
        },
        "replay": {
            "read:*",
            "execute:replay",
        },
        "automation": {
            "read:*",
            "write:metrics",
        },
        "worker": {
            "read:*",
            "write:runs",
            "write:traces",
        },
        # Internal product roles
        "internal": {
            "read:*",
            "write:runs",
            "write:agents",
            "execute:*",
        },
        "product": {
            "read:*",
            "write:*",
        },
        # Legacy role names (for migration compatibility)
        "readonly": {"read:*"},
        "infra": {"read:*", "write:ops", "write:metrics"},
        "dev": {"read:*", "write:runs", "write:agents"},
    }

    # =========================================================================
    # ActorType restrictions (what each type can EVER do)
    # =========================================================================
    ACTOR_TYPE_ALLOWED: Dict[ActorType, Set[str]] = {
        ActorType.EXTERNAL_PAID: {
            "read:*",
            "write:*",
            "delete:*",
            "admin:team",
            "admin:members:team",
            "read:billing:account",
        },
        ActorType.EXTERNAL_TRIAL: {
            "read:*",
            "write:runs",
            "write:agents",
            "execute:*",
        },
        ActorType.INTERNAL_PRODUCT: {
            "read:*",
            "write:*",
            "execute:*",
            "audit:*",
        },
        ActorType.OPERATOR: {"*"},  # Everything
        ActorType.SYSTEM: {
            "read:*",
            "write:runs",
            "write:traces",
            "write:metrics",
            "execute:*",
        },
    }

    # =========================================================================
    # ActorType forbidden actions (explicit denies)
    # =========================================================================
    ACTOR_TYPE_FORBIDDEN: Dict[ActorType, Set[str]] = {
        ActorType.EXTERNAL_PAID: {
            "admin:system",
            "delete:system",
            "read:system",  # No cross-tenant
        },
        ActorType.EXTERNAL_TRIAL: {
            "write:policies",
            "delete:*",
            "admin:*",
            "billing:*",
            "read:system",
        },
        ActorType.INTERNAL_PRODUCT: {
            "delete:system",
            "admin:account",
            "admin:billing",
        },
        ActorType.OPERATOR: set(),  # No restrictions
        ActorType.SYSTEM: {
            "delete:*",
            "admin:*",
            "write:policies",
            "write:billing",
        },
    }

    def __init__(self) -> None:
        self._policy_cache: Dict[str, Set[str]] = {}

    def compute_permissions(self, actor: ActorContext) -> ActorContext:
        """
        Compute effective permissions for an actor based on their roles.

        Returns a new ActorContext with permissions populated.
        This is called by IdentityChain after extracting identity.
        """
        permissions: Set[str] = set()

        for role in actor.roles:
            role_perms = self.ROLE_PERMISSIONS.get(role, set())
            permissions.update(role_perms)

        # Return new ActorContext with computed permissions
        return ActorContext(
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            source=actor.source,
            tenant_id=actor.tenant_id,
            account_id=actor.account_id,
            team_id=actor.team_id,
            roles=actor.roles,
            permissions=frozenset(permissions),
            email=actor.email,
            display_name=actor.display_name,
        )

    def authorize(
        self,
        actor: ActorContext,
        resource: str,
        action: str,
        tenant_id: Optional[str] = None,
    ) -> AuthorizationResult:
        """
        Evaluate authorization for an action.

        Args:
            actor: The actor requesting access
            resource: Resource being accessed (e.g., "runs", "agents")
            action: Action being performed (e.g., "read", "write", "delete")
            tenant_id: Tenant context for the action (if applicable)

        Returns:
            AuthorizationResult with decision and reason

        Evaluation Order:
        1. Check explicit denies (ActorType forbidden)
        2. Check ActorType restrictions (what this type can ever do)
        3. Check tenant isolation
        4. Check operator bypass
        5. Check permission grants
        6. Deny by default
        """
        permission = f"{action}:{resource}"

        # 1. Check explicit denies
        forbidden = self.ACTOR_TYPE_FORBIDDEN.get(actor.actor_type, set())
        if self._matches_pattern(permission, forbidden):
            return AuthorizationResult(
                allowed=False,
                decision=Decision.DENY,
                reason=f"forbidden:{actor.actor_type.value}:{permission}",
                actor=actor,
                resource=resource,
                action=action,
            )

        # 2. Check ActorType restrictions
        allowed_patterns = self.ACTOR_TYPE_ALLOWED.get(actor.actor_type, set())
        if not self._matches_pattern(permission, allowed_patterns):
            return AuthorizationResult(
                allowed=False,
                decision=Decision.DENY,
                reason=f"actor_type:{actor.actor_type.value} cannot {permission}",
                actor=actor,
                resource=resource,
                action=action,
            )

        # 3. Check tenant isolation (if tenant context provided)
        if tenant_id and actor.tenant_id and actor.tenant_id != tenant_id:
            # Operators bypass tenant isolation
            if not actor.is_operator():
                return AuthorizationResult(
                    allowed=False,
                    decision=Decision.DENY,
                    reason=f"tenant_isolation: {actor.tenant_id} != {tenant_id}",
                    actor=actor,
                    resource=resource,
                    action=action,
                )

        # 4. Check operator bypass
        if actor.is_operator():
            return AuthorizationResult(
                allowed=True,
                decision=Decision.ALLOW,
                reason="operator_bypass",
                actor=actor,
                resource=resource,
                action=action,
            )

        # 5. Check permission grants
        if actor.has_permission(permission):
            return AuthorizationResult(
                allowed=True,
                decision=Decision.ALLOW,
                reason=f"permission:{permission}",
                actor=actor,
                resource=resource,
                action=action,
            )

        # 6. Deny by default
        return AuthorizationResult(
            allowed=False,
            decision=Decision.DENY,
            reason=f"no_permission:{permission}",
            actor=actor,
            resource=resource,
            action=action,
        )

    def _matches_pattern(self, permission: str, patterns: Set[str]) -> bool:
        """
        Check if permission matches any pattern (supports wildcards).

        Patterns:
        - "*" matches everything
        - "read:*" matches "read:runs", "read:agents", etc.
        - "read:runs" matches exactly "read:runs"
        """
        if "*" in patterns:
            return True
        if permission in patterns:
            return True

        # Check wildcard patterns
        parts = permission.split(":")
        if len(parts) >= 2:
            action = parts[0]
            resource = parts[1]

            # Action wildcard: "read:*" matches "read:runs"
            if f"{action}:*" in patterns:
                return True

            # Resource wildcard: "*:runs" matches "read:runs"
            if f"*:{resource}" in patterns:
                return True

        return False

    def can_access_resource(
        self,
        actor: ActorContext,
        resource: str,
        action: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Convenience method: returns True if authorized, False otherwise.

        Use authorize() when you need the full AuthorizationResult.
        """
        result = self.authorize(actor, resource, action, tenant_id)
        return result.allowed


# =============================================================================
# Singleton Instance
# =============================================================================

_authorization_engine: Optional[AuthorizationEngine] = None


def get_authorization_engine() -> AuthorizationEngine:
    """Get the singleton authorization engine."""
    global _authorization_engine
    if _authorization_engine is None:
        _authorization_engine = AuthorizationEngine()
    return _authorization_engine


def authorize(
    actor: ActorContext,
    resource: str,
    action: str,
    tenant_id: Optional[str] = None,
) -> AuthorizationResult:
    """
    Convenience function for authorization checks.

    Equivalent to: get_authorization_engine().authorize(...)
    """
    return get_authorization_engine().authorize(actor, resource, action, tenant_id)
