# Layer: L4 — Domain Engine
# Product: system-wide
# AUDIENCE: SHARED
# Temporal:
#   Trigger: api
#   Execution: async
# Role: HumanAuthProvider ABC, HumanPrincipal contract, and provider factory
# Callers: gateway.py (_authenticate_human)
# Allowed Imports: L4 (auth_constants, contexts)
# Forbidden Imports: L1, L2, L5, L6
# Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md

"""
Human Auth Provider Seam

Defines the HumanAuthProvider interface, the HumanPrincipal data contract,
and the provider factory that selects between Clerk and HOC Identity
based on the AUTH_PROVIDER environment variable.

INVARIANTS:
1. All human authentication flows go through a HumanAuthProvider.
2. The provider returns a HumanPrincipal; the gateway maps it to HumanAuthContext.
3. Provider selection is determined at startup via AUTH_PROVIDER env var.
4. Default provider is "clerk" (backward compatible).
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .auth_constants import AuthDenyReason, AuthProviderType

logger = logging.getLogger("nova.auth.auth_provider")


# =============================================================================
# HumanPrincipal — Provider-Neutral Identity Contract
# =============================================================================

@dataclass(frozen=True)
class HumanPrincipal:
    """
    Provider-neutral human identity returned by any HumanAuthProvider.

    The gateway maps this to the existing HumanAuthContext for downstream
    compatibility. Fields follow the V1 design lock.
    """

    subject_user_id: str                    # Internal user ID (JWT sub)
    email: Optional[str]                    # User email (optional)
    tenant_id: Optional[str]               # Active tenant binding (JWT tid / Clerk org_id)
    session_id: Optional[str]              # Session ID for revocation (JWT sid)
    roles_or_groups: tuple[str, ...]       # Role hints (not authoritative; RBAC decides)
    issued_at: datetime                     # Token iat
    expires_at: datetime                    # Token exp
    auth_provider: AuthProviderType         # Which provider verified this


# =============================================================================
# AuthProviderError — Uniform Error Contract
# =============================================================================

class AuthProviderError(Exception):
    """Raised when a HumanAuthProvider cannot verify a credential."""

    def __init__(self, reason: AuthDenyReason, message: str = ""):
        self.reason = reason
        self.message = message or reason.value
        super().__init__(self.message)


# =============================================================================
# HumanAuthProvider ABC
# =============================================================================

class HumanAuthProvider(ABC):
    """
    Abstract contract for human authentication providers.

    Implementations:
    - ClerkHumanAuthProvider: wraps current Clerk RS256 JWKS verification.
    - HocIdentityHumanAuthProvider: in-house EdDSA/JWKS verification (V1 target).
    """

    @abstractmethod
    async def verify_bearer_token(self, token: str) -> HumanPrincipal:
        """
        Verify a bearer token and return a HumanPrincipal.

        Args:
            token: Raw JWT string (already stripped of "Bearer " prefix).

        Returns:
            HumanPrincipal with verified identity claims.

        Raises:
            AuthProviderError with appropriate AuthDenyReason on failure.
        """
        ...

    @property
    @abstractmethod
    def provider_type(self) -> AuthProviderType:
        """Return the provider type identifier."""
        ...

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if the provider has all required configuration."""
        ...


# =============================================================================
# Provider Factory
# =============================================================================

# Env switch — default to Clerk for backward compatibility
AUTH_PROVIDER_ENV = os.getenv("AUTH_PROVIDER", "clerk").lower().strip()

# Singleton cache
_provider_instance: Optional[HumanAuthProvider] = None


def get_human_auth_provider() -> HumanAuthProvider:
    """
    Get the configured HumanAuthProvider singleton.

    Selection is driven by AUTH_PROVIDER env var:
    - "clerk" (default): ClerkHumanAuthProvider
    - "hoc_identity": HocIdentityHumanAuthProvider

    Returns:
        The configured HumanAuthProvider instance.
    """
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    if AUTH_PROVIDER_ENV == "hoc_identity":
        from .auth_provider_hoc_identity import HocIdentityHumanAuthProvider
        _provider_instance = HocIdentityHumanAuthProvider()
        logger.info("human_auth_provider_selected", extra={"provider": "hoc_identity"})
    else:
        from .auth_provider_clerk import ClerkHumanAuthProvider
        _provider_instance = ClerkHumanAuthProvider()
        logger.info("human_auth_provider_selected", extra={"provider": "clerk"})

    return _provider_instance


def reset_human_auth_provider() -> None:
    """Reset the provider singleton (for testing only)."""
    global _provider_instance
    _provider_instance = None
