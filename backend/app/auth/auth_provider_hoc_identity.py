# Layer: L4 — Domain Engine
# Product: system-wide
# AUDIENCE: SHARED
# Temporal:
#   Trigger: api
#   Execution: async
# Role: HOC Identity provider scaffold — in-house EdDSA/JWKS verification (TODO)
# Callers: auth_provider.get_human_auth_provider()
# Allowed Imports: L4 (auth_provider, auth_constants)
# Forbidden Imports: L1, L2, L5, L6
# Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md

"""
HocIdentityHumanAuthProvider — In-House Auth Provider Scaffold

Placeholder for the first-party HOC Identity authentication provider.
Implements HumanAuthProvider interface with TODO stubs for:
- EdDSA (Ed25519) JWT verification via JWKS
- Claim validation against canonical JWTClaim constants
- Session revocation check

INVARIANTS:
1. Currently raises AuthProviderError(PROVIDER_UNAVAILABLE) for all calls.
2. Will be activated when AUTH_PROVIDER=hoc_identity and implementation complete.
3. Must emit the same HumanPrincipal contract as ClerkHumanAuthProvider.
"""

from __future__ import annotations

import logging
import os

from .auth_constants import (
    AuthDenyReason,
    AuthProviderType,
    HOC_IDENTITY_AUDIENCE,
    HOC_IDENTITY_ISSUER,
    JWTClaim,
)
from .auth_provider import AuthProviderError, HumanAuthProvider, HumanPrincipal

logger = logging.getLogger("nova.auth.auth_provider_hoc_identity")

# Configuration (env vars per V1 design)
_JWKS_ENDPOINT = os.getenv("HOC_IDENTITY_JWKS_ENDPOINT", "/.well-known/jwks.json")
_ACCESS_TOKEN_LIFETIME = int(os.getenv("ACCESS_TOKEN_LIFETIME", "900"))  # 15 min default


class HocIdentityHumanAuthProvider(HumanAuthProvider):
    """
    In-house HOC Identity auth provider (scaffold).

    TODO: Implement the following when moving beyond scaffold:
    1. JWKS client for Ed25519 public key fetching and caching.
    2. EdDSA JWT signature verification.
    3. Mandatory claim validation (all 9 JWTClaim.MANDATORY fields).
    4. Session revocation check (sid against revocation store).
    5. Tenant binding validation (tid must be non-empty for CUS paths).
    """

    @property
    def provider_type(self) -> AuthProviderType:
        return AuthProviderType.HOC_IDENTITY

    @property
    def is_configured(self) -> bool:
        # TODO: Check for signing key availability, JWKS endpoint reachability
        return False

    async def verify_bearer_token(self, token: str) -> HumanPrincipal:
        """
        Verify an HOC Identity EdDSA JWT and return a HumanPrincipal.

        TODO: Implement full verification:
        1. Decode JWT header → extract kid
        2. Fetch signing key from JWKS endpoint (with 10-min cache)
        3. Verify EdDSA signature
        4. Validate mandatory claims (JWTClaim.MANDATORY)
        5. Check iss == HOC_IDENTITY_ISSUER
        6. Check aud == HOC_IDENTITY_AUDIENCE
        7. Check exp > now > iat
        8. Check session not revoked (sid lookup)
        9. Build and return HumanPrincipal
        """
        # Scaffold: not yet implemented
        raise AuthProviderError(
            AuthDenyReason.PROVIDER_UNAVAILABLE,
            "HOC Identity provider not yet implemented — set AUTH_PROVIDER=clerk",
        )
