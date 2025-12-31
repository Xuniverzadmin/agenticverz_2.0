# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: JWT token validation and parsing
# Callers: middleware, API routes
# Allowed Imports: None
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Auth Infrastructure

"""
JWT/OIDC Authentication for AOS Traces API

M8 Deliverable: Production-ready JWT authentication with JWKS verification.

Features:
- JWKS (JSON Web Key Set) verification with caching
- Support for RS256 and ES256 algorithms
- Automatic key rotation handling
- Tenant isolation via JWT claims
- Rate limit tier extraction from claims
"""

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# JWT libraries
try:
    import jwt
    from jwt import PyJWKClient, PyJWKClientError

    HAS_PYJWT = True
except ImportError:
    HAS_PYJWT = False
    jwt = None
    PyJWKClient = None
    PyJWKClientError = Exception

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None

logger = logging.getLogger(__name__)


@dataclass
class JWTConfig:
    """Configuration for JWT authentication."""

    # OIDC Provider settings
    issuer_url: str = field(default_factory=lambda: os.getenv("OIDC_ISSUER_URL", ""))
    jwks_uri: str = field(default_factory=lambda: os.getenv("OIDC_JWKS_URI", ""))
    audience: str = field(default_factory=lambda: os.getenv("OIDC_AUDIENCE", "aos-api"))
    client_id: str = field(default_factory=lambda: os.getenv("OIDC_CLIENT_ID", ""))

    # Validation settings
    algorithms: List[str] = field(default_factory=lambda: ["RS256", "ES256"])
    verify_exp: bool = True
    verify_aud: bool = True
    verify_iss: bool = True

    # Cache settings
    jwks_cache_ttl: int = 3600  # 1 hour

    # Claim mappings
    tenant_claim: str = "tenant_id"
    roles_claim: str = "roles"
    rate_limit_claim: str = "rate_limit_tier"

    # Fallback for development
    allow_dev_token: bool = field(default_factory=lambda: os.getenv("JWT_ALLOW_DEV_TOKEN", "false").lower() == "true")
    dev_token_secret: str = field(default_factory=lambda: os.getenv("JWT_DEV_SECRET", "dev-secret-not-for-production"))

    def __post_init__(self):
        # Auto-discover JWKS URI from issuer if not set
        if self.issuer_url and not self.jwks_uri:
            self.jwks_uri = f"{self.issuer_url.rstrip('/')}/.well-known/jwks.json"


@dataclass
class TokenPayload:
    """Parsed and validated JWT payload."""

    sub: str  # Subject (user ID)
    tenant_id: str
    roles: List[str]
    rate_limit_tier: str
    exp: datetime
    iat: datetime
    iss: str
    aud: str
    raw_claims: Dict[str, Any]

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles

    @property
    def can_write_traces(self) -> bool:
        return "traces:write" in self.roles or self.is_admin

    @property
    def can_read_traces(self) -> bool:
        return "traces:read" in self.roles or self.can_write_traces


class JWKSCache:
    """Cached JWKS client with automatic refresh."""

    def __init__(self, config: JWTConfig):
        self.config = config
        self._client: Optional[PyJWKClient] = None
        self._last_refresh: float = 0
        self._keys: Dict[str, Any] = {}

    def get_client(self) -> PyJWKClient:
        """Get JWKS client, refreshing if needed."""
        if not HAS_PYJWT:
            raise RuntimeError("PyJWT not installed. Run: pip install PyJWT[crypto]")

        now = time.time()
        if self._client is None or (now - self._last_refresh) > self.config.jwks_cache_ttl:
            self._client = PyJWKClient(self.config.jwks_uri, cache_keys=True, lifespan=self.config.jwks_cache_ttl)
            self._last_refresh = now
            logger.info(f"Refreshed JWKS from {self.config.jwks_uri}")

        return self._client

    def get_signing_key(self, token: str) -> Any:
        """Get signing key for a token."""
        client = self.get_client()
        try:
            return client.get_signing_key_from_jwt(token)
        except PyJWKClientError as e:
            logger.warning(f"JWKS key lookup failed: {e}")
            # Force refresh and retry once
            self._client = None
            client = self.get_client()
            return client.get_signing_key_from_jwt(token)


class JWTAuthDependency:
    """FastAPI dependency for JWT authentication."""

    def __init__(self, config: Optional[JWTConfig] = None):
        self.config = config or JWTConfig()
        self._jwks_cache: Optional[JWKSCache] = None
        self._security = HTTPBearer(auto_error=False)

    @property
    def jwks_cache(self) -> JWKSCache:
        if self._jwks_cache is None:
            self._jwks_cache = JWKSCache(self.config)
        return self._jwks_cache

    async def __call__(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Security(HTTPBearer(auto_error=False)),
    ) -> TokenPayload:
        """Authenticate request and return token payload."""

        # Check for Bearer token
        if credentials is None:
            # Try X-API-Key header as fallback
            api_key = request.headers.get("X-API-Key")
            if api_key:
                return self._handle_api_key(api_key)
            raise HTTPException(
                status_code=401, detail="Missing authentication token", headers={"WWW-Authenticate": "Bearer"}
            )

        token = credentials.credentials

        # Handle development tokens
        if self.config.allow_dev_token and token.startswith("dev:"):
            return self._verify_dev_token(token)

        # Verify JWT with JWKS
        return await self._verify_jwt(token)

    def _handle_api_key(self, api_key: str) -> TokenPayload:
        """Handle legacy API key authentication."""
        # For backwards compatibility with existing API keys
        # In production, this should validate against a key store
        expected_key = os.getenv("AOS_API_KEY", "")
        if api_key != expected_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Return a system token payload for API key auth
        now = datetime.utcnow()
        return TokenPayload(
            sub="system:api-key",
            tenant_id=os.getenv("DEFAULT_TENANT", "default"),
            roles=["traces:read", "traces:write"],
            rate_limit_tier="standard",
            exp=now + timedelta(hours=24),
            iat=now,
            iss="aos-api-key",
            aud=self.config.audience,
            raw_claims={"auth_type": "api_key"},
        )

    def _verify_dev_token(self, token: str) -> TokenPayload:
        """Verify development token (HS256 signed)."""
        if not self.config.allow_dev_token:
            raise HTTPException(status_code=401, detail="Development tokens not allowed")

        if not HAS_PYJWT:
            raise HTTPException(status_code=500, detail="PyJWT not installed")

        # Strip dev: prefix
        actual_token = token[4:]

        try:
            payload = jwt.decode(
                actual_token,
                self.config.dev_token_secret,
                algorithms=["HS256"],
                options={"verify_exp": self.config.verify_exp},
            )
            return self._parse_claims(payload)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    async def _verify_jwt(self, token: str) -> TokenPayload:
        """Verify JWT against JWKS."""
        if not HAS_PYJWT:
            raise HTTPException(status_code=500, detail="PyJWT not installed")

        try:
            # Get signing key from JWKS
            signing_key = self.jwks_cache.get_signing_key(token)

            # Decode and verify
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=self.config.algorithms,
                audience=self.config.audience if self.config.verify_aud else None,
                issuer=self.config.issuer_url if self.config.verify_iss else None,
                options={
                    "verify_exp": self.config.verify_exp,
                    "verify_aud": self.config.verify_aud,
                    "verify_iss": self.config.verify_iss,
                },
            )

            return self._parse_claims(payload)

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token expired",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Token expired"'},
            )
        except jwt.InvalidAudienceError:
            raise HTTPException(
                status_code=401,
                detail="Invalid audience",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Invalid audience"'},
            )
        except jwt.InvalidIssuerError:
            raise HTTPException(
                status_code=401,
                detail="Invalid issuer",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Invalid issuer"'},
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})
        except Exception as e:
            logger.error(f"JWT verification error: {e}")
            raise HTTPException(status_code=500, detail="Authentication service error")

    def _parse_claims(self, payload: Dict[str, Any]) -> TokenPayload:
        """Parse JWT claims into TokenPayload."""
        now = datetime.utcnow()

        # Extract standard claims
        sub = payload.get("sub", "")
        exp_ts = payload.get("exp", 0)
        iat_ts = payload.get("iat", time.time())
        iss = payload.get("iss", "")
        aud = payload.get("aud", "")
        if isinstance(aud, list):
            aud = aud[0] if aud else ""

        # Extract custom claims
        tenant_id = payload.get(self.config.tenant_claim, "default")
        roles = payload.get(self.config.roles_claim, [])
        if isinstance(roles, str):
            roles = [roles]
        rate_limit_tier = payload.get(self.config.rate_limit_claim, "standard")

        return TokenPayload(
            sub=sub,
            tenant_id=tenant_id,
            roles=roles,
            rate_limit_tier=rate_limit_tier,
            exp=datetime.fromtimestamp(exp_ts) if exp_ts else now + timedelta(hours=1),
            iat=datetime.fromtimestamp(iat_ts),
            iss=iss,
            aud=aud,
            raw_claims=payload,
        )


# Global instance
_jwt_auth: Optional[JWTAuthDependency] = None


def get_jwt_auth() -> JWTAuthDependency:
    """Get or create global JWT auth dependency."""
    global _jwt_auth
    if _jwt_auth is None:
        _jwt_auth = JWTAuthDependency()
    return _jwt_auth


async def verify_token(token: str, config: Optional[JWTConfig] = None) -> TokenPayload:
    """Standalone token verification function."""
    auth = JWTAuthDependency(config)

    # Create a mock credentials object
    from fastapi.security import HTTPAuthorizationCredentials

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Create a minimal mock request
    class MockRequest:
        headers = {}

    return await auth(MockRequest(), credentials)


# Utility functions for generating dev tokens
def create_dev_token(
    sub: str,
    tenant_id: str = "default",
    roles: Optional[List[str]] = None,
    rate_limit_tier: str = "standard",
    expires_in: int = 3600,
    secret: Optional[str] = None,
) -> str:
    """Create a development token for testing."""
    if not HAS_PYJWT:
        raise RuntimeError("PyJWT not installed")

    now = datetime.utcnow()
    payload = {
        "sub": sub,
        "tenant_id": tenant_id,
        "roles": roles or ["traces:read", "traces:write"],
        "rate_limit_tier": rate_limit_tier,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "iss": "aos-dev",
        "aud": "aos-api",
    }

    secret = secret or os.getenv("JWT_DEV_SECRET", "dev-secret-not-for-production")
    token = jwt.encode(payload, secret, algorithm="HS256")

    return f"dev:{token}"
