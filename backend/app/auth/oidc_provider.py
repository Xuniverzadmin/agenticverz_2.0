# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: external
#   Execution: async
# Role: OIDC authentication provider adapter
# Callers: auth services
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: Auth Integration

"""
OIDC Provider Integration for Keycloak

Provides JWT validation using JWKS (JSON Web Key Set) from Keycloak.
Extracts roles from Keycloak-specific token claims.

Configuration (environment variables):
    OIDC_ISSUER_URL: Keycloak realm URL (e.g., https://auth-dev.xuniverz.com/realms/agentiverz-dev)
    OIDC_CLIENT_ID: Client ID for audience validation
    OIDC_VERIFY_SSL: Whether to verify SSL certificates (default: true)

Usage:
    from app.auth.oidc_provider import validate_token, get_roles_from_token

    claims = await validate_token(token)
    roles = get_roles_from_token(claims)
"""

import logging
import os
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import httpx
import jwt
from jwt import PyJWKClient, PyJWKClientError

logger = logging.getLogger("nova.auth.oidc")

# Configuration
OIDC_ISSUER_URL = os.getenv("OIDC_ISSUER_URL", "")
OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "aos-backend")
OIDC_VERIFY_SSL = os.getenv("OIDC_VERIFY_SSL", "true").lower() == "true"
OIDC_ENABLED = bool(OIDC_ISSUER_URL)

# Cache JWKS for 1 hour
_jwks_client: Optional[PyJWKClient] = None
_jwks_client_timestamp: float = 0
JWKS_CACHE_TTL = 3600  # 1 hour


class OIDCError(Exception):
    """Base exception for OIDC-related errors."""

    pass


class TokenValidationError(OIDCError):
    """Raised when token validation fails."""

    def __init__(self, message: str, error_code: str = "invalid_token"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


def _get_jwks_client() -> PyJWKClient:
    """
    Get or create a JWKS client with caching.

    Returns:
        PyJWKClient configured for the OIDC issuer

    Raises:
        OIDCError: If OIDC is not configured
    """
    global _jwks_client, _jwks_client_timestamp

    if not OIDC_ISSUER_URL:
        raise OIDCError("OIDC_ISSUER_URL not configured")

    now = time.time()
    if _jwks_client is None or (now - _jwks_client_timestamp) > JWKS_CACHE_TTL:
        jwks_url = f"{OIDC_ISSUER_URL}/protocol/openid-connect/certs"
        logger.info(f"Initializing JWKS client from {jwks_url}")

        _jwks_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=JWKS_CACHE_TTL)
        _jwks_client_timestamp = now

    return _jwks_client


@lru_cache(maxsize=100)
def _get_oidc_config() -> Dict[str, Any]:
    """
    Fetch OIDC discovery document (cached).

    Returns:
        OIDC configuration from .well-known/openid-configuration
    """
    if not OIDC_ISSUER_URL:
        return {}

    discovery_url = f"{OIDC_ISSUER_URL}/.well-known/openid-configuration"
    try:
        with httpx.Client(verify=OIDC_VERIFY_SSL, timeout=10.0) as client:
            response = client.get(discovery_url)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch OIDC discovery: {e}")
        return {}


def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate a JWT token using JWKS from the OIDC provider.

    Args:
        token: The JWT token to validate

    Returns:
        Decoded token claims

    Raises:
        TokenValidationError: If token is invalid, expired, or signature fails
    """
    if not OIDC_ENABLED:
        # Fall back to unverified decoding if OIDC not configured
        logger.warning("OIDC not configured, decoding token without verification")
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except jwt.InvalidTokenError as e:
            raise TokenValidationError(f"Invalid token format: {e}")

    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode with full verification
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "RS384", "RS512"],
            audience=OIDC_CLIENT_ID,
            issuer=OIDC_ISSUER_URL,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
            },
        )

        logger.debug(f"Token validated successfully for sub={claims.get('sub')}")
        return claims

    except jwt.ExpiredSignatureError:
        raise TokenValidationError("Token has expired", "token_expired")
    except jwt.InvalidAudienceError:
        raise TokenValidationError("Invalid audience", "invalid_audience")
    except jwt.InvalidIssuerError:
        raise TokenValidationError("Invalid issuer", "invalid_issuer")
    except PyJWKClientError as e:
        logger.error(f"JWKS client error: {e}")
        raise TokenValidationError(f"Failed to fetch signing key: {e}", "jwks_error")
    except jwt.InvalidTokenError as e:
        raise TokenValidationError(f"Invalid token: {e}", "invalid_token")


def get_roles_from_token(claims: Dict[str, Any]) -> List[str]:
    """
    Extract roles from Keycloak token claims.

    Keycloak stores roles in multiple locations:
    - realm_access.roles: Realm-level roles
    - resource_access.<client_id>.roles: Client-specific roles
    - roles: Sometimes used in custom mappers

    Args:
        claims: Decoded JWT claims

    Returns:
        List of roles (deduplicated)
    """
    roles = set()

    # 1. Check realm_access.roles (Keycloak realm roles)
    realm_access = claims.get("realm_access", {})
    realm_roles = realm_access.get("roles", [])
    roles.update(realm_roles)

    # 2. Check resource_access.<client>.roles (client-specific roles)
    resource_access = claims.get("resource_access", {})
    client_access = resource_access.get(OIDC_CLIENT_ID, {})
    client_roles = client_access.get("roles", [])
    roles.update(client_roles)

    # 3. Check top-level roles claim (custom mapper or simple setup)
    top_level_roles = claims.get("roles", [])
    if isinstance(top_level_roles, list):
        roles.update(top_level_roles)
    elif isinstance(top_level_roles, str):
        roles.add(top_level_roles)

    # 4. Check groups claim (often used for role-like groupings)
    groups = claims.get("groups", [])
    # Convert group paths to roles (e.g., "/admin" -> "admin")
    for group in groups:
        if group.startswith("/"):
            roles.add(group[1:].replace("/", "_"))
        else:
            roles.add(group)

    return list(roles)


def get_user_info_from_token(claims: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user information from token claims.

    Args:
        claims: Decoded JWT claims

    Returns:
        Dict with user info (sub, email, name, etc.)
    """
    return {
        "sub": claims.get("sub"),
        "email": claims.get("email"),
        "email_verified": claims.get("email_verified", False),
        "name": claims.get("name"),
        "preferred_username": claims.get("preferred_username"),
        "given_name": claims.get("given_name"),
        "family_name": claims.get("family_name"),
    }


def validate_and_extract(token: str) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate token and extract roles in one call.

    Args:
        token: The JWT token

    Returns:
        Tuple of (claims, roles)

    Raises:
        TokenValidationError: If validation fails
    """
    claims = validate_token(token)
    roles = get_roles_from_token(claims)
    return claims, roles


# =============================================================================
# B04 FIX: Role mapping moved to L4 RBACEngine
# =============================================================================
# Previously: Local KEYCLOAK_TO_AOS_ROLE_MAP and map_keycloak_roles_to_aos()
# Now: Delegates to L4 RBACEngine.map_external_roles_to_aos()
# Reference: PIN-254 Phase B Fix


def map_keycloak_roles_to_aos(keycloak_roles: List[str]) -> List[str]:
    """
    Map Keycloak roles to AOS RBAC roles.

    B04 FIX: Delegates to L4 RBACEngine for domain authority.
    L3 no longer contains role mapping logic.

    Args:
        keycloak_roles: Roles from Keycloak token

    Returns:
        Mapped AOS roles
    """
    from app.auth.rbac_engine import map_external_roles_to_aos

    return map_external_roles_to_aos(keycloak_roles)
