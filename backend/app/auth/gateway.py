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

INVARIANTS:
1. Mutual Exclusivity: JWT XOR API Key (both = HARD FAIL)
2. Human Flow: JWT → HumanAuthContext (no permissions)
3. Machine Flow: API Key → MachineCapabilityContext (scopes, no RBAC)
4. Session Revocation: Every human request checks revocation
5. Headers Stripped: After gateway, auth headers are removed from request

ROUTING (Issuer-Based):
- Route based on `iss` claim, NEVER on `alg` header
- `iss: "agenticverz-console"` → ConsoleAuthenticator (HS256)
- `iss` in CLERK_ISSUERS → ClerkAuthenticator (RS256)
- Unknown issuer → REJECT

DESIGN:
- TokenClassifier parses claims without verification
- Issuer determines which authenticator to use
- Each authenticator is a separate trust domain
- Deprecation controlled by feature flags
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
    HumanAuthContext,
    MachineCapabilityContext,
)
from .gateway_metrics import (
    record_console_grace_period,
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
# Configuration (No Fallback Chains)
# =============================================================================

# Console JWT secret - single source, no aliasing
CONSOLE_JWT_SECRET = os.getenv("CONSOLE_JWT_SECRET", "")
CONSOLE_TOKEN_ISSUER = "agenticverz-console"

# Clerk issuers - explicit list, exact match only
_clerk_issuers_raw = os.getenv("CLERK_ISSUERS", "")
CLERK_ISSUERS: Set[str] = set(
    iss.strip() for iss in _clerk_issuers_raw.split(",") if iss.strip()
)

# Warn if CLERK_ISSUERS is empty (Clerk auth will be effectively disabled)
if not CLERK_ISSUERS:
    logger.warning(
        "CLERK_ISSUERS is empty - Clerk authentication is disabled. "
        "Set CLERK_ISSUERS env var for production."
    )

# Feature flags for deprecation control
AUTH_CONSOLE_ENABLED = os.getenv("AUTH_CONSOLE_ENABLED", "true").lower() == "true"
AUTH_CONSOLE_ALLOW_MISSING_ISS = os.getenv("AUTH_CONSOLE_ALLOW_MISSING_ISS", "true").lower() == "true"
AUTH_STUB_ENABLED = os.getenv("AUTH_STUB_ENABLED", "true").lower() == "true"

# Machine auth
AOS_API_KEY = os.getenv("AOS_API_KEY", "")


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

        Returns TokenInfo with issuer (may be None for legacy tokens).
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

    Usage:
        gateway = AuthGateway()
        result = await gateway.authenticate(
            authorization_header=request.headers.get("Authorization"),
            api_key_header=request.headers.get("X-AOS-Key"),
        )

        if isinstance(result, GatewayAuthError):
            return error_response(result)

        # result is now HumanAuthContext or MachineCapabilityContext
        request.state.auth_context = result
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

        Routes to appropriate authenticator based on token issuer (iss claim).
        NEVER routes based on algorithm (alg header).
        """
        # Extract token from Bearer header
        token = self._extract_bearer_token(authorization_header)
        if token is None:
            return error_jwt_invalid("Malformed Authorization header")

        # Check for stub token first (development/CI)
        if AUTH_STUB_ENABLED and token.startswith("stub_"):
            return self._authenticate_stub(token)

        # Classify token by issuer
        try:
            token_info = self._classifier.classify(token)
        except ValueError as e:
            record_token_rejected("unknown", "malformed")
            return error_jwt_invalid(str(e))

        # Route based on issuer
        return await self._route_by_issuer(token_info)

    async def _route_by_issuer(self, token_info: TokenInfo) -> GatewayResult:
        """
        Route token to appropriate authenticator based on issuer.

        Routing rules:
        1. iss == "agenticverz-console" → ConsoleAuthenticator
        2. iss in CLERK_ISSUERS → ClerkAuthenticator
        3. iss == None AND grace period → ConsoleAuthenticator (with warning)
        4. Unknown issuer → REJECT
        """
        issuer = token_info.issuer

        # Route 1: Console tokens (explicit issuer)
        if issuer == CONSOLE_TOKEN_ISSUER:
            if not AUTH_CONSOLE_ENABLED:
                record_token_rejected("console", "disabled")
                return error_jwt_invalid("Console authentication is disabled")
            return self._authenticate_console(token_info)

        # Route 2: Clerk tokens (exact match against configured issuers)
        if issuer and issuer in CLERK_ISSUERS:
            return await self._authenticate_clerk(token_info)

        # Route 3: Grace period for legacy tokens without iss claim
        if issuer is None and AUTH_CONSOLE_ALLOW_MISSING_ISS and AUTH_CONSOLE_ENABLED:
            # Try console auth with grace period logging
            record_console_grace_period()
            logger.warning(
                "[DEPRECATED] Token missing iss claim - accepted via grace period. "
                "This will be rejected after grace period ends."
            )
            return self._authenticate_console(token_info)

        # Route 4: Unknown issuer - REJECT
        record_token_rejected("unknown", "untrusted_issuer")
        logger.warning(f"Untrusted token issuer: {issuer}")
        return error_jwt_invalid(f"Untrusted token issuer: {issuer}")

    def _authenticate_console(self, token_info: TokenInfo) -> GatewayResult:
        """
        Console Authenticator - HS256 tokens from agenticverz-console issuer.

        TRANSITIONAL: This authenticator handles tokens from the custom login system.
        Will be deprecated when Clerk is fully integrated.

        Trust domain: Internal console authentication
        Algorithm: HS256 (symmetric)
        Secret: CONSOLE_JWT_SECRET
        """
        try:
            import jwt
        except ImportError:
            logger.error("PyJWT not installed for console token verification")
            record_token_rejected("console", "library_missing")
            return error_internal("JWT library not available")

        if not CONSOLE_JWT_SECRET:
            logger.error("CONSOLE_JWT_SECRET not configured")
            record_token_rejected("console", "secret_missing")
            return error_internal("Console authentication not configured")

        try:
            # Verify and decode the token with HS256
            payload = jwt.decode(
                token_info.raw_token,
                CONSOLE_JWT_SECRET,
                algorithms=["HS256"],
                options={
                    "verify_exp": True,
                    "verify_aud": False,  # Console tokens don't use audience
                    "require": ["exp", "sub"],  # Required claims
                },
            )

            # Verify issuer if present (grace period allows missing iss)
            token_issuer = payload.get("iss")
            if token_issuer and token_issuer != CONSOLE_TOKEN_ISSUER:
                record_token_rejected("console", "issuer_mismatch")
                return error_jwt_invalid(f"Invalid issuer: expected {CONSOLE_TOKEN_ISSUER}")

            # Extract claims
            user_id = payload.get("sub")
            if not user_id:
                record_token_rejected("console", "missing_sub")
                return error_jwt_invalid("Missing subject claim")

            # Generate session ID from token if not present
            session_id = payload.get("sid", payload.get("jti", ""))
            if not session_id:
                session_id = hashlib.sha256(token_info.raw_token.encode()).hexdigest()[:32]

            # Extract tenant
            tenant_id = payload.get("org_id") or payload.get("tenant_id") or "default"

            # Record successful verification
            record_token_verified("console")

            return HumanAuthContext(
                actor_id=user_id,
                session_id=session_id,
                auth_source=AuthSource.CONSOLE,  # Explicit CONSOLE source
                tenant_id=tenant_id,
                account_id=payload.get("account_id"),
                email=payload.get("email"),
                display_name=payload.get("name"),
                authenticated_at=datetime.utcnow(),
            )

        except jwt.ExpiredSignatureError:
            record_token_rejected("console", "expired")
            return error_jwt_expired()
        except jwt.InvalidTokenError as e:
            record_token_rejected("console", "invalid_signature")
            logger.warning(f"Console JWT validation failed: {e}")
            return error_jwt_invalid(str(e))
        except Exception as e:
            record_token_rejected("console", "internal_error")
            logger.exception(f"Console JWT auth error: {e}")
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

    def _authenticate_stub(self, token: str) -> GatewayResult:
        """
        Authenticate using stub token (development/CI only).

        Stub tokens have format: stub_<role>_<tenant>
        """
        from .stub import parse_stub_token

        claims = parse_stub_token(token)
        if claims is None:
            return error_jwt_invalid("Invalid stub token format")

        # Generate deterministic session ID from token
        session_id = hashlib.sha256(token.encode()).hexdigest()[:32]

        return HumanAuthContext(
            actor_id=claims.sub,
            session_id=session_id,
            auth_source=AuthSource.STUB,
            tenant_id=claims.org_id,
            account_id=None,
            email=None,
            display_name=f"Stub User ({claims.roles[0]})" if claims.roles else "Stub User",
            authenticated_at=datetime.utcnow(),
        )

    async def _authenticate_clerk(self, token_info: TokenInfo) -> GatewayResult:
        """
        Clerk Authenticator - RS256 tokens from Clerk IdP.

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
                logger.error("Clerk not configured for production JWT auth")
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

            # Extract tenant from org_id or metadata
            tenant_id = payload.get("org_id")
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

        # Check against simple environment key (legacy compatibility)
        if AOS_API_KEY and api_key == AOS_API_KEY:
            return self._create_legacy_machine_context(api_key)

        # Use API key service if available
        if self._api_key_service:
            return await self._validate_api_key_service(api_key)

        # No API key service and key doesn't match env var
        return error_api_key_invalid()

    def _create_legacy_machine_context(self, api_key: str) -> MachineCapabilityContext:
        """
        Create machine context for legacy AOS_API_KEY.

        Legacy keys get full access for backward compatibility.
        """
        key_fingerprint = hashlib.sha256(api_key.encode()).hexdigest()[:16]

        return MachineCapabilityContext(
            key_id=key_fingerprint,
            key_name="legacy_aos_key",
            auth_source=AuthSource.API_KEY,
            tenant_id="default",  # Legacy keys are not tenant-scoped
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
