"""
Clerk Auth Provider for AOS

This module provides Clerk-based authentication and authorization.
It replaces the previous Keycloak OIDC and stub auth implementations.

Clerk provides:
- User management with roles via public_metadata
- JWT verification via JWKS
- M2M (machine-to-machine) authentication support

Usage:
    from app.auth.clerk_provider import ClerkAuthProvider, get_clerk_provider

    provider = get_clerk_provider()
    user_info = await provider.get_user_roles(user_id, tenant_id)
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from functools import lru_cache

import httpx
import jwt
from jwt import PyJWKClient

logger = logging.getLogger("nova.auth.clerk")

# Clerk configuration
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_ISSUER_URL = os.getenv("CLERK_ISSUER_URL", "")
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", "")
CLERK_API_URL = "https://api.clerk.com/v1"

# Production safety
RBAC_ENFORCE = os.getenv("RBAC_ENFORCE", "false").lower() == "true"


@dataclass
class ClerkUser:
    """Represents a Clerk user with role information."""
    user_id: str
    email: Optional[str]
    roles: List[str]
    max_approval_level: int
    tenant_id: Optional[str]
    metadata: Dict[str, Any]


class ClerkAuthError(Exception):
    """Raised when Clerk authentication fails."""
    def __init__(self, message: str, user_id: Optional[str] = None):
        self.message = message
        self.user_id = user_id
        super().__init__(message)


class ClerkAuthProvider:
    """
    Clerk authentication provider for AOS.

    Handles:
    - User role lookup via Clerk API
    - JWT token verification
    - Role-to-level mapping for RBAC
    """

    def __init__(
        self,
        secret_key: str = CLERK_SECRET_KEY,
        issuer_url: str = CLERK_ISSUER_URL,
        jwks_url: str = CLERK_JWKS_URL,
    ):
        self.secret_key = secret_key
        self.issuer_url = issuer_url
        self.jwks_url = jwks_url or f"{issuer_url}/.well-known/jwks.json"
        self._jwk_client: Optional[PyJWKClient] = None
        self._http_client: Optional[httpx.AsyncClient] = None

        # Role to approval level mapping
        self.role_levels = {
            "owner": 5,
            "admin": 5,
            "manager": 4,
            "policy_admin": 4,
            "director": 4,
            "team_lead": 3,
            "senior_engineer": 3,
            "tech_lead": 3,
            "team_member": 2,
            "engineer": 2,
            "developer": 2,
            "guest": 1,
            "readonly": 1,
        }

    @property
    def is_configured(self) -> bool:
        """Check if Clerk is properly configured."""
        return bool(self.secret_key and self.issuer_url)

    def _get_jwk_client(self) -> PyJWKClient:
        """Get or create JWK client for token verification."""
        if self._jwk_client is None:
            self._jwk_client = PyJWKClient(self.jwks_url)
        return self._jwk_client

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.secret_key}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
        return self._http_client

    async def close(self):
        """Close HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify a Clerk JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload

        Raises:
            ClerkAuthError: If token is invalid
        """
        try:
            jwk_client = self._get_jwk_client()
            signing_key = jwk_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self.issuer_url,
                options={"verify_aud": False},  # Clerk doesn't always set aud
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise ClerkAuthError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ClerkAuthError(f"Invalid token: {e}")

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Fetch user details from Clerk API.

        Args:
            user_id: Clerk user ID (e.g., "user_xxx")

        Returns:
            User data from Clerk API

        Raises:
            ClerkAuthError: If user not found or API error
        """
        client = await self._get_http_client()

        try:
            response = await client.get(f"{CLERK_API_URL}/users/{user_id}")

            if response.status_code == 404:
                raise ClerkAuthError(f"User {user_id} not found", user_id)

            response.raise_for_status()
            return response.json()

        except httpx.RequestError as e:
            logger.error(f"Clerk API error: {e}")
            raise ClerkAuthError(f"Clerk API unavailable: {e}", user_id)

    def _extract_roles(self, user_data: Dict[str, Any]) -> List[str]:
        """
        Extract roles from Clerk user metadata.

        Clerk stores custom data in:
        - public_metadata (visible to frontend)
        - private_metadata (backend only)

        We look for roles in public_metadata.roles or private_metadata.roles
        """
        roles = []

        # Check public_metadata
        public_meta = user_data.get("public_metadata", {})
        if "roles" in public_meta:
            roles.extend(public_meta["roles"])
        if "role" in public_meta:
            roles.append(public_meta["role"])

        # Check private_metadata (takes precedence for security-sensitive roles)
        private_meta = user_data.get("private_metadata", {})
        if "roles" in private_meta:
            roles.extend(private_meta["roles"])
        if "role" in private_meta:
            roles.append(private_meta["role"])

        # Deduplicate and normalize
        return list(set(r.lower() for r in roles if r))

    def _extract_tenant(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Extract tenant ID from user metadata."""
        # Check organization memberships first
        org_memberships = user_data.get("organization_memberships", [])
        if org_memberships:
            # Return first org as tenant
            return org_memberships[0].get("organization", {}).get("id")

        # Fall back to metadata
        public_meta = user_data.get("public_metadata", {})
        return public_meta.get("tenant_id")

    def _roles_to_level(self, roles: List[str]) -> int:
        """Convert roles to maximum approval level."""
        if not roles:
            return 1  # Default to guest level

        max_level = 1
        for role in roles:
            role_lower = role.lower()
            if role_lower in self.role_levels:
                max_level = max(max_level, self.role_levels[role_lower])

        return max_level

    async def get_user_roles(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> ClerkUser:
        """
        Get user roles and approval level from Clerk.

        This is the main method used by RBAC integration.

        Args:
            user_id: Clerk user ID
            tenant_id: Optional tenant context (for multi-tenant checks)

        Returns:
            ClerkUser with roles and approval level

        Raises:
            ClerkAuthError: If user not found or API error
        """
        if not self.is_configured:
            if RBAC_ENFORCE:
                # Fail-closed: Production requires Clerk to be configured
                logger.error("Clerk not configured but RBAC_ENFORCE=true")
                raise ClerkAuthError(
                    "Clerk auth required but not configured (set CLERK_SECRET_KEY and CLERK_ISSUER_URL)",
                    user_id
                )
            # Return mock for development when Clerk is not configured
            logger.warning("Clerk not configured, returning mock roles - NOT FOR PRODUCTION")
            return ClerkUser(
                user_id=user_id,
                email=None,
                roles=["team_member"],
                max_approval_level=3,
                tenant_id=tenant_id,
                metadata={},
            )

        user_data = await self.get_user(user_id)

        roles = self._extract_roles(user_data)
        user_tenant = self._extract_tenant(user_data)

        # If tenant_id is specified, verify user belongs to it
        if tenant_id and user_tenant and user_tenant != tenant_id:
            logger.warning(
                f"User {user_id} tenant mismatch: expected {tenant_id}, got {user_tenant}"
            )
            # Could raise error here for strict tenant isolation

        return ClerkUser(
            user_id=user_id,
            email=user_data.get("email_addresses", [{}])[0].get("email_address"),
            roles=roles,
            max_approval_level=self._roles_to_level(roles),
            tenant_id=user_tenant or tenant_id,
            metadata={
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "image_url": user_data.get("image_url"),
            },
        )

    async def get_user_by_token(self, token: str) -> ClerkUser:
        """
        Get user from a JWT token.

        Args:
            token: Clerk JWT token

        Returns:
            ClerkUser with roles and approval level
        """
        payload = self.verify_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise ClerkAuthError("Token missing subject (user_id)")

        return await self.get_user_roles(user_id)


# Singleton instance
_clerk_provider: Optional[ClerkAuthProvider] = None


def get_clerk_provider() -> ClerkAuthProvider:
    """Get or create the Clerk auth provider singleton."""
    global _clerk_provider
    if _clerk_provider is None:
        _clerk_provider = ClerkAuthProvider()
    return _clerk_provider


async def get_user_roles_from_clerk(
    user_id: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to get user roles from Clerk.

    Returns dict compatible with existing RBAC code:
    {
        "user_id": "...",
        "roles": ["admin", "team_lead"],
        "max_approval_level": 4,
        "tenant_id": "..."
    }
    """
    provider = get_clerk_provider()
    user = await provider.get_user_roles(user_id, tenant_id)

    return {
        "user_id": user.user_id,
        "roles": user.roles,
        "max_approval_level": user.max_approval_level,
        "tenant_id": user.tenant_id,
    }
