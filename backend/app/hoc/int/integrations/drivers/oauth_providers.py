# capability_id: CAP-018
# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: external
#   Execution: async
# Role: OAuth provider adapters (Google, GitHub, etc)
# Callers: auth services
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: Auth Integration

"""
OAuth2 Providers - Google & Azure

Provides OAuth2 authentication flow for customer onboarding.

Configuration (environment variables):
    GOOGLE_CLIENT_ID: Google OAuth client ID
    GOOGLE_CLIENT_SECRET: Google OAuth client secret
    AZURE_CLIENT_ID: Azure AD client ID
    AZURE_CLIENT_SECRET: Azure AD client secret
    AZURE_TENANT_ID: Azure AD tenant ID (or "common" for multi-tenant)
    OAUTH_REDIRECT_BASE: Base URL for OAuth redirects (e.g., https://agenticverz.com)
"""

import logging
import os
import secrets
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx

logger = logging.getLogger("nova.auth.oauth")

# ============== Configuration ==============

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "common")
OAUTH_REDIRECT_BASE = os.getenv("OAUTH_REDIRECT_BASE", "https://agenticverz.com")

# OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

AZURE_AUTH_URL = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/authorize"
AZURE_TOKEN_URL = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
AZURE_USERINFO_URL = "https://graph.microsoft.com/v1.0/me"


@dataclass
class OAuthUserInfo:
    """Standardized user info from OAuth providers."""

    provider: str  # google, azure
    provider_user_id: str  # sub or oid
    email: str
    email_verified: bool
    name: Optional[str]
    given_name: Optional[str]
    family_name: Optional[str]
    picture: Optional[str]
    raw_data: Dict[str, Any]


class OAuthError(Exception):
    """OAuth-related error."""

    def __init__(self, message: str, error_code: str = "oauth_error"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


# ============== Google OAuth ==============


class GoogleOAuthProvider:
    """Google OAuth2 provider."""

    def __init__(self):
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            logger.warning("Google OAuth not configured")
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.redirect_uri = f"{OAUTH_REDIRECT_BASE}/api/v1/auth/callback/google"

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_authorization_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """
        Get the Google OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Tuple of (authorization_url, state)
        """
        if not self.is_configured:
            raise OAuthError("Google OAuth not configured", "not_configured")

        state = state or secrets.token_urlsafe(32)

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }

        url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
        return url, state

    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback

        Returns:
            Token response including access_token
        """
        if not self.is_configured:
            raise OAuthError("Google OAuth not configured", "not_configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                },
            )

            if response.status_code != 200:
                logger.error(f"Google token exchange failed: {response.text}")
                raise OAuthError(f"Token exchange failed: {response.status_code}", "token_error")

            return response.json()

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get user information from Google.

        Args:
            access_token: Access token from token exchange

        Returns:
            Standardized user info
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                logger.error(f"Google userinfo failed: {response.text}")
                raise OAuthError(f"Failed to get user info: {response.status_code}", "userinfo_error")

            data = response.json()

            return OAuthUserInfo(
                provider="google",
                provider_user_id=data.get("sub", ""),
                email=data.get("email", ""),
                email_verified=data.get("email_verified", False),
                name=data.get("name"),
                given_name=data.get("given_name"),
                family_name=data.get("family_name"),
                picture=data.get("picture"),
                raw_data=data,
            )


# ============== Azure OAuth ==============


class AzureOAuthProvider:
    """Azure AD OAuth2 provider."""

    def __init__(self):
        if not AZURE_CLIENT_ID or not AZURE_CLIENT_SECRET:
            logger.warning("Azure OAuth not configured")
        self.client_id = AZURE_CLIENT_ID
        self.client_secret = AZURE_CLIENT_SECRET
        self.tenant_id = AZURE_TENANT_ID
        self.redirect_uri = f"{OAUTH_REDIRECT_BASE}/api/v1/auth/callback/azure"

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_authorization_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """
        Get the Azure OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Tuple of (authorization_url, state)
        """
        if not self.is_configured:
            raise OAuthError("Azure OAuth not configured", "not_configured")

        state = state or secrets.token_urlsafe(32)

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile User.Read",
            "state": state,
            "response_mode": "query",
        }

        url = f"{AZURE_AUTH_URL}?{urlencode(params)}"
        return url, state

    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback

        Returns:
            Token response including access_token
        """
        if not self.is_configured:
            raise OAuthError("Azure OAuth not configured", "not_configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                AZURE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                    "scope": "openid email profile User.Read",
                },
            )

            if response.status_code != 200:
                logger.error(f"Azure token exchange failed: {response.text}")
                raise OAuthError(f"Token exchange failed: {response.status_code}", "token_error")

            return response.json()

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get user information from Microsoft Graph.

        Args:
            access_token: Access token from token exchange

        Returns:
            Standardized user info
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                AZURE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                logger.error(f"Azure userinfo failed: {response.text}")
                raise OAuthError(f"Failed to get user info: {response.status_code}", "userinfo_error")

            data = response.json()

            return OAuthUserInfo(
                provider="azure",
                provider_user_id=data.get("id", ""),
                email=data.get("mail") or data.get("userPrincipalName", ""),
                email_verified=True,  # Azure always verifies emails
                name=data.get("displayName"),
                given_name=data.get("givenName"),
                family_name=data.get("surname"),
                picture=None,  # Requires separate Graph API call
                raw_data=data,
            )


# ============== Provider Factory ==============

_google_provider: Optional[GoogleOAuthProvider] = None
_azure_provider: Optional[AzureOAuthProvider] = None


def get_google_provider() -> GoogleOAuthProvider:
    """Get Google OAuth provider singleton."""
    global _google_provider
    if _google_provider is None:
        _google_provider = GoogleOAuthProvider()
    return _google_provider


def get_azure_provider() -> AzureOAuthProvider:
    """Get Azure OAuth provider singleton."""
    global _azure_provider
    if _azure_provider is None:
        _azure_provider = AzureOAuthProvider()
    return _azure_provider
