# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Identity resolution from various providers
# Callers: IAMService, Auth middleware
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: GAP-173 (IAM Integration)

"""
Identity Resolver (GAP-173)

Resolves identities from various sources:
- JWT tokens (Clerk, Auth0)
- API keys
- System tokens
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from .iam_service import ActorType, Identity, IdentityProvider

logger = logging.getLogger(__name__)


class IdentityResolver(ABC):
    """Abstract identity resolver."""

    @abstractmethod
    async def resolve(
        self,
        credential: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[Identity]:
        """Resolve an identity from a credential."""
        pass

    @property
    @abstractmethod
    def provider(self) -> IdentityProvider:
        """Get the provider type."""
        pass


class ClerkIdentityResolver(IdentityResolver):
    """Resolver for Clerk JWT tokens."""

    def __init__(self, clerk_secret_key: Optional[str] = None):
        import os
        self._secret_key = clerk_secret_key or os.getenv("CLERK_SECRET_KEY")

    @property
    def provider(self) -> IdentityProvider:
        return IdentityProvider.CLERK

    async def resolve(
        self,
        credential: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[Identity]:
        """Resolve identity from Clerk JWT."""
        import jwt

        try:
            # In production, verify with Clerk's public key
            payload = jwt.decode(credential, options={"verify_signature": False})

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

            return identity

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid Clerk token: {e}")
            return None


class APIKeyIdentityResolver(IdentityResolver):
    """Resolver for API keys."""

    @property
    def provider(self) -> IdentityProvider:
        return IdentityProvider.API_KEY

    async def resolve(
        self,
        credential: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[Identity]:
        """Resolve identity from API key."""
        # In production, look up API key in database
        # For now, create a machine identity

        if not credential or len(credential) < 8:
            return None

        return Identity(
            identity_id=f"apikey:{credential[:8]}",
            provider=IdentityProvider.API_KEY,
            actor_type=ActorType.MACHINE,
            tenant_id=tenant_id,
            roles={"developer"},
        )


class SystemIdentityResolver(IdentityResolver):
    """Resolver for internal system identities."""

    @property
    def provider(self) -> IdentityProvider:
        return IdentityProvider.SYSTEM

    async def resolve(
        self,
        credential: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[Identity]:
        """Create a system identity."""
        return Identity(
            identity_id=f"system:{credential}",
            provider=IdentityProvider.SYSTEM,
            actor_type=ActorType.SYSTEM,
            tenant_id=tenant_id,
            roles={"system"},
        )


@dataclass
class IdentityChain:
    """
    Chain of identity resolvers.

    Tries each resolver in order until one succeeds.
    """

    resolvers: list[IdentityResolver]

    async def resolve(
        self,
        credential: str,
        provider_hint: Optional[IdentityProvider] = None,
        tenant_id: Optional[str] = None,
    ) -> Optional[Identity]:
        """
        Resolve identity using the resolver chain.

        Args:
            credential: Token or API key
            provider_hint: Optional hint about which provider to use
            tenant_id: Optional tenant context

        Returns:
            Identity or None
        """
        # If provider hint given, try that resolver first
        if provider_hint:
            for resolver in self.resolvers:
                if resolver.provider == provider_hint:
                    identity = await resolver.resolve(credential, tenant_id)
                    if identity:
                        return identity

        # Try all resolvers in order
        for resolver in self.resolvers:
            try:
                identity = await resolver.resolve(credential, tenant_id)
                if identity:
                    return identity
            except Exception as e:
                logger.debug(f"Resolver {resolver.provider} failed: {e}")
                continue

        return None


def create_default_identity_chain() -> IdentityChain:
    """Create the default identity resolver chain."""
    return IdentityChain(
        resolvers=[
            ClerkIdentityResolver(),
            APIKeyIdentityResolver(),
            SystemIdentityResolver(),
        ]
    )
