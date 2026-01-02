# RBAC Authority Separation Design

**Status:** PROPOSED
**Created:** 2026-01-02
**Category:** Architecture / Security
**Reference:** PIN-271 (pending)

---

## Problem Statement

The current RBAC implementation conflates three orthogonal concerns:

1. **Identity Provider** (Clerk) - Who is this?
2. **Authorization Semantics** (roles, permissions) - What can they do?
3. **Execution Context** (local dev, CI, production) - Where are we running?

This causes:
- Stubs that fake Clerk tokens instead of being real actors
- JWT claim inspection scattered across the codebase
- No way to distinguish actor classes (customer vs internal product)
- CI tests that skip RBAC instead of testing real authorization

---

## Proposed Architecture

### Core Principle

> **RBAC must be provider-agnostic and environment-aware, but semantics must be identical everywhere.**

- Clerk is **identity**
- AOS owns **authorization**
- Environment decides **token source**, not rules

---

## Component Design

### 1. ActorContext (L6 - Platform Substrate)

The canonical actor model consumed by all downstream systems.

```python
# backend/app/auth/actor.py

from dataclasses import dataclass
from typing import Literal, Optional, FrozenSet
from enum import Enum


class ActorType(str, Enum):
    """Classification of actors for policy enforcement."""
    EXTERNAL_PAID = "external_paid"      # Paying customers
    EXTERNAL_TRIAL = "external_trial"    # Beta, trial users
    INTERNAL_PRODUCT = "internal_product" # Xuniverz, AI Console, M12 agents
    OPERATOR = "operator"                # Founders, ops team
    SYSTEM = "system"                    # CI, workers, replay


class IdentitySource(str, Enum):
    """How the identity was established."""
    CLERK = "clerk"           # Production Clerk JWT
    OIDC = "oidc"            # Keycloak/generic OIDC
    INTERNAL = "internal"     # Internal service-to-service
    SYSTEM = "system"         # CI, workers, automation
    DEV = "dev"              # Local development


@dataclass(frozen=True)
class ActorContext:
    """
    Immutable, canonical representation of an authenticated actor.

    All authorization decisions consume this model.
    No endpoint, worker, or service inspects raw JWTs ever again.

    Layer: L6 (Platform Substrate)
    """

    # Identity
    actor_id: str                         # Unique identifier
    actor_type: ActorType                 # Classification for policy
    source: IdentitySource                # How identity was established

    # Enterprise hierarchy (None for operators/system)
    tenant_id: Optional[str]              # Logical isolation boundary
    account_id: Optional[str]             # Enterprise account (parent)
    team_id: Optional[str]                # Sub-team within account

    # Authorization grants
    roles: FrozenSet[str]                 # e.g., {"admin", "dev"}
    permissions: FrozenSet[str]           # e.g., {"read:runs", "write:agents"}

    # Metadata (non-authoritative)
    email: Optional[str] = None
    display_name: Optional[str] = None

    def has_role(self, role: str) -> bool:
        """Check if actor has a specific role."""
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """Check if actor has a specific permission or wildcard."""
        if "*" in self.permissions:
            return True
        if permission in self.permissions:
            return True
        # Check wildcard patterns: "read:*" matches "read:runs"
        resource_action = permission.split(":")
        if len(resource_action) == 2:
            wildcard = f"{resource_action[0]}:*"
            return wildcard in self.permissions
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

    def same_account(self, other: "ActorContext") -> bool:
        """Check if two actors belong to the same account."""
        if self.account_id is None or other.account_id is None:
            return False
        return self.account_id == other.account_id

    def same_team(self, other: "ActorContext") -> bool:
        """Check if two actors belong to the same team."""
        if self.team_id is None or other.team_id is None:
            return False
        return self.team_id == other.team_id


# Predefined system actors
SYSTEM_ACTORS = {
    "ci": ActorContext(
        actor_id="system:ci",
        actor_type=ActorType.SYSTEM,
        source=IdentitySource.SYSTEM,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"ci", "automation"}),
        permissions=frozenset({"read:*", "write:metrics", "write:traces"}),
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
    ),
    "replay": ActorContext(
        actor_id="system:replay",
        actor_type=ActorType.SYSTEM,
        source=IdentitySource.SYSTEM,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"replay", "readonly"}),
        permissions=frozenset({"read:*"}),
    ),
}
```

---

### 2. IdentityAdapter Protocol (L3 - Boundary Adapter)

Common interface for all identity providers.

```python
# backend/app/auth/identity_adapter.py

from abc import ABC, abstractmethod
from typing import Optional
from fastapi import Request

from app.auth.actor import ActorContext


class IdentityAdapter(ABC):
    """
    Abstract base for identity adapters.

    Identity adapters:
    - Extract identity from requests (tokens, headers, etc.)
    - Validate tokens cryptographically
    - Return ActorContext

    Identity adapters do NOT:
    - Contain permission logic
    - Make authorization decisions
    - Modify roles based on context

    Layer: L3 (Boundary Adapter)
    """

    @abstractmethod
    async def extract_actor(self, request: Request) -> Optional[ActorContext]:
        """
        Extract actor identity from request.

        Returns None if no valid identity found.
        Raises AuthenticationError if token is invalid/expired.
        """
        pass

    @abstractmethod
    def get_source(self) -> str:
        """Return the identity source name for this adapter."""
        pass


class ClerkAdapter(IdentityAdapter):
    """
    Clerk identity adapter.

    Converts Clerk JWT → ActorContext
    No permission logic inside adapter.
    """

    def get_source(self) -> str:
        return "clerk"

    async def extract_actor(self, request: Request) -> Optional[ActorContext]:
        # 1. Get token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1]

        # 2. Validate with Clerk JWKS
        claims = await self._verify_token(token)
        if not claims:
            return None

        # 3. Extract identity (NOT authorization)
        user_id = claims.get("sub")
        org_id = claims.get("org_id")

        # 4. Fetch roles from Clerk metadata
        roles = await self._fetch_user_roles(user_id)

        # 5. Classify actor type based on org metadata
        actor_type = self._classify_actor(claims, roles)

        # 6. Build permissions from roles (delegated to AuthorizationEngine)
        # Note: We pass raw roles, engine computes permissions

        return ActorContext(
            actor_id=user_id,
            actor_type=actor_type,
            source=IdentitySource.CLERK,
            tenant_id=org_id,
            roles=frozenset(roles),
            permissions=frozenset(),  # Computed by AuthorizationEngine
            email=claims.get("email"),
            display_name=claims.get("name"),
        )


class SystemIdentityAdapter(IdentityAdapter):
    """
    System identity adapter for CI, workers, internal services.

    Used by:
    - CI pipelines (X-Machine-Token header)
    - Background workers
    - Replay system
    - Internal service-to-service calls
    """

    def get_source(self) -> str:
        return "system"

    async def extract_actor(self, request: Request) -> Optional[ActorContext]:
        # 1. Check for machine token
        machine_token = (
            request.headers.get("X-Machine-Token") or
            request.headers.get("Authorization-Machine")
        )

        if not machine_token:
            return None

        # 2. Validate machine token
        if not self._validate_machine_token(machine_token):
            return None

        # 3. Determine which system actor
        actor_name = self._get_actor_name(machine_token)

        # 4. Return predefined system actor
        return SYSTEM_ACTORS.get(actor_name)


class DevIdentityAdapter(IdentityAdapter):
    """
    Development identity adapter.

    Deterministic local identities for development.
    Configurable via environment.
    """

    def get_source(self) -> str:
        return "dev"

    async def extract_actor(self, request: Request) -> Optional[ActorContext]:
        # 1. Check for dev header (X-Dev-Actor)
        dev_actor = request.headers.get("X-Dev-Actor")
        if not dev_actor:
            return None

        # 2. Parse dev actor format: role:tenant
        # Example: admin:test_tenant, founder:, dev:my_org
        parts = dev_actor.split(":")
        role = parts[0]
        tenant_id = parts[1] if len(parts) > 1 and parts[1] else None

        # 3. Build actor context
        return ActorContext(
            actor_id=f"dev:{role}:{tenant_id or 'global'}",
            actor_type=ActorType.OPERATOR if role in ("founder", "operator") else ActorType.EXTERNAL_TRIAL,
            source=IdentitySource.DEV,
            tenant_id=tenant_id,
            roles=frozenset({role}),
            permissions=frozenset(),  # Computed by AuthorizationEngine
        )
```

---

### 3. AuthorizationEngine (L4 - Domain Engine)

Single source of truth for all authorization decisions.

```python
# backend/app/auth/authorization.py

from dataclasses import dataclass
from typing import Dict, List, Set, Optional
from enum import Enum

from app.auth.actor import ActorContext, ActorType


class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ABSTAIN = "abstain"  # No opinion, let next check decide


@dataclass(frozen=True)
class AuthorizationResult:
    """Result of an authorization check."""
    allowed: bool
    decision: Decision
    reason: str
    actor: ActorContext
    resource: str
    action: str

    def raise_if_denied(self) -> None:
        """Raise HTTPException if denied."""
        if not self.allowed:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403,
                detail=f"Denied: {self.reason}"
            )


class AuthorizationEngine:
    """
    Core authorization engine.

    Single source of truth for all authorization decisions.
    No JWT logic. No identity provider logic.
    Consumes ActorContext, evaluates against policy.

    Layer: L4 (Domain Engine)
    """

    # Role → Permissions mapping (from current RBAC_MATRIX)
    ROLE_PERMISSIONS: Dict[str, Set[str]] = {
        "founder": {"*"},
        "operator": {"read:*", "write:*", "delete:*"},
        "admin": {"read:*", "write:*", "delete:tenant"},
        "infra": {"read:*", "write:ops", "write:metrics"},
        "dev": {"read:*", "write:runs", "write:agents"},
        "readonly": {"read:*"},
        "machine": {"read:*", "write:runs", "write:traces"},
        "ci": {"read:*", "write:metrics"},
        "replay": {"read:*"},
    }

    # Actor type restrictions
    ACTOR_TYPE_ALLOWED_ACTIONS: Dict[ActorType, Set[str]] = {
        ActorType.EXTERNAL_PAID: {"read:*", "write:*"},
        ActorType.EXTERNAL_TRIAL: {"read:*", "write:runs"},
        ActorType.INTERNAL_PRODUCT: {"read:*", "write:*"},
        ActorType.OPERATOR: {"*"},
        ActorType.SYSTEM: {"read:*", "write:metrics", "write:traces"},
    }

    def __init__(self):
        self._policy_cache: Dict[str, Set[str]] = {}

    def compute_permissions(self, actor: ActorContext) -> ActorContext:
        """
        Compute effective permissions for an actor.

        Returns new ActorContext with permissions populated.
        """
        permissions: Set[str] = set()

        for role in actor.roles:
            role_perms = self.ROLE_PERMISSIONS.get(role, set())
            permissions.update(role_perms)

        return ActorContext(
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            source=actor.source,
            tenant_id=actor.tenant_id,
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
        """
        permission = f"{action}:{resource}"

        # 1. Check actor type restrictions
        allowed_actions = self.ACTOR_TYPE_ALLOWED_ACTIONS.get(actor.actor_type, set())
        if not self._matches_pattern(permission, allowed_actions):
            return AuthorizationResult(
                allowed=False,
                decision=Decision.DENY,
                reason=f"actor_type:{actor.actor_type.value} not allowed {permission}",
                actor=actor,
                resource=resource,
                action=action,
            )

        # 2. Check tenant isolation (if applicable)
        if tenant_id and actor.tenant_id and actor.tenant_id != tenant_id:
            return AuthorizationResult(
                allowed=False,
                decision=Decision.DENY,
                reason=f"tenant_isolation: actor tenant {actor.tenant_id} != {tenant_id}",
                actor=actor,
                resource=resource,
                action=action,
            )

        # 3. Check operator bypass (operators skip tenant checks)
        if actor.is_operator():
            return AuthorizationResult(
                allowed=True,
                decision=Decision.ALLOW,
                reason="operator_bypass",
                actor=actor,
                resource=resource,
                action=action,
            )

        # 4. Check permission grants
        if actor.has_permission(permission):
            return AuthorizationResult(
                allowed=True,
                decision=Decision.ALLOW,
                reason=f"permission:{permission}",
                actor=actor,
                resource=resource,
                action=action,
            )

        # 5. Deny by default
        return AuthorizationResult(
            allowed=False,
            decision=Decision.DENY,
            reason=f"no_permission:{permission}",
            actor=actor,
            resource=resource,
            action=action,
        )

    def _matches_pattern(self, permission: str, patterns: Set[str]) -> bool:
        """Check if permission matches any pattern (supports wildcards)."""
        if "*" in patterns:
            return True
        if permission in patterns:
            return True

        # Check wildcard patterns
        parts = permission.split(":")
        if len(parts) == 2:
            action, resource = parts
            if f"{action}:*" in patterns:
                return True
            if f"*:{resource}" in patterns:
                return True

        return False


# Singleton instance
_authorization_engine: Optional[AuthorizationEngine] = None


def get_authorization_engine() -> AuthorizationEngine:
    """Get the singleton authorization engine."""
    global _authorization_engine
    if _authorization_engine is None:
        _authorization_engine = AuthorizationEngine()
    return _authorization_engine
```

---

### 4. Identity Chain (L6 - Platform Integration)

Unified identity extraction that tries adapters in order.

```python
# backend/app/auth/identity_chain.py

from typing import List, Optional
from fastapi import Request

from app.auth.actor import ActorContext
from app.auth.identity_adapter import IdentityAdapter
from app.auth.authorization import get_authorization_engine


class IdentityChain:
    """
    Chain of identity adapters tried in order.

    Environment decides which adapters are active.
    All produce ActorContext → same authorization path.

    Layer: L6 (Platform Substrate)
    """

    def __init__(self, adapters: List[IdentityAdapter]):
        self.adapters = adapters
        self.engine = get_authorization_engine()

    async def extract_actor(self, request: Request) -> Optional[ActorContext]:
        """
        Extract actor from request using first matching adapter.

        Returns ActorContext with permissions computed.
        Returns None if no adapter can extract identity.
        """
        for adapter in self.adapters:
            try:
                actor = await adapter.extract_actor(request)
                if actor:
                    # Compute permissions from roles
                    return self.engine.compute_permissions(actor)
            except Exception as e:
                # Log and try next adapter
                continue

        return None


# Environment-based configuration
def create_identity_chain() -> IdentityChain:
    """Create identity chain based on environment."""
    import os

    adapters = []

    # System adapter always first (machine tokens)
    from app.auth.identity_adapter import SystemIdentityAdapter
    adapters.append(SystemIdentityAdapter())

    # Clerk in production
    if os.environ.get("CLERK_ENABLED", "").lower() == "true":
        from app.auth.identity_adapter import ClerkAdapter
        adapters.append(ClerkAdapter())

    # Dev adapter in development
    if os.environ.get("DEV_AUTH_ENABLED", "").lower() == "true":
        from app.auth.identity_adapter import DevIdentityAdapter
        adapters.append(DevIdentityAdapter())

    return IdentityChain(adapters)
```

---

## Migration Path

### Phase 1: Create Core Components (No Breaking Changes)

1. Create `app/auth/actor.py` with ActorContext
2. Create `app/auth/authorization.py` with AuthorizationEngine
3. Create `app/auth/identity_adapter.py` with protocol + adapters
4. Add tests for new components

### Phase 2: Parallel Path (Shadow Mode)

1. Add identity chain alongside existing middleware
2. Log comparison: old decision vs new decision
3. Validate 100% alignment before switching

### Phase 3: Switch Over

1. Replace `extract_roles_from_request()` with identity chain
2. Replace RBAC_MATRIX checks with AuthorizationEngine
3. Remove stub token format (use SystemIdentityAdapter)
4. Update all tests to use new API

### Phase 4: Cleanup

1. Remove legacy token parsing code
2. Remove stub.py (replaced by SystemIdentityAdapter)
3. Update documentation

---

## CI Invariants (Enforcement)

After migration, these rules are mechanically enforced:

```yaml
# .github/workflows/rbac-invariants.yml

rules:
  - id: RBAC-001
    name: No JWT logic outside adapters
    pattern: "jwt\\.|decode.*token|verify.*token"
    allowed_in:
      - app/auth/identity_adapter.py
      - app/auth/clerk_provider.py

  - id: RBAC-002
    name: No direct claim access
    pattern: "claims\\[|payload\\[|token_data\\["
    allowed_in:
      - app/auth/identity_adapter.py

  - id: RBAC-003
    name: All auth checks use ActorContext
    pattern: "def authorize|def check_permission"
    required_param: "actor: ActorContext"

  - id: RBAC-004
    name: No X-Roles header in production
    pattern: 'headers\\.get\\(["\']X-Roles'
    allowed_in:
      - tests/
```

---

## INFRA_REGISTRY Update

```yaml
# After migration

authorization:
  name: AuthorizationEngine
  state: C  # Production - no external dependency
  owner: core

clerk:
  name: Clerk Identity Provider
  state: C  # Production for customer auth
  owner: auth

system_identity:
  name: System Identity Provider
  state: C  # Production - no external dependency
  owner: core

dev_identity:
  name: Dev Identity Provider
  state: B  # Local only
  owner: dev
```

---

## Success Criteria

After implementation:

- [ ] All authorization decisions go through AuthorizationEngine
- [ ] No JWT parsing outside identity adapters
- [ ] CI uses SystemIdentityAdapter (real actor, not fake token)
- [ ] Same authorization rules in all environments
- [ ] Actor types explicitly classified
- [ ] 100% test coverage on authorization engine
- [ ] Shadow audit shows 0 divergence before switchover
