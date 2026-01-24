# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Central authentication gateway - single entry point for all auth
# Callers: gateway_middleware ONLY
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-306 (Capability Registry), CAP-006 (Authentication)
# capability_id: CAP-006

"""
Auth Gateway - Central Authentication Entry Point

This module is the ONLY place where authentication headers are parsed.
All downstream code consumes contexts, never raw headers.

INVARIANTS (AUTH_DESIGN.md):
1. Mutual Exclusivity: JWT XOR API Key (both = HARD FAIL)
2. Human Flow: Clerk JWT (RS256) → HumanAuthContext
3. Machine Flow: API Key → MachineCapabilityContext
4. Session Revocation: Every human request checks revocation
5. Headers Stripped: After gateway, auth headers are removed from request

ROUTING:
- All human JWTs must be from Clerk (RS256, JWKS-verified)
- Unknown issuer → REJECT
- No fallbacks. No grace periods.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Set

from .contexts import (
    AuthPlane,
    AuthSource,
    FounderAuthContext,
    HumanAuthContext,
    MachineCapabilityContext,
)
from .gateway_metrics import (
    record_token_rejected,
    record_token_verified,
)
from .gateway_types import (
    GatewayResult,
    error_api_key_invalid,
    error_internal,
    error_jwt_expired,
    error_jwt_invalid,
    error_missing_auth,
    error_mixed_auth,
    error_provider_unavailable,
    error_session_revoked,
)

logger = logging.getLogger("nova.auth.gateway")

# =============================================================================
# Configuration
# =============================================================================

# Clerk issuers - explicit list, exact match only
_clerk_issuers_raw = os.getenv("CLERK_ISSUERS", "")
CLERK_ISSUERS: Set[str] = set(
    iss.strip() for iss in _clerk_issuers_raw.split(",") if iss.strip()
)

# Require Clerk to be configured for human auth
if not CLERK_ISSUERS:
    logger.warning(
        "CLERK_ISSUERS is empty - human authentication is disabled. "
        "Set CLERK_ISSUERS env var for production."
    )

# Machine auth - legacy env var support (to be migrated to DB-only)
AOS_API_KEY = os.getenv("AOS_API_KEY", "")

# Founder auth - FOPS tokens (control plane)
AOS_FOPS_SECRET = os.getenv("AOS_FOPS_SECRET", "")
FOPS_ISSUER = "agenticverz-fops"

if not AOS_FOPS_SECRET:
    logger.warning(
        "AOS_FOPS_SECRET is empty - founder authentication is disabled. "
        "Set AOS_FOPS_SECRET env var for production."
    )


# =============================================================================
# TokenClassifier (Issuer-Based Routing)
# =============================================================================

@dataclass
class TokenInfo:
    """Parsed token information for routing decisions."""
    issuer: Optional[str]
    raw_token: str


class TokenClassifier:
    """
    Classify tokens by issuer for routing to appropriate authenticator.

    CRITICAL: This class NEVER routes based on `alg` header.
    The `alg` header is attacker-controlled and must not influence routing.
    """

    def classify(self, token: str) -> TokenInfo:
        """
        Extract issuer from token without verification.

        Returns TokenInfo with issuer.
        Does NOT validate the token - just extracts routing information.
        """
        try:
            import jwt
            # Decode WITHOUT verification to get claims for routing
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
            )
            return TokenInfo(
                issuer=payload.get("iss"),
                raw_token=token,
            )
        except Exception as e:
            logger.warning(f"Token classification failed: {e}")
            raise ValueError(f"Malformed JWT: {e}")


class AuthGateway:
    """
    Central authentication gateway.

    This class is the ONLY entry point for authentication.
    All JWT parsing, API key validation, and session checking
    happens here and nowhere else.

    DESIGN (AUTH_DESIGN.md):
    - Humans authenticate via Clerk only
    - Machines authenticate via API key only
    - No fallbacks, no grace periods, no alternative paths
    """

    def __init__(
        self,
        session_store: Optional["SessionStore"] = None,
        api_key_service: Optional["ApiKeyService"] = None,
    ):
        """
        Initialize the gateway.

        Args:
            session_store: Optional session revocation store
            api_key_service: Optional API key validation service
        """
        self._session_store = session_store
        self._api_key_service = api_key_service
        self._clerk_provider = None  # Lazy-loaded
        self._classifier = TokenClassifier()

    async def authenticate(
        self,
        authorization_header: Optional[str],
        api_key_header: Optional[str],
    ) -> GatewayResult:
        """
        Authenticate a request.

        This is the SINGLE entry point for all authentication.

        Args:
            authorization_header: Value of Authorization header (Bearer <token>)
            api_key_header: Value of X-AOS-Key header

        Returns:
            GatewayResult: HumanAuthContext, MachineCapabilityContext, or GatewayAuthError
        """
        # Check for mutual exclusivity FIRST
        has_jwt = authorization_header is not None and authorization_header.strip() != ""
        has_api_key = api_key_header is not None and api_key_header.strip() != ""

        if has_jwt and has_api_key:
            # HARD FAIL: Both headers present violates mutual exclusivity
            logger.warning("MIXED_AUTH: Both Authorization and X-AOS-Key present")
            return error_mixed_auth()

        if not has_jwt and not has_api_key:
            return error_missing_auth()

        # Route to appropriate flow
        if has_jwt:
            return await self._authenticate_human(authorization_header)
        else:
            return await self._authenticate_machine(api_key_header)

    async def _authenticate_human(
        self,
        authorization_header: str,
    ) -> GatewayResult:
        """
        Human authentication flow (JWT).

        All human JWTs must be from Clerk.
        No other human authentication path exists.
        """
        # Extract token from Bearer header
        token = self._extract_bearer_token(authorization_header)
        if token is None:
            return error_jwt_invalid("Malformed Authorization header")

        # Classify token by issuer
        try:
            token_info = self._classifier.classify(token)
        except ValueError as e:
            record_token_rejected("unknown", "malformed")
            return error_jwt_invalid(str(e))

        # Route based on issuer - Clerk only
        return await self._route_by_issuer(token_info)

    async def _route_by_issuer(self, token_info: TokenInfo) -> GatewayResult:
        """
        Route token to appropriate authenticator based on issuer.

        Routes:
        - FOPS issuer → Founder auth (control plane)
        - Clerk issuers → Human auth (tenant-scoped)
        - All others → REJECT

        No fallbacks. No grace periods.
        """
        issuer = token_info.issuer

        # Route 1: FOPS tokens (founder/control plane)
        if issuer == FOPS_ISSUER:
            return self._authenticate_fops_token(token_info.raw_token)

        # Route 2: Clerk tokens (human/tenant-scoped)
        if issuer and issuer in CLERK_ISSUERS:
            return await self._authenticate_clerk(token_info)

        # All other issuers are rejected
        record_token_rejected("unknown", "untrusted_issuer")
        logger.warning(f"Untrusted token issuer: {issuer}")
        return error_jwt_invalid(f"Untrusted token issuer: {issuer}")

    def _authenticate_fops_token(self, token: str) -> GatewayResult:
        """
        Founder (FOPS) token authentication.

        FOPS tokens are control-plane only:
        - No tenant_id
        - No roles
        - No scopes
        - reason is required (audit trail)

        Trust domain: Internal FOPS infrastructure
        Algorithm: HS256 (symmetric)
        """
        import jwt

        if not AOS_FOPS_SECRET:
            record_token_rejected("fops", "not_configured")
            logger.error("FOPS authentication not configured")
            return error_provider_unavailable("fops")

        try:
            payload = jwt.decode(
                token,
                AOS_FOPS_SECRET,
                algorithms=["HS256"],
                options={"require": ["exp", "iat", "sub", "iss", "reason"]},
            )

            if payload.get("iss") != FOPS_ISSUER:
                record_token_rejected("fops", "invalid_issuer")
                return error_jwt_invalid("Invalid FOPS issuer")

            # Validate reason is present and non-empty
            reason = payload.get("reason", "")
            if not reason or not reason.strip():
                record_token_rejected("fops", "missing_reason")
                return error_jwt_invalid("FOPS token missing reason")

            record_token_verified("fops")

            return FounderAuthContext(
                actor_id=payload["sub"],
                reason=reason.strip(),
                issued_at=datetime.utcfromtimestamp(payload["iat"]),
            )

        except jwt.ExpiredSignatureError:
            record_token_rejected("fops", "expired")
            return error_jwt_expired()
        except jwt.InvalidTokenError as e:
            record_token_rejected("fops", "invalid")
            logger.warning(f"FOPS token validation failed: {e}")
            return error_jwt_invalid(str(e))
        except Exception as e:
            record_token_rejected("fops", "internal_error")
            logger.exception(f"FOPS auth error: {e}")
            return error_internal(str(e))

    def _extract_bearer_token(self, authorization_header: str) -> Optional[str]:
        """Extract token from 'Bearer <token>' format."""
        if not authorization_header:
            return None

        parts = authorization_header.split(" ", 1)
        if len(parts) != 2:
            return None

        scheme, token = parts
        if scheme.lower() != "bearer":
            return None

        return token.strip() if token.strip() else None

    async def _authenticate_clerk(self, token_info: TokenInfo) -> GatewayResult:
        """
        Clerk Authenticator - RS256 tokens from Clerk IdP.

        This is the ONLY human authentication path.

        Trust domain: External identity provider (Clerk)
        Algorithm: RS256 (asymmetric)
        Verification: JWKS (public key)
        """
        try:
            # Lazy-load Clerk provider
            if self._clerk_provider is None:
                from .clerk_provider import get_clerk_provider

                self._clerk_provider = get_clerk_provider()

            # Check if Clerk is configured
            if not self._clerk_provider.is_configured:
                logger.error("Clerk not configured for human authentication")
                record_token_rejected("clerk", "not_configured")
                return error_provider_unavailable("clerk")

            # Verify JWT via JWKS
            try:
                payload = self._clerk_provider.verify_token(token_info.raw_token)
            except Exception as e:
                error_msg = str(e).lower()
                logger.warning(f"Clerk JWT verify failed: {type(e).__name__}: {e}")
                if "expired" in error_msg:
                    record_token_rejected("clerk", "expired")
                    return error_jwt_expired()
                record_token_rejected("clerk", "invalid_signature")
                return error_jwt_invalid(str(e))

            # Extract claims
            user_id = payload.get("sub")
            session_id = payload.get("sid", payload.get("jti", ""))

            if not user_id:
                record_token_rejected("clerk", "missing_sub")
                return error_jwt_invalid("Missing subject claim")

            # Check session revocation
            if self._session_store:
                is_revoked = await self._session_store.is_revoked(session_id)
                if is_revoked:
                    record_token_rejected("clerk", "revoked")
                    logger.warning(f"Revoked session attempted: {session_id[:8]}...")
                    return error_session_revoked()

            # Extract tenant from org_id - NO FALLBACK
            tenant_id = payload.get("org_id")
            if not tenant_id:
                # Tenant resolution from membership lookup will happen downstream
                # But we don't provide a "default" - that's a governance violation
                pass

            account_id = payload.get("account_id")

            # Record successful verification
            record_token_verified("clerk")

            return HumanAuthContext(
                actor_id=user_id,
                session_id=session_id,
                auth_source=AuthSource.CLERK,
                tenant_id=tenant_id,
                account_id=account_id,
                email=payload.get("email"),
                display_name=payload.get("name"),
                authenticated_at=datetime.utcnow(),
            )

        except Exception as e:
            record_token_rejected("clerk", "internal_error")
            logger.exception(f"Clerk JWT auth error: {e}")
            return error_internal(str(e))

    async def _authenticate_machine(
        self,
        api_key_header: str,
    ) -> GatewayResult:
        """
        Machine authentication flow (API Key).

        Validates API key and returns MachineCapabilityContext.
        """
        if not api_key_header or not api_key_header.strip():
            return error_api_key_invalid()

        api_key = api_key_header.strip()

        # Use API key service if available (production path)
        if self._api_key_service:
            return await self._validate_api_key_service(api_key)

        # Legacy: Check against environment key
        if AOS_API_KEY and api_key == AOS_API_KEY:
            return self._create_legacy_machine_context(api_key)

        # No valid key
        return error_api_key_invalid()

    def _create_legacy_machine_context(self, api_key: str) -> MachineCapabilityContext:
        """
        Create machine context for legacy AOS_API_KEY.

        This path exists for backward compatibility during migration.
        Production should use database-validated API keys.
        """
        key_fingerprint = hashlib.sha256(api_key.encode()).hexdigest()[:16]

        return MachineCapabilityContext(
            key_id=key_fingerprint,
            key_name="legacy_aos_key",
            auth_source=AuthSource.API_KEY,
            tenant_id=None,  # Legacy keys require tenant lookup
            scopes=frozenset({"*"}),  # Full access for backward compatibility
            rate_limit=1000,  # Default rate limit
            authenticated_at=datetime.utcnow(),
        )

    async def _validate_api_key_service(self, api_key: str) -> GatewayResult:
        """
        Validate API key using the API key service.

        This is the production machine authentication flow.
        """
        try:
            key_info = await self._api_key_service.validate_key(api_key)

            if key_info is None:
                return error_api_key_invalid()

            if key_info.get("revoked"):
                return error_api_key_invalid()  # Don't reveal revocation status

            return MachineCapabilityContext(
                key_id=key_info["key_id"],
                key_name=key_info.get("name"),
                auth_source=AuthSource.API_KEY,
                tenant_id=key_info["tenant_id"],
                scopes=frozenset(key_info.get("scopes", ["*"])),
                rate_limit=key_info.get("rate_limit", 1000),
                authenticated_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.exception(f"API key validation error: {e}")
            return error_internal(str(e))

    def get_auth_plane(self, result: GatewayResult) -> Optional[AuthPlane]:
        """
        Get the authentication plane from a result.

        Returns None if result is an error.
        """
        if isinstance(result, HumanAuthContext):
            return AuthPlane.HUMAN
        elif isinstance(result, MachineCapabilityContext):
            return AuthPlane.MACHINE
        elif isinstance(result, FounderAuthContext):
            return AuthPlane.HUMAN  # Founders are humans, but control-plane
        return None


# Singleton gateway instance
_gateway: Optional[AuthGateway] = None


def get_auth_gateway() -> AuthGateway:
    """Get or create the auth gateway singleton."""
    global _gateway
    if _gateway is None:
        _gateway = AuthGateway()
    return _gateway


def configure_auth_gateway(
    session_store: Optional["SessionStore"] = None,
    api_key_service: Optional["ApiKeyService"] = None,
) -> AuthGateway:
    """
    Configure the auth gateway with services.

    Call this during application startup to wire in dependencies.
    """
    global _gateway
    _gateway = AuthGateway(
        session_store=session_store,
        api_key_service=api_key_service,
    )
    return _gateway


# Type hints for services (defined in other modules)
class SessionStore:
    """Protocol for session revocation store."""

    async def is_revoked(self, session_id: str) -> bool:
        """Check if a session has been revoked."""
        ...


class ApiKeyService:
    """Protocol for API key validation service."""

    async def validate_key(self, api_key: str) -> Optional[dict]:
        """
        Validate an API key.

        Returns dict with key_id, tenant_id, scopes, rate_limit
        or None if invalid.
        """
        ...
