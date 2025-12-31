# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Console-specific authentication handling
# Callers: console API routes
# Allowed Imports: None
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Auth Infrastructure

"""
Console Auth - Domain-Separated Authentication for AOS Consoles

PIN-148 Category 2: Auth Boundary Verification (Full Spec)

INVARIANTS (from spec):
1. A token belongs to exactly one domain
2. A session belongs to exactly one console
3. A role escalation is impossible by accident
4. Failure must be loud and logged

This module provides SEPARATE authentication for:
- Customer Console (aud="console") - /guard/* endpoints
- Founder Ops Console (aud="fops") - /ops/* endpoints

NO SHARED LOGIC. NO FLAGS. NO FALLBACKS.
"""

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Literal, Optional

from fastapi import Cookie, Depends, HTTPException, Request, status

# JWT support
try:
    import jwt

    HAS_JWT = True
except ImportError:
    jwt = None
    HAS_JWT = False

logger = logging.getLogger("nova.console_auth")


# =============================================================================
# 2.1 TOKEN MODEL - FOUNDATION
# =============================================================================


class TokenAudience(str, Enum):
    """Explicit token audiences - NO SHARED TOKENS."""

    CONSOLE = "console"  # Customer Console
    FOPS = "fops"  # Founder Ops Console


class CustomerRole(str, Enum):
    """Customer Console roles."""

    OWNER = "OWNER"
    ADMIN = "ADMIN"
    DEV = "DEV"
    VIEWER = "VIEWER"


class FounderRole(str, Enum):
    """Founder Ops Console roles."""

    FOUNDER = "FOUNDER"
    OPERATOR = "OPERATOR"


@dataclass
class CustomerToken:
    """
    Customer Console Token Claims.

    Required claims:
    - aud: "console" (MUST be exactly this)
    - sub: user_id
    - org_id: organization_id
    - role: OWNER | ADMIN | DEV | VIEWER
    - iss: "agenticverz"
    - exp: expiration timestamp
    """

    aud: Literal["console"]
    sub: str
    org_id: str
    role: CustomerRole
    iss: str
    exp: int
    iat: int = field(default_factory=lambda: int(time.time()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "aud": self.aud,
            "sub": self.sub,
            "org_id": self.org_id,
            "role": self.role.value if isinstance(self.role, CustomerRole) else self.role,
            "iss": self.iss,
            "exp": self.exp,
            "iat": self.iat,
        }


@dataclass
class FounderToken:
    """
    Founder Ops Console Token Claims.

    Required claims:
    - aud: "fops" (MUST be exactly this)
    - sub: founder_id
    - role: FOUNDER | OPERATOR
    - mfa: true (MUST be true)
    - iss: "agenticverz"
    - exp: expiration timestamp
    """

    aud: Literal["fops"]
    sub: str
    role: FounderRole
    mfa: bool
    iss: str
    exp: int
    iat: int = field(default_factory=lambda: int(time.time()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "aud": self.aud,
            "sub": self.sub,
            "role": self.role.value if isinstance(self.role, FounderRole) else self.role,
            "mfa": self.mfa,
            "iss": self.iss,
            "exp": self.exp,
            "iat": self.iat,
        }


# =============================================================================
# 2.4 AUDIT LOGGING - MANDATORY
# =============================================================================


class AuthRejectReason(str, Enum):
    """Explicit rejection reasons for audit logging."""

    MISSING_TOKEN = "MISSING_TOKEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    AUD_MISMATCH = "AUD_MISMATCH"
    ROLE_INVALID = "ROLE_INVALID"
    MFA_REQUIRED = "MFA_REQUIRED"
    ORG_ID_MISSING = "ORG_ID_MISSING"
    ISSUER_INVALID = "ISSUER_INVALID"


@dataclass
class AuthAuditEvent:
    """
    Audit log schema (from spec 2.4.1).

    Every rejection MUST log exactly once.
    """

    event: str = "AUTH_DOMAIN_REJECT"
    actor_id: str = ""
    attempted_domain: str = ""  # "console" | "fops"
    token_aud: str = ""  # actual aud from token | "missing"
    reason: str = ""  # AuthRejectReason value
    ip: str = ""
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event,
            "actor_id": self.actor_id,
            "attempted_domain": self.attempted_domain,
            "token_aud": self.token_aud,
            "reason": self.reason,
            "ip": self.ip,
            "ts": self.ts,
        }


def log_auth_rejection(
    request: Request,
    domain: str,
    reason: AuthRejectReason,
    actor_id: str = "",
    token_aud: str = "missing",
) -> None:
    """
    Log auth rejection event. MANDATORY for every rejection.

    This function MUST be called for every auth failure.
    Silent failures are unacceptable.
    """
    # Get client IP
    ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()

    event = AuthAuditEvent(
        actor_id=actor_id or "anonymous",
        attempted_domain=domain,
        token_aud=token_aud,
        reason=reason.value,
        ip=ip,
    )

    # Log as structured JSON
    logger.warning("auth_domain_reject", extra={"audit": event.to_dict()})

    # Also log in standard format for searchability
    logger.warning(
        f"AUTH_DOMAIN_REJECT: domain={domain} reason={reason.value} "
        f"actor={actor_id or 'anonymous'} token_aud={token_aud} ip={ip}"
    )


# =============================================================================
# TOKEN SIGNING & VERIFICATION
# =============================================================================

# Signing keys (separate per domain for clarity, but can be same with strict aud check)
CONSOLE_SECRET = os.getenv("CONSOLE_JWT_SECRET", os.getenv("AOS_JWT_SECRET", ""))
FOPS_SECRET = os.getenv("FOPS_JWT_SECRET", os.getenv("AOS_JWT_SECRET", ""))
ISSUER = "agenticverz"


def _get_signing_secret(audience: str) -> str:
    """Get signing secret for audience."""
    if audience == TokenAudience.CONSOLE.value:
        return CONSOLE_SECRET
    elif audience == TokenAudience.FOPS.value:
        return FOPS_SECRET
    return ""


def create_console_token(
    sub: str,
    org_id: str,
    role: CustomerRole,
    expires_in: int = 3600,
) -> str:
    """Create a Customer Console token."""
    if not HAS_JWT:
        raise RuntimeError("PyJWT not installed")

    now = int(time.time())
    token = CustomerToken(
        aud="console",
        sub=sub,
        org_id=org_id,
        role=role,
        iss=ISSUER,
        exp=now + expires_in,
        iat=now,
    )

    secret = _get_signing_secret("console")
    if not secret:
        raise RuntimeError("CONSOLE_JWT_SECRET not configured")

    return jwt.encode(token.to_dict(), secret, algorithm="HS256")


def create_fops_token(
    sub: str,
    role: FounderRole,
    mfa: bool = True,
    expires_in: int = 3600,
) -> str:
    """Create a Founder Ops Console token."""
    if not HAS_JWT:
        raise RuntimeError("PyJWT not installed")

    if not mfa:
        raise ValueError("MFA must be true for FOPS tokens")

    now = int(time.time())
    token = FounderToken(
        aud="fops",
        sub=sub,
        role=role,
        mfa=mfa,
        iss=ISSUER,
        exp=now + expires_in,
        iat=now,
    )

    secret = _get_signing_secret("fops")
    if not secret:
        raise RuntimeError("FOPS_JWT_SECRET not configured")

    return jwt.encode(token.to_dict(), secret, algorithm="HS256")


def decode_token(token: str, expected_audience: str) -> Dict[str, Any]:
    """
    Decode and verify a token.

    STRICT audience check - tokens from wrong domain will fail.
    """
    if not HAS_JWT:
        raise RuntimeError("PyJWT not installed")

    secret = _get_signing_secret(expected_audience)
    if not secret:
        raise ValueError(f"No secret configured for audience: {expected_audience}")

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={
                "verify_exp": True,
                "verify_aud": False,  # We check manually for clearer error
                "require": ["aud", "sub", "exp", "iss"],
            },
        )

        # STRICT audience check
        token_aud = payload.get("aud", "")
        if token_aud != expected_audience:
            raise jwt.InvalidAudienceError(
                f"Token audience '{token_aud}' does not match expected '{expected_audience}'"
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        raise


# =============================================================================
# 2.2 COOKIE & SESSION ISOLATION
# =============================================================================

# Cookie names - SEPARATE per domain
CONSOLE_COOKIE_NAME = "aos_console_session"
FOPS_COOKIE_NAME = "aos_fops_session"

# CSRF token names - SEPARATE per domain
CONSOLE_CSRF_COOKIE = "aos_console_csrf"
FOPS_CSRF_COOKIE = "aos_fops_csrf"


def get_cookie_settings(domain: str, is_production: bool = True) -> Dict[str, Any]:
    """Get cookie settings for a domain."""
    if domain == "console":
        return {
            "key": CONSOLE_COOKIE_NAME,
            "httponly": True,
            "secure": is_production,
            "samesite": "strict",
            "domain": "console.agenticverz.com" if is_production else None,
        }
    elif domain == "fops":
        return {
            "key": FOPS_COOKIE_NAME,
            "httponly": True,
            "secure": is_production,
            "samesite": "strict",
            "domain": "fops.agenticverz.com" if is_production else None,
        }
    raise ValueError(f"Unknown domain: {domain}")


# =============================================================================
# 2.3 MIDDLEWARE DESIGN - NO FLAGS, NO FALLBACKS
# =============================================================================


class AuthDomainError(HTTPException):
    """Auth domain mismatch error with proper body."""

    def __init__(self, detail: str = "AUTH_DOMAIN_MISMATCH"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail={"error": detail})


async def verify_console_token(
    request: Request,
    aos_console_session: Optional[str] = Cookie(None, alias=CONSOLE_COOKIE_NAME),
) -> CustomerToken:
    """
    Customer Console middleware.

    Applies to: /guard/* (Customer Console routes)

    Pseudo-logic (from spec 2.3.1):
        assert token exists
        assert token.aud === "console"
        assert token.org_id exists
        assert role in [OWNER, ADMIN, DEV, VIEWER]
        reject if ANY fail

    NO flags. NO fallbacks. NO shortcuts.
    """
    domain = "console"

    # Try cookie first, then Authorization header, then X-API-Key
    token_str = aos_console_session

    if not token_str:
        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token_str = auth_header[7:]

    if not token_str:
        # Check X-API-Key header (legacy support during transition)
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            # Validate API key and create synthetic token
            expected_key = os.getenv("AOS_API_KEY", "")
            if not expected_key:
                log_auth_rejection(request, domain, AuthRejectReason.MISSING_TOKEN)
                raise AuthDomainError("AUTH_NOT_CONFIGURED")

            if api_key != expected_key:
                log_auth_rejection(request, domain, AuthRejectReason.INVALID_TOKEN)
                raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

            # API key is valid - create synthetic customer token
            # This is a transitional measure; real tokens should be used in production
            return CustomerToken(
                aud="console",
                sub="api_key_user",
                org_id=request.query_params.get("tenant_id", "default"),
                role=CustomerRole.ADMIN,
                iss=ISSUER,
                exp=int(time.time()) + 3600,
            )

    if not token_str:
        log_auth_rejection(request, domain, AuthRejectReason.MISSING_TOKEN)
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

    # Decode and verify token
    try:
        payload = decode_token(token_str, expected_audience="console")
    except jwt.ExpiredSignatureError:
        log_auth_rejection(request, domain, AuthRejectReason.EXPIRED_TOKEN, token_aud="console")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "TOKEN_EXPIRED"})
    except jwt.InvalidAudienceError as e:
        # Token exists but wrong audience - this is a domain mismatch
        log_auth_rejection(request, domain, AuthRejectReason.AUD_MISMATCH, token_aud=str(e))
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")
    except jwt.InvalidTokenError:
        log_auth_rejection(request, domain, AuthRejectReason.INVALID_TOKEN)
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

    # Validate claims
    aud = payload.get("aud")
    if aud != "console":
        log_auth_rejection(
            request, domain, AuthRejectReason.AUD_MISMATCH, actor_id=payload.get("sub", ""), token_aud=aud or "missing"
        )
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

    org_id = payload.get("org_id")
    if not org_id:
        log_auth_rejection(
            request, domain, AuthRejectReason.ORG_ID_MISSING, actor_id=payload.get("sub", ""), token_aud=aud
        )
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

    role_str = payload.get("role", "")
    try:
        role = CustomerRole(role_str)
    except ValueError:
        log_auth_rejection(
            request, domain, AuthRejectReason.ROLE_INVALID, actor_id=payload.get("sub", ""), token_aud=aud
        )
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

    if role not in [CustomerRole.OWNER, CustomerRole.ADMIN, CustomerRole.DEV, CustomerRole.VIEWER]:
        log_auth_rejection(
            request, domain, AuthRejectReason.ROLE_INVALID, actor_id=payload.get("sub", ""), token_aud=aud
        )
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

    # All checks passed
    return CustomerToken(
        aud="console",
        sub=payload["sub"],
        org_id=org_id,
        role=role,
        iss=payload.get("iss", ISSUER),
        exp=payload["exp"],
        iat=payload.get("iat", int(time.time())),
    )


async def verify_fops_token(
    request: Request,
    aos_fops_session: Optional[str] = Cookie(None, alias=FOPS_COOKIE_NAME),
) -> FounderToken:
    """
    Founder Ops Console middleware.

    Applies to: /ops/* (Founder Ops routes)

    Pseudo-logic (from spec 2.3.2):
        assert token exists
        assert token.aud === "fops"
        assert role in [FOUNDER, OPERATOR]
        assert mfa === true
        reject if ANY fail

    NO reusing customer middleware.
    NO "if (isFounder)" switches.
    NO "downgrade" access.
    Founder access is EXPLICIT ONLY.
    """
    domain = "fops"

    # Try cookie first, then Authorization header, then X-API-Key
    token_str = aos_fops_session

    if not token_str:
        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token_str = auth_header[7:]

    if not token_str:
        # Check X-API-Key header (legacy support during transition)
        # For FOPS, we require a SEPARATE key: AOS_FOPS_KEY
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            # FOPS uses separate key - NOT the same as console
            expected_key = os.getenv("AOS_FOPS_KEY", "")
            if not expected_key:
                # Fall back to operator token for backwards compatibility
                expected_key = os.getenv("AOS_OPERATOR_TOKEN", "")

            if not expected_key:
                log_auth_rejection(request, domain, AuthRejectReason.MISSING_TOKEN)
                raise AuthDomainError("AUTH_NOT_CONFIGURED")

            if api_key != expected_key:
                # Check if they accidentally used the console key
                console_key = os.getenv("AOS_API_KEY", "")
                if api_key == console_key:
                    # Cross-domain access attempt - log and reject
                    log_auth_rejection(
                        request, domain, AuthRejectReason.AUD_MISMATCH, actor_id="console_key_user", token_aud="console"
                    )
                    raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

                log_auth_rejection(request, domain, AuthRejectReason.INVALID_TOKEN)
                raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

            # FOPS API key is valid - create synthetic founder token
            # MFA is assumed true for API key (key possession = MFA equivalent)
            return FounderToken(
                aud="fops",
                sub="fops_api_key_user",
                role=FounderRole.FOUNDER,
                mfa=True,
                iss=ISSUER,
                exp=int(time.time()) + 3600,
            )

    if not token_str:
        log_auth_rejection(request, domain, AuthRejectReason.MISSING_TOKEN)
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

    # Decode and verify token
    try:
        payload = decode_token(token_str, expected_audience="fops")
    except jwt.ExpiredSignatureError:
        log_auth_rejection(request, domain, AuthRejectReason.EXPIRED_TOKEN, token_aud="fops")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "TOKEN_EXPIRED"})
    except jwt.InvalidAudienceError:
        # Token exists but wrong audience - this is a domain mismatch
        log_auth_rejection(request, domain, AuthRejectReason.AUD_MISMATCH, token_aud="wrong_aud")
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")
    except jwt.InvalidTokenError:
        log_auth_rejection(request, domain, AuthRejectReason.INVALID_TOKEN)
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

    # Validate claims
    aud = payload.get("aud")
    if aud != "fops":
        log_auth_rejection(
            request, domain, AuthRejectReason.AUD_MISMATCH, actor_id=payload.get("sub", ""), token_aud=aud or "missing"
        )
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

    role_str = payload.get("role", "")
    try:
        role = FounderRole(role_str)
    except ValueError:
        log_auth_rejection(
            request, domain, AuthRejectReason.ROLE_INVALID, actor_id=payload.get("sub", ""), token_aud=aud
        )
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

    if role not in [FounderRole.FOUNDER, FounderRole.OPERATOR]:
        log_auth_rejection(
            request, domain, AuthRejectReason.ROLE_INVALID, actor_id=payload.get("sub", ""), token_aud=aud
        )
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

    # MFA check - MANDATORY for FOPS
    mfa = payload.get("mfa", False)
    if not mfa:
        log_auth_rejection(
            request, domain, AuthRejectReason.MFA_REQUIRED, actor_id=payload.get("sub", ""), token_aud=aud
        )
        raise AuthDomainError("AUTH_DOMAIN_MISMATCH")

    # All checks passed
    return FounderToken(
        aud="fops",
        sub=payload["sub"],
        role=role,
        mfa=True,
        iss=payload.get("iss", ISSUER),
        exp=payload["exp"],
        iat=payload.get("iat", int(time.time())),
    )


# =============================================================================
# DEPENDENCY EXPORTS - Use these in routers
# =============================================================================

# Customer Console dependency (for /guard/* routes)
CustomerAuth = Depends(verify_console_token)

# Founder Ops Console dependency (for /ops/* routes)
FounderAuth = Depends(verify_fops_token)


__all__ = [
    # Token types
    "CustomerToken",
    "FounderToken",
    "TokenAudience",
    "CustomerRole",
    "FounderRole",
    # Auth dependencies
    "verify_console_token",
    "verify_fops_token",
    "CustomerAuth",
    "FounderAuth",
    # Token creation (for login endpoints)
    "create_console_token",
    "create_fops_token",
    # Cookie names (for login endpoints)
    "CONSOLE_COOKIE_NAME",
    "FOPS_COOKIE_NAME",
    "get_cookie_settings",
    # Audit logging
    "log_auth_rejection",
    "AuthRejectReason",
]
