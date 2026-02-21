# capability_id: CAP-012
# Layer: L5 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# AUDIENCE: INTERNAL
# Role: Extract identity from requests, produce ActorContext
# Callers: IdentityChain, API middleware
# Reference: PIN-271 (RBAC Authority Separation)

"""
Identity Adapters: Extract identity from requests.

Each adapter handles a specific identity source (Clerk, System, Dev).
All adapters produce ActorContext - the canonical actor model.

Invariants:
- Adapters do identity extraction ONLY
- No authorization logic inside adapters
- No permission computation inside adapters
- All produce ActorContext

Usage:
    adapter = ClerkAdapter()
    actor = await adapter.extract_actor(request)

    if actor is None:
        # No valid identity found
        pass
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from fastapi import Request

from app.auth.actor import (
    SYSTEM_ACTORS,
    ActorContext,
    ActorType,
    IdentitySource,
    create_operator_actor,
)

logger = logging.getLogger("nova.auth.identity")


class AuthenticationError(Exception):
    """Raised when authentication fails (invalid/expired token)."""

    pass


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
    - Compute permissions (that's AuthorizationEngine's job)

    Layer: L5 (Domain Engine)
    """

    @abstractmethod
    async def extract_actor(self, request: Request) -> Optional[ActorContext]:
        """
        Extract actor identity from request.

        Returns None if no valid identity found for this adapter.
        Raises AuthenticationError if token is invalid/expired.
        """
        pass

    @abstractmethod
    def get_source(self) -> IdentitySource:
        """Return the identity source for this adapter."""
        pass

    @property
    def name(self) -> str:
        """Adapter name for logging."""
        return self.__class__.__name__


class ClerkAdapter(IdentityAdapter):
    """
    Clerk identity adapter.

    Converts Clerk JWT → ActorContext.
    No permission logic inside adapter.

    Configuration:
    - CLERK_SECRET_KEY: Required for JWT verification
    - CLERK_JWKS_URL: JWKS endpoint for public keys

    Layer: L5 (Domain Engine)
    """

    def __init__(self) -> None:
        self.secret_key = os.getenv("CLERK_SECRET_KEY", "")
        self.jwks_url = os.getenv("CLERK_JWKS_URL", "")
        self._jwks_cache: Optional[Dict[str, Any]] = None

    def get_source(self) -> IdentitySource:
        return IdentitySource.CLERK

    async def extract_actor(self, request: Request) -> Optional[ActorContext]:
        """
        Extract actor from Clerk JWT.

        Returns None if no Authorization header.
        Raises AuthenticationError if token invalid.
        """
        # 1. Get token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1]

        # 2. Validate with Clerk
        claims = await self._verify_token(token)
        if not claims:
            return None

        # 3. Extract identity (NOT authorization)
        user_id = claims.get("sub", "")
        org_id = claims.get("org_id")
        org_role = claims.get("org_role", "")

        # 4. Determine actor type
        actor_type = self._classify_actor(claims)

        # 5. Extract roles from Clerk metadata
        roles = self._extract_roles(claims)

        # 6. Build ActorContext
        # Note: permissions are empty - computed by AuthorizationEngine
        return ActorContext(
            actor_id=user_id,
            actor_type=actor_type,
            source=IdentitySource.CLERK,
            tenant_id=org_id,
            account_id=org_id,  # In Clerk, org_id is the account
            team_id=claims.get("team_id"),  # Custom claim if set
            roles=frozenset(roles),
            permissions=frozenset(),  # Computed by AuthorizationEngine
            email=claims.get("email"),
            display_name=claims.get("name"),
        )

    async def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Clerk JWT and return claims.

        Returns None if token is invalid.
        """
        if not self.secret_key:
            logger.warning("Clerk not configured (no secret key)")
            return None

        try:
            # Import Clerk verification from existing provider
            from app.auth.clerk_provider import get_clerk_provider

            provider = get_clerk_provider()
            if provider is None or not provider.is_configured:
                logger.warning("Clerk provider not configured")
                return None

            # verify_token is SYNC, not async - returns JWT payload dict
            payload = provider.verify_token(token)

            # payload is the decoded JWT with claims like sub, email, etc.
            return {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "org_id": payload.get("org_id"),
                "org_role": payload.get("org_role"),
                "metadata": payload.get("metadata", {}),
            }
        except Exception as e:
            logger.warning(f"Clerk token verification failed: {e}")
            return None

    def _classify_actor(self, claims: Dict[str, Any]) -> ActorType:
        """
        Classify actor type based on Clerk claims.

        Uses org metadata or special markers to determine type.
        """
        metadata = claims.get("metadata", {})

        # Check for operator flag
        if metadata.get("is_operator") or metadata.get("is_founder"):
            return ActorType.OPERATOR

        # Check for internal product flag
        if metadata.get("is_internal_product"):
            return ActorType.INTERNAL_PRODUCT

        # Check for trial flag
        if metadata.get("is_trial"):
            return ActorType.EXTERNAL_TRIAL

        # Default to paid customer
        return ActorType.EXTERNAL_PAID

    def _extract_roles(self, claims: Dict[str, Any]) -> List[str]:
        """Extract roles from Clerk claims/metadata."""
        roles: List[str] = []

        # Org role from Clerk
        org_role = claims.get("org_role", "")
        if org_role:
            roles.append(org_role)

        # Custom roles from metadata
        metadata = claims.get("metadata", {})
        custom_roles = metadata.get("roles", [])
        if isinstance(custom_roles, list):
            roles.extend(custom_roles)

        return roles


class SystemIdentityAdapter(IdentityAdapter):
    """
    System identity adapter for CI, workers, internal services.

    Used by:
    - CI pipelines (X-Machine-Token header)
    - Background workers
    - Replay system
    - Internal service-to-service calls

    Configuration:
    - AOS_MACHINE_TOKEN: Shared secret for system actors

    Layer: L5 (Domain Engine)
    """

    def __init__(self) -> None:
        self.machine_token = os.getenv("AOS_MACHINE_TOKEN", "")
        self.aos_api_key = os.getenv("AOS_API_KEY", "")

    def get_source(self) -> IdentitySource:
        return IdentitySource.SYSTEM

    async def extract_actor(self, request: Request) -> Optional[ActorContext]:
        """
        Extract system actor from machine token.

        Checks headers in order:
        1. X-Machine-Token (preferred)
        2. X-AOS-Key (legacy, maps to worker)
        """
        # 1. Check for machine token
        machine_token = request.headers.get("X-Machine-Token", "")

        if machine_token:
            actor = self._validate_machine_token(machine_token)
            if actor:
                return actor

        # 2. Check for AOS API key (legacy support)
        aos_key = request.headers.get("X-AOS-Key", "")
        if aos_key and self.aos_api_key and aos_key == self.aos_api_key:
            # Legacy API key maps to worker actor
            return SYSTEM_ACTORS.get("worker")

        return None

    def _validate_machine_token(self, token: str) -> Optional[ActorContext]:
        """
        Validate machine token and return appropriate system actor.

        Token format: {actor_name}:{secret}
        Example: "ci:abc123", "worker:xyz789"
        """
        if not self.machine_token:
            return None

        # Parse token
        parts = token.split(":", 1)
        if len(parts) != 2:
            return None

        actor_name, secret = parts

        # Validate secret
        if secret != self.machine_token:
            return None

        # Return predefined system actor
        return SYSTEM_ACTORS.get(actor_name)


class DevIdentityAdapter(IdentityAdapter):
    """
    Development identity adapter.

    Provides deterministic local identities for development.
    Explicitly marked as DEV source - NOT fake Clerk.

    Configuration:
    - DEV_AUTH_ENABLED: Must be "true" to enable
    - DEV_DEFAULT_ROLE: Default role for dev actors

    Header format: X-Dev-Actor: {role}:{tenant_id}
    Examples:
    - X-Dev-Actor: admin:test_tenant
    - X-Dev-Actor: founder:
    - X-Dev-Actor: dev:my_org

    Layer: L5 (Domain Engine)
    """

    def __init__(self) -> None:
        self.enabled = os.getenv("DEV_AUTH_ENABLED", "").lower() == "true"
        self.default_role = os.getenv("DEV_DEFAULT_ROLE", "developer")

    def get_source(self) -> IdentitySource:
        return IdentitySource.DEV

    async def extract_actor(self, request: Request) -> Optional[ActorContext]:
        """
        Extract dev actor from X-Dev-Actor header.

        Only works if DEV_AUTH_ENABLED=true.
        """
        if not self.enabled:
            return None

        # Check for dev header
        dev_actor = request.headers.get("X-Dev-Actor", "")
        if not dev_actor:
            return None

        # Parse format: role:tenant
        parts = dev_actor.split(":", 1)
        role = parts[0] if parts else self.default_role
        tenant_id = parts[1] if len(parts) > 1 and parts[1] else None

        # Determine actor type
        if role in ("founder", "operator"):
            # Use create_operator_actor for standardized operator context
            return create_operator_actor(
                actor_id=f"dev:{role}:{tenant_id or 'global'}",
                email=f"dev-{role}@localhost",
                display_name=f"Dev {role.title()}",
            )
        elif role in ("internal", "product"):
            actor_type = ActorType.INTERNAL_PRODUCT
        elif role == "trial":
            actor_type = ActorType.EXTERNAL_TRIAL
        else:
            actor_type = ActorType.EXTERNAL_PAID

        # Build dev actor
        return ActorContext(
            actor_id=f"dev:{role}:{tenant_id or 'global'}",
            actor_type=actor_type,
            source=IdentitySource.DEV,
            tenant_id=tenant_id,
            account_id=tenant_id,  # Same as tenant for dev
            team_id=None,
            roles=frozenset({role}),
            permissions=frozenset(),  # Computed by AuthorizationEngine
            email=f"dev-{role}@localhost",
            display_name=f"Dev {role.title()}",
        )


# StubIdentityAdapter DELETED
# Reference: AUTH_DESIGN.md (AUTH-HUMAN-004)
# Stub authentication does not exist. Use SystemIdentityAdapter or DevIdentityAdapter.
