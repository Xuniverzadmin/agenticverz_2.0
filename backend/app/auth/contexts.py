# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Gateway authentication context models for human and machine flows
# Callers: AuthGateway, gateway_middleware
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-306 (Capability Registry), CAP-006 (Authentication)
# capability_id: CAP-006

"""
Gateway Authentication Contexts

This module defines the context models produced by the Auth Gateway.
These are GATEWAY-level contexts, distinct from RBAC-level contexts.

Two flows, two context types:
1. Human Flow (JWT) → HumanAuthContext
2. Machine Flow (API Key) → MachineCapabilityContext

INVARIANTS:
- HumanAuthContext has NO permissions (RBAC decides later)
- MachineCapabilityContext has scopes only (NO RBAC, NO role lookup)
- These contexts are immutable after creation
- Downstream code consumes context, never raw headers
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import FrozenSet, Optional


class AuthSource(str, Enum):
    """How authentication was established.

    Only two valid auth sources exist:
    - CLERK: Humans authenticate via Clerk RS256 JWT
    - API_KEY: Machines authenticate via API key

    Reference: AUTH_DESIGN.md (AUTH-HUMAN-001, AUTH-MACHINE-001)
    """

    CLERK = "clerk"  # Production Clerk RS256 JWT (ONLY human auth)
    API_KEY = "api_key"  # Machine API key


class AuthPlane(str, Enum):
    """
    Which authentication plane the request uses.

    MACHINE: API Key authentication (agents, integrations, workers)
    HUMAN: JWT authentication (console users)
    """

    MACHINE = "machine"
    HUMAN = "human"


@dataclass(frozen=True)
class HumanAuthContext:
    """
    Context for human (JWT) authentication flow.

    Created by the gateway when a valid JWT is presented.
    Contains identity information ONLY - no permissions.
    Permissions are computed by RBAC layer downstream.

    INVARIANTS:
    - This context has NO permissions field (RBAC decides)
    - session_id is always present (for revocation checks)
    - auth_source indicates how identity was established
    """

    # Identity
    actor_id: str  # User ID from JWT (e.g., "user_xxx")
    session_id: str  # Session ID for revocation checks
    auth_source: AuthSource  # How identity was established

    # Tenant context (may be None for founders)
    tenant_id: Optional[str]
    account_id: Optional[str]

    # Metadata (non-authoritative, for display/audit)
    email: Optional[str] = None
    display_name: Optional[str] = None

    # Timestamp
    authenticated_at: datetime = None  # type: ignore

    def __post_init__(self):
        """Set authenticated_at if not provided."""
        if self.authenticated_at is None:
            object.__setattr__(self, "authenticated_at", datetime.utcnow())

    @property
    def plane(self) -> AuthPlane:
        """Return the auth plane for this context."""
        return AuthPlane.HUMAN

    def __repr__(self) -> str:
        return f"HumanAuthContext(actor={self.actor_id}, session={self.session_id[:8]}..., tenant={self.tenant_id})"


@dataclass(frozen=True)
class MachineCapabilityContext:
    """
    Context for machine (API Key) authentication flow.

    Created by the gateway when a valid API key is presented.
    Contains capability scopes ONLY - no RBAC, no role lookup.

    INVARIANTS:
    - Scopes define what the key can do (not RBAC roles)
    - rate_limit defines requests per minute
    - No role lookup, no permission expansion
    """

    # Identity
    key_id: str  # API key identifier (fingerprint)
    key_name: Optional[str]  # Human-readable key name
    auth_source: AuthSource  # Always API_KEY

    # Tenant context
    tenant_id: str  # All API keys are tenant-scoped

    # Capabilities
    scopes: FrozenSet[str]  # What this key can do (e.g., {"runs:write", "agents:read"})
    rate_limit: int  # Requests per minute

    # Timestamp
    authenticated_at: datetime = None  # type: ignore

    def __post_init__(self):
        """Set authenticated_at if not provided."""
        if self.authenticated_at is None:
            object.__setattr__(self, "authenticated_at", datetime.utcnow())

    @property
    def plane(self) -> AuthPlane:
        """Return the auth plane for this context."""
        return AuthPlane.MACHINE

    def has_scope(self, scope: str) -> bool:
        """
        Check if this key has a specific scope.

        Supports:
        - Exact match: "runs:write"
        - Wildcard: "*"
        - Prefix wildcard: "runs:*"
        """
        if "*" in self.scopes:
            return True
        if scope in self.scopes:
            return True

        # Check prefix wildcard (e.g., "runs:*" matches "runs:write")
        parts = scope.split(":")
        if len(parts) >= 2:
            resource = parts[0]
            wildcard = f"{resource}:*"
            if wildcard in self.scopes:
                return True

        return False

    def __repr__(self) -> str:
        return f"MachineCapabilityContext(key={self.key_id[:8]}..., tenant={self.tenant_id}, scopes={set(self.scopes)})"


@dataclass(frozen=True)
class FounderAuthContext:
    """
    Context for founder (FOPS) authentication flow.

    Created by the gateway when a valid FOPS token is presented.
    Founders operate at control-plane level, outside tenant context.

    INVARIANTS:
    - No tenant_id (founders are not tenant-scoped)
    - No roles (type is authority)
    - No scopes (not capability-based)
    - No permissions (not RBAC-controlled)
    - reason is always required (audit trail)

    Reference: PIN-398 (Founder Auth Architecture)
    """

    # Identity
    actor_id: str  # Founder identifier from token sub claim
    reason: str  # Required reason for FOPS access (audit)
    issued_at: datetime  # Token issue time

    @property
    def plane(self) -> AuthPlane:
        """Return the auth plane for this context."""
        return AuthPlane.HUMAN  # Founders are humans, but control-plane

    def __repr__(self) -> str:
        return f"FounderAuthContext(actor={self.actor_id}, reason={self.reason})"


# Type alias for gateway result context
GatewayContext = HumanAuthContext | MachineCapabilityContext | FounderAuthContext
