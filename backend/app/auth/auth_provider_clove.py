# Layer: L4 — Domain Engine
# Product: system-wide
# AUDIENCE: SHARED
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Clove auth provider — in-house EdDSA/JWKS verification
# Callers: auth_provider.get_human_auth_provider()
# Allowed Imports: L4 (auth_provider, auth_constants)
# Forbidden Imports: L1, L2, L5, L6
# Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md
# capability_id: CAP-006

"""
CloveHumanAuthProvider — Canonical Auth Provider

Implements first-party Clove authentication with:
- EdDSA (Ed25519) JWT verification via JWKS
- Mandatory claim validation using canonical JWTClaim names
- Provider diagnostics for health/status visibility

INVARIANTS:
1. Clove is the canonical human-auth provider.
2. Invalid tokens fail closed with deterministic reason codes.
3. Provider emits HumanPrincipal contract consumed by gateway mapping.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import urlopen

import jwt

from .auth_constants import (
    AuthDenyReason,
    AuthProviderType,
    CLOVE_AUDIENCE,
    CLOVE_ISSUER,
    JWTClaim,
)
from .gateway_metrics import record_token_rejected, record_token_verified
from .auth_provider import AuthProviderError, HumanAuthProvider, HumanPrincipal

logger = logging.getLogger("nova.auth.auth_provider_clove")

# Configuration — env vars accept both CLOVE_* (canonical) and HOC_IDENTITY_* (legacy alias)
_DEFAULT_ISSUER = os.getenv("CLOVE_ISSUER", os.getenv("HOC_IDENTITY_ISSUER", CLOVE_ISSUER))
_DEFAULT_AUDIENCE = os.getenv("CLOVE_AUDIENCE", os.getenv("HOC_IDENTITY_AUDIENCE", CLOVE_AUDIENCE))
_JWKS_URL = os.getenv("CLOVE_JWKS_URL", os.getenv("HOC_IDENTITY_JWKS_URL", "")).strip()
_JWKS_ENDPOINT = os.getenv("CLOVE_JWKS_ENDPOINT", os.getenv("HOC_IDENTITY_JWKS_ENDPOINT", "/.well-known/jwks.json")).strip()
_JWKS_FILE = os.getenv("CLOVE_JWKS_FILE", os.getenv("HOC_IDENTITY_JWKS_FILE", "")).strip()
_JWKS_CACHE_TTL_SECONDS = int(os.getenv("CLOVE_JWKS_CACHE_TTL_SECONDS", os.getenv("HOC_IDENTITY_JWKS_CACHE_TTL_SECONDS", "600")))
_JWKS_TIMEOUT_SECONDS = float(os.getenv("CLOVE_JWKS_TIMEOUT_SECONDS", os.getenv("HOC_IDENTITY_JWKS_TIMEOUT_SECONDS", "5")))


class CloveHumanAuthProvider(HumanAuthProvider):
    """
    Clove auth provider — canonical in-house human authentication.

    Current behavior:
    1. JWKS read from URL or static file with TTL cache.
    2. EdDSA signature verification for bearer tokens.
    3. Mandatory claim validation (all JWTClaim.MANDATORY fields).
    4. Tenant binding validation (`tid` required).

    Session revocation remains gateway-owned via session_store checks.
    """

    def __init__(self) -> None:
        self._issuer = _DEFAULT_ISSUER.strip()
        self._audience = _DEFAULT_AUDIENCE.strip()
        self._jwks_url = self._resolve_jwks_url()
        self._jwks_file = _JWKS_FILE
        self._jwks_cache: Optional[dict[str, Any]] = None
        self._jwks_cache_expires_at: Optional[datetime] = None
        self._last_jwks_fetch_at: Optional[datetime] = None
        self._jwks_cache_state: str = "cold"

    @property
    def provider_type(self) -> AuthProviderType:
        return AuthProviderType.CLOVE

    @property
    def is_configured(self) -> bool:
        has_identity_core = bool(self._issuer and self._audience)
        has_jwks_source = bool(self._jwks_file or self._jwks_url)
        return has_identity_core and has_jwks_source

    def diagnostics(self) -> dict[str, Any]:
        """Provider diagnostics for health/status observability."""
        return {
            "issuer": self._issuer,
            "audience": self._audience,
            "jwks_source": "file" if self._jwks_file else "url",
            "jwks_location": self._jwks_file or self._jwks_url,
            "jwks_cache_status": self._jwks_cache_state,
            "last_jwks_fetch_at": self._iso(self._last_jwks_fetch_at),
            "jwks_cache_expires_at": self._iso(self._jwks_cache_expires_at),
        }

    async def verify_bearer_token(self, token: str) -> HumanPrincipal:
        """
        Verify a Clove EdDSA JWT and return a HumanPrincipal.
        """
        if not self.is_configured:
            record_token_rejected("clove", "not_configured")
            raise AuthProviderError(
                AuthDenyReason.PROVIDER_UNAVAILABLE,
                "Clove provider is not configured",
            )

        try:
            signing_key = self._resolve_signing_key(token)
        except AuthProviderError:
            raise
        except Exception as e:  # pragma: no cover - defensive path
            record_token_rejected("clove", "jwks_resolution_error")
            logger.exception("JWKS key resolution failed: %s", e)
            raise AuthProviderError(AuthDenyReason.INTERNAL_ERROR, "Failed to resolve signing key")

        try:
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["EdDSA"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": sorted(JWTClaim.MANDATORY)},
            )
        except jwt.ExpiredSignatureError:
            record_token_rejected("clove", "expired")
            raise AuthProviderError(AuthDenyReason.TOKEN_EXPIRED, "Token has expired")
        except jwt.InvalidIssuerError:
            record_token_rejected("clove", "issuer_not_allowed")
            raise AuthProviderError(AuthDenyReason.ISSUER_UNTRUSTED, "Issuer not allowed")
        except jwt.InvalidAudienceError:
            record_token_rejected("clove", "invalid_audience")
            raise AuthProviderError(AuthDenyReason.TOKEN_MISSING_CLAIMS, "Audience mismatch")
        except jwt.MissingRequiredClaimError as e:
            record_token_rejected("clove", "missing_claims")
            raise AuthProviderError(
                AuthDenyReason.TOKEN_MISSING_CLAIMS,
                f"Missing required claim: {e.claim}",
            )
        except jwt.InvalidSignatureError:
            record_token_rejected("clove", "invalid_signature")
            raise AuthProviderError(AuthDenyReason.TOKEN_INVALID_SIGNATURE, "Invalid signature")
        except jwt.InvalidTokenError as e:
            record_token_rejected("clove", "malformed")
            raise AuthProviderError(AuthDenyReason.TOKEN_MALFORMED, f"Malformed token: {e}")

        tenant_id = str(payload.get(JWTClaim.TID, "")).strip()
        if not tenant_id:
            record_token_rejected("clove", "tenant_missing")
            raise AuthProviderError(AuthDenyReason.TENANT_MISSING, "Token missing tenant binding")

        iat = self._parse_timestamp(payload.get(JWTClaim.IAT), JWTClaim.IAT)
        exp = self._parse_timestamp(payload.get(JWTClaim.EXP), JWTClaim.EXP)
        roles_or_groups = self._normalize_roles(payload.get(JWTClaim.ROLES))

        record_token_verified("clove")
        return HumanPrincipal(
            subject_user_id=str(payload[JWTClaim.SUB]),
            email=self._as_optional_str(payload.get(JWTClaim.EMAIL)),
            tenant_id=tenant_id,
            account_id=self._as_optional_str(payload.get("account_id")),
            session_id=self._as_optional_str(payload.get(JWTClaim.SID)),
            display_name=self._as_optional_str(payload.get("name") or payload.get("display_name")),
            roles_or_groups=roles_or_groups,
            issued_at=iat,
            expires_at=exp,
            auth_provider=AuthProviderType.CLOVE,
        )

    def _resolve_jwks_url(self) -> str:
        if _JWKS_URL:
            return _JWKS_URL
        if _JWKS_ENDPOINT.startswith(("http://", "https://")):
            return _JWKS_ENDPOINT
        if not _DEFAULT_ISSUER:
            return ""
        return urljoin(f"{_DEFAULT_ISSUER.rstrip('/')}/", _JWKS_ENDPOINT.lstrip("/"))

    def _resolve_signing_key(self, token: str) -> Any:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.InvalidTokenError as e:
            record_token_rejected("clove", "malformed_header")
            raise AuthProviderError(AuthDenyReason.TOKEN_MALFORMED, f"Invalid JWT header: {e}")

        alg = header.get("alg")
        kid = header.get("kid")
        if alg != "EdDSA":
            record_token_rejected("clove", "invalid_alg")
            raise AuthProviderError(
                AuthDenyReason.TOKEN_INVALID_SIGNATURE,
                f"Unsupported alg: {alg}",
            )

        if not kid:
            record_token_rejected("clove", "missing_kid")
            raise AuthProviderError(AuthDenyReason.TOKEN_MALFORMED, "Missing kid in JWT header")

        jwks = self._load_jwks(force_refresh=False)
        jwk = self._find_jwk_by_kid(jwks, kid)
        if jwk is None:
            # One forced refresh retry when kid is unknown.
            jwks = self._load_jwks(force_refresh=True)
            jwk = self._find_jwk_by_kid(jwks, kid)
            if jwk is None:
                record_token_rejected("clove", "kid_not_found")
                raise AuthProviderError(AuthDenyReason.TOKEN_INVALID_SIGNATURE, "Unknown kid")

        try:
            return jwt.PyJWK.from_dict(jwk).key
        except Exception as e:
            record_token_rejected("clove", "jwk_invalid")
            raise AuthProviderError(
                AuthDenyReason.TOKEN_INVALID_SIGNATURE,
                f"Invalid JWK: {e}",
            )

    def _load_jwks(self, force_refresh: bool) -> dict[str, Any]:
        now = datetime.utcnow()
        if (
            not force_refresh
            and self._jwks_cache is not None
            and self._jwks_cache_expires_at is not None
            and now < self._jwks_cache_expires_at
        ):
            return self._jwks_cache

        if self._jwks_file:
            jwks = self._read_jwks_file(self._jwks_file)
        else:
            jwks = self._fetch_jwks_url(self._jwks_url)

        if not isinstance(jwks, dict) or not isinstance(jwks.get("keys"), list):
            raise AuthProviderError(AuthDenyReason.PROVIDER_UNAVAILABLE, "JWKS payload is invalid")

        self._jwks_cache = jwks
        self._last_jwks_fetch_at = now
        self._jwks_cache_expires_at = now + timedelta(seconds=_JWKS_CACHE_TTL_SECONDS)
        self._jwks_cache_state = "warm"
        return jwks

    def _fetch_jwks_url(self, url: str) -> dict[str, Any]:
        if not url:
            raise AuthProviderError(AuthDenyReason.PROVIDER_UNAVAILABLE, "JWKS URL not configured")
        try:
            with urlopen(url, timeout=_JWKS_TIMEOUT_SECONDS) as resp:
                payload = resp.read().decode("utf-8")
            return json.loads(payload)
        except (URLError, OSError, json.JSONDecodeError) as e:
            raise AuthProviderError(AuthDenyReason.PROVIDER_UNAVAILABLE, f"Unable to fetch JWKS: {e}")

    def _read_jwks_file(self, path: str) -> dict[str, Any]:
        try:
            content = Path(path).read_text(encoding="utf-8")
            return json.loads(content)
        except (OSError, json.JSONDecodeError) as e:
            raise AuthProviderError(AuthDenyReason.PROVIDER_UNAVAILABLE, f"Unable to read JWKS file: {e}")

    @staticmethod
    def _find_jwk_by_kid(jwks: dict[str, Any], kid: str) -> Optional[dict[str, Any]]:
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        return None

    @staticmethod
    def _parse_timestamp(value: Any, claim_name: str) -> datetime:
        try:
            return datetime.utcfromtimestamp(int(value))
        except Exception as e:
            raise AuthProviderError(
                AuthDenyReason.TOKEN_MALFORMED,
                f"Invalid {claim_name} claim: {e}",
            )

    @staticmethod
    def _normalize_roles(value: Any) -> tuple[str, ...]:
        if value is None:
            return tuple()
        if isinstance(value, (list, tuple)):
            return tuple(str(v) for v in value)
        return tuple()

    @staticmethod
    def _as_optional_str(value: Any) -> Optional[str]:
        if value is None:
            return None
        rendered = str(value).strip()
        return rendered or None

    @staticmethod
    def _iso(value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None
