# Layer: L4 — Domain Engine
# Product: system-wide
# AUDIENCE: SHARED
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Clerk adapter implementing HumanAuthProvider — wraps existing clerk_provider.py
# Callers: auth_provider.get_human_auth_provider()
# Allowed Imports: L4 (auth_provider, auth_constants, clerk_provider, contexts)
# Forbidden Imports: L1, L2, L5, L6
# Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md

"""
ClerkHumanAuthProvider — Clerk Adapter for HumanAuthProvider Seam

Wraps the existing clerk_provider.py verification path behind the
HumanAuthProvider interface. This is the default provider and preserves
all existing Clerk authentication behavior.

INVARIANTS:
1. Delegates to existing ClerkAuthProvider.verify_token() — no new Clerk logic.
2. Maps Clerk JWT claims to HumanPrincipal contract.
3. Preserves all existing error codes and metrics emissions.
"""

from __future__ import annotations

import logging
from datetime import datetime

from .auth_constants import AuthDenyReason, AuthProviderType
from .auth_provider import AuthProviderError, HumanAuthProvider, HumanPrincipal
from .clerk_provider import ClerkAuthError, get_clerk_provider
from .gateway_metrics import record_token_rejected, record_token_verified

logger = logging.getLogger("nova.auth.auth_provider_clerk")


class ClerkHumanAuthProvider(HumanAuthProvider):
    """
    Clerk adapter implementing the HumanAuthProvider seam.

    Delegates JWT verification to the existing ClerkAuthProvider singleton
    and maps verified claims to the canonical HumanPrincipal contract.
    """

    def __init__(self) -> None:
        self._clerk = get_clerk_provider()

    @property
    def provider_type(self) -> AuthProviderType:
        return AuthProviderType.CLERK

    @property
    def is_configured(self) -> bool:
        return self._clerk.is_configured

    async def verify_bearer_token(self, token: str) -> HumanPrincipal:
        """
        Verify a Clerk RS256 JWT and return a HumanPrincipal.

        Delegates to ClerkAuthProvider.verify_token() and maps claims.
        """
        if not self.is_configured:
            record_token_rejected("clerk", "not_configured")
            raise AuthProviderError(
                AuthDenyReason.PROVIDER_UNAVAILABLE,
                "Clerk not configured for human authentication",
            )

        try:
            payload = self._clerk.verify_token(token)
        except ClerkAuthError as e:
            error_msg = str(e).lower()
            if "expired" in error_msg:
                record_token_rejected("clerk", "expired")
                raise AuthProviderError(AuthDenyReason.TOKEN_EXPIRED, str(e))
            record_token_rejected("clerk", "invalid_signature")
            raise AuthProviderError(AuthDenyReason.TOKEN_INVALID_SIGNATURE, str(e))
        except Exception as e:
            record_token_rejected("clerk", "internal_error")
            logger.exception(f"Clerk token verification error: {e}")
            raise AuthProviderError(AuthDenyReason.INTERNAL_ERROR, str(e))

        # Extract claims — Clerk uses standard JWT fields + org_id for tenant
        user_id = payload.get("sub")
        if not user_id:
            record_token_rejected("clerk", "missing_sub")
            raise AuthProviderError(
                AuthDenyReason.TOKEN_MISSING_CLAIMS,
                "Missing subject claim",
            )

        record_token_verified("clerk")

        return HumanPrincipal(
            subject_user_id=user_id,
            email=payload.get("email"),
            tenant_id=payload.get("org_id"),
            session_id=payload.get("sid", payload.get("jti", "")),
            roles_or_groups=tuple(),  # Clerk roles resolved downstream via API
            issued_at=datetime.utcfromtimestamp(payload.get("iat", 0)),
            expires_at=datetime.utcfromtimestamp(payload.get("exp", 0)),
            auth_provider=AuthProviderType.CLERK,
        )
