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
# capability_id: CAP-006

"""
Human Auth Provider Seam

Defines the HumanAuthProvider interface, the HumanPrincipal data contract,
and the provider factory for the canonical Clove auth provider.

INVARIANTS:
1. All human authentication flows go through a HumanAuthProvider.
2. The provider returns a HumanPrincipal; the gateway maps it to HumanAuthContext.
3. Provider selection is determined at startup via AUTH_PROVIDER env var.
4. Default and canonical provider is "clove".
5. "clerk" is DEPRECATED — triggers warning (non-prod) or fail-fast (prod).
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

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
    tenant_id: Optional[str]              # Active tenant binding (JWT tid)
    account_id: Optional[str]             # Provider account ID (optional profile linkage)
    session_id: Optional[str]              # Session ID for revocation (JWT sid)
    display_name: Optional[str]            # Display name (HOC profile)
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
    - CloveHumanAuthProvider: in-house EdDSA/JWKS verification (canonical).
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

# Env switch — Clove is the canonical default
AUTH_PROVIDER_ENV = os.getenv("AUTH_PROVIDER", "clove").lower().strip()

# Legacy alias mapping: "hoc_identity" → "clove" (silent upgrade)
_LEGACY_ALIASES = {"hoc_identity": "clove"}

# Singleton cache
_provider_instance: Optional[HumanAuthProvider] = None


def get_human_auth_provider() -> HumanAuthProvider:
    """
    Get the configured HumanAuthProvider singleton.

    Selection is driven by AUTH_PROVIDER env var.
    Canonical value:
    - "clove" (default): CloveHumanAuthProvider
    Deprecated:
    - "clerk": triggers deprecation warning (non-prod) or fail-fast (prod)
    - "hoc_identity": silently upgraded to "clove"

    Returns:
        The configured HumanAuthProvider instance.
    """
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    effective = _LEGACY_ALIASES.get(AUTH_PROVIDER_ENV, AUTH_PROVIDER_ENV)

    if effective != "clove":
        runtime_mode = (
            os.getenv("AOS_MODE")
            or os.getenv("APP_ENV")
            or os.getenv("ENV")
            or ""
        ).strip().lower()

        if AUTH_PROVIDER_ENV == "clerk":
            message = (
                f"AUTH_PROVIDER=clerk is DEPRECATED; "
                "forcing clove (policy: clerk deprecated)"
            )
        else:
            message = (
                f"AUTH_PROVIDER={AUTH_PROVIDER_ENV or '<empty>'} ignored; "
                "forcing clove (canonical provider)"
            )

        if runtime_mode in {"prod", "production"}:
            logger.critical(message + " [fatal in prod]")
            raise RuntimeError(
                "Invalid AUTH_PROVIDER in production: must be clove"
            )
        logger.warning(
            message,
            extra={"requested_provider": AUTH_PROVIDER_ENV, "runtime_mode": runtime_mode or "unknown"},
        )

    from .auth_provider_clove import CloveHumanAuthProvider

    _provider_instance = CloveHumanAuthProvider()
    logger.info("human_auth_provider_selected", extra={"provider": "clove"})

    return _provider_instance


def reset_human_auth_provider() -> None:
    """Reset the provider singleton (for testing only)."""
    global _provider_instance
    _provider_instance = None


def get_human_auth_provider_status() -> dict[str, Any]:
    """
    Return provider policy and runtime status for observability endpoints.

    This makes auth-provider policy decisions visible to operators.
    """
    provider = get_human_auth_provider()
    effective = _LEGACY_ALIASES.get(AUTH_PROVIDER_ENV, AUTH_PROVIDER_ENV)
    is_deprecated = AUTH_PROVIDER_ENV in {"clerk"}
    # Readiness checks (per-input pass/fail)
    readiness_fn = getattr(provider, "readiness_summary", None)
    readiness = readiness_fn() if callable(readiness_fn) else {"ready": provider.is_configured, "checks": [], "failed_count": 0}

    status: dict[str, Any] = {
        "requested_provider": AUTH_PROVIDER_ENV or "clove",
        "effective_provider": provider.provider_type.value,
        "canonical_provider": "clove",
        "forced": (effective != provider.provider_type.value),
        "configured": provider.is_configured,
        "readiness": readiness,
        "deprecation": {
            "clerk": {
                "status": "deprecated",
                "message": "Clerk is deprecated. Clove is the canonical auth provider.",
                "migration": "Set AUTH_PROVIDER=clove (or remove — clove is the default).",
            },
        },
    }

    diagnostics = getattr(provider, "diagnostics", None)
    if callable(diagnostics):
        status["provider_diagnostics"] = diagnostics()

    return status
