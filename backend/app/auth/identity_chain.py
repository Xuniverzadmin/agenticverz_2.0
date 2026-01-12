# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified identity extraction via adapter chain
# Callers: API middleware
# Allowed Imports: L3, L4
# Forbidden Imports: L1, L2
# Reference: PIN-271 (RBAC Authority Separation)

"""
IdentityChain: Unified identity extraction.

Tries identity adapters in order until one succeeds.
Environment decides which adapters are active.
All adapters produce ActorContext → same authorization path.

Invariants:
- Adapter order matters (first match wins)
- System adapter always checked first (machine tokens)
- Clerk checked in production
- Dev adapter only in development
- Permissions computed after identity extraction

Usage:
    chain = create_identity_chain()
    actor = await chain.extract_actor(request)

    if actor is None:
        raise HTTPException(401, "No valid identity")

Layer: L6 (Platform Substrate)
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

from fastapi import Request

from app.auth.actor import ActorContext
from app.auth.authorization import get_authorization_engine
from app.auth.identity_adapter import (
    ClerkAdapter,
    DevIdentityAdapter,
    IdentityAdapter,
    SystemIdentityAdapter,
)

logger = logging.getLogger("nova.auth.identity_chain")


class IdentityChain:
    """
    Chain of identity adapters tried in order.

    Environment decides which adapters are active.
    All adapters produce ActorContext → same authorization path.

    Adapter Order (important):
    1. SystemIdentityAdapter - Machine tokens (CI, workers)
    2. ClerkAdapter - Production user auth (Clerk RS256 JWKS)
    3. DevIdentityAdapter - Local development

    Reference: AUTH_DESIGN.md (AUTH-HUMAN-001, AUTH-MACHINE-001)

    Layer: L6 (Platform Substrate)
    """

    def __init__(self, adapters: List[IdentityAdapter]) -> None:
        self.adapters = adapters
        self.engine = get_authorization_engine()
        self._adapter_names = [a.name for a in adapters]
        logger.info(f"IdentityChain initialized with adapters: {self._adapter_names}")

    async def extract_actor(self, request: Request) -> Optional[ActorContext]:
        """
        Extract actor from request using first matching adapter.

        Returns ActorContext with permissions computed.
        Returns None if no adapter can extract identity.
        """
        for adapter in self.adapters:
            try:
                actor = await adapter.extract_actor(request)
                if actor is not None:
                    logger.debug(f"Identity extracted by {adapter.name}: {actor.actor_id}")
                    # Compute permissions from roles
                    return self.engine.compute_permissions(actor)
            except Exception as e:
                logger.warning(
                    f"Adapter {adapter.name} failed: {e}",
                    exc_info=True,
                )
                # Continue to next adapter
                continue

        logger.debug("No adapter could extract identity")
        return None

    async def extract_actor_or_raise(self, request: Request) -> ActorContext:
        """
        Extract actor or raise HTTPException.

        Use this when authentication is required.
        """
        actor = await self.extract_actor(request)
        if actor is None:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=401,
                detail="Authentication required",
            )
        return actor

    def get_adapter_names(self) -> List[str]:
        """Return list of active adapter names (for debugging)."""
        return self._adapter_names


# =============================================================================
# Factory Functions
# =============================================================================


def create_identity_chain() -> IdentityChain:
    """
    Create identity chain based on environment.

    Adapter configuration:
    - SystemIdentityAdapter: Always active (machine tokens)
    - ClerkAdapter: Active if CLERK_SECRET_KEY is set
    - DevIdentityAdapter: Active if DEV_AUTH_ENABLED=true

    Reference: AUTH_DESIGN.md
    - AUTH-HUMAN-001: All human users authenticate via Clerk (RS256 JWKS)
    - AUTH-MACHINE-001: Machine clients authenticate via API Key
    """
    adapters: List[IdentityAdapter] = []

    # 1. System adapter always first (machine tokens)
    adapters.append(SystemIdentityAdapter())
    logger.debug("Added SystemIdentityAdapter")

    # 2. Clerk in production (human auth)
    clerk_key = os.getenv("CLERK_SECRET_KEY", "")
    if clerk_key:
        adapters.append(ClerkAdapter())
        logger.debug("Added ClerkAdapter (Clerk configured)")

    # 3. Dev adapter in development
    dev_enabled = os.getenv("DEV_AUTH_ENABLED", "").lower() == "true"
    if dev_enabled:
        adapters.append(DevIdentityAdapter())
        logger.debug("Added DevIdentityAdapter (dev mode enabled)")

    # StubIdentityAdapter DELETED - AUTH_DESIGN.md (AUTH-HUMAN-004)
    # Stub authentication does not exist.

    return IdentityChain(adapters)


# =============================================================================
# Singleton Instance
# =============================================================================

_identity_chain: Optional[IdentityChain] = None


def get_identity_chain() -> IdentityChain:
    """Get the singleton identity chain."""
    global _identity_chain
    if _identity_chain is None:
        _identity_chain = create_identity_chain()
    return _identity_chain


def reset_identity_chain() -> None:
    """Reset the singleton (for testing)."""
    global _identity_chain
    _identity_chain = None


# =============================================================================
# FastAPI Dependency
# =============================================================================


async def get_current_actor(request: Request) -> ActorContext:
    """
    FastAPI dependency for getting the current actor.

    Usage:
        @app.get("/resource")
        async def get_resource(actor: ActorContext = Depends(get_current_actor)):
            ...

    Raises:
        HTTPException 401 if no valid identity
    """
    chain = get_identity_chain()
    return await chain.extract_actor_or_raise(request)


async def get_current_actor_optional(request: Request) -> Optional[ActorContext]:
    """
    FastAPI dependency for optional authentication.

    Returns None if no valid identity (doesn't raise).

    Usage:
        @app.get("/public")
        async def get_public(actor: Optional[ActorContext] = Depends(get_current_actor_optional)):
            if actor:
                # Authenticated
            else:
                # Anonymous
    """
    chain = get_identity_chain()
    return await chain.extract_actor(request)
