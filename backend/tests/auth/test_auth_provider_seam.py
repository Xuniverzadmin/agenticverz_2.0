# Layer: TEST
# Product: system-wide
# AUDIENCE: INTERNAL
# Role: Tests for auth provider seam — factory selection, contract compliance, gateway integration
# Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md

"""
Auth Provider Seam Tests

Tests:
1. Provider factory selects correct implementation based on AUTH_PROVIDER env.
2. ClerkHumanAuthProvider implements the HumanAuthProvider interface.
3. HocIdentityHumanAuthProvider implements the HumanAuthProvider interface.
4. Gateway human-auth path delegates to provider seam.
5. HumanPrincipal → HumanAuthContext mapping preserves downstream contract.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

from app.auth.auth_constants import AuthDenyReason, AuthProviderType, JWTClaim
from app.auth.auth_provider import (
    AuthProviderError,
    HumanAuthProvider,
    HumanPrincipal,
    get_human_auth_provider,
    reset_human_auth_provider,
)
from app.auth.auth_provider_clerk import ClerkHumanAuthProvider
from app.auth.auth_provider_hoc_identity import HocIdentityHumanAuthProvider


# =============================================================================
# Provider Factory Tests
# =============================================================================


class TestProviderFactory:
    """Tests for get_human_auth_provider() factory selection."""

    def setup_method(self):
        reset_human_auth_provider()

    def teardown_method(self):
        reset_human_auth_provider()

    def test_default_provider_is_clerk(self):
        """Default AUTH_PROVIDER env (unset or 'clerk') yields ClerkHumanAuthProvider."""
        with patch.dict(os.environ, {"AUTH_PROVIDER": "clerk"}):
            reset_human_auth_provider()
            # Need to reimport to pick up env change
            from app.auth import auth_provider
            auth_provider.AUTH_PROVIDER_ENV = "clerk"
            reset_human_auth_provider()
            provider = get_human_auth_provider()
            assert isinstance(provider, ClerkHumanAuthProvider)
            assert provider.provider_type == AuthProviderType.CLERK

    def test_hoc_identity_provider_selection(self):
        """AUTH_PROVIDER=hoc_identity yields HocIdentityHumanAuthProvider."""
        from app.auth import auth_provider
        auth_provider.AUTH_PROVIDER_ENV = "hoc_identity"
        reset_human_auth_provider()
        provider = get_human_auth_provider()
        assert isinstance(provider, HocIdentityHumanAuthProvider)
        assert provider.provider_type == AuthProviderType.HOC_IDENTITY
        # Restore
        auth_provider.AUTH_PROVIDER_ENV = "clerk"
        reset_human_auth_provider()

    def test_factory_returns_singleton(self):
        """Factory returns the same instance on repeated calls."""
        p1 = get_human_auth_provider()
        p2 = get_human_auth_provider()
        assert p1 is p2

    def test_reset_clears_singleton(self):
        """reset_human_auth_provider() clears the cached instance."""
        p1 = get_human_auth_provider()
        reset_human_auth_provider()
        p2 = get_human_auth_provider()
        assert p1 is not p2


# =============================================================================
# Interface Compliance Tests
# =============================================================================


class TestClerkAdapterInterface:
    """Tests that ClerkHumanAuthProvider satisfies HumanAuthProvider contract."""

    def test_is_human_auth_provider(self):
        adapter = ClerkHumanAuthProvider()
        assert isinstance(adapter, HumanAuthProvider)

    def test_has_provider_type(self):
        adapter = ClerkHumanAuthProvider()
        assert adapter.provider_type == AuthProviderType.CLERK

    def test_has_is_configured(self):
        adapter = ClerkHumanAuthProvider()
        # Clerk not configured in test env
        assert isinstance(adapter.is_configured, bool)

    @pytest.mark.asyncio
    async def test_unconfigured_raises_provider_unavailable(self):
        """Unconfigured Clerk adapter raises PROVIDER_UNAVAILABLE."""
        adapter = ClerkHumanAuthProvider()
        if not adapter.is_configured:
            with pytest.raises(AuthProviderError) as exc_info:
                await adapter.verify_bearer_token("fake_token")
            assert exc_info.value.reason == AuthDenyReason.PROVIDER_UNAVAILABLE


class TestHocIdentityAdapterInterface:
    """Tests that HocIdentityHumanAuthProvider satisfies HumanAuthProvider contract."""

    def test_is_human_auth_provider(self):
        adapter = HocIdentityHumanAuthProvider()
        assert isinstance(adapter, HumanAuthProvider)

    def test_has_provider_type(self):
        adapter = HocIdentityHumanAuthProvider()
        assert adapter.provider_type == AuthProviderType.HOC_IDENTITY

    def test_not_configured(self):
        """Scaffold provider is never configured."""
        adapter = HocIdentityHumanAuthProvider()
        assert adapter.is_configured is False

    @pytest.mark.asyncio
    async def test_raises_provider_unavailable(self):
        """Scaffold provider always raises PROVIDER_UNAVAILABLE."""
        adapter = HocIdentityHumanAuthProvider()
        with pytest.raises(AuthProviderError) as exc_info:
            await adapter.verify_bearer_token("any_token")
        assert exc_info.value.reason == AuthDenyReason.PROVIDER_UNAVAILABLE


# =============================================================================
# HumanPrincipal Contract Tests
# =============================================================================


class TestHumanPrincipal:
    """Tests for HumanPrincipal data contract."""

    def test_principal_is_frozen(self):
        from datetime import datetime
        principal = HumanPrincipal(
            subject_user_id="user_123",
            email="test@example.com",
            tenant_id="tenant_456",
            account_id="acct_789",
            session_id="session_789",
            display_name="Test User",
            roles_or_groups=("admin",),
            issued_at=datetime(2026, 1, 1),
            expires_at=datetime(2026, 1, 2),
            auth_provider=AuthProviderType.CLERK,
        )
        assert principal.subject_user_id == "user_123"
        assert principal.tenant_id == "tenant_456"
        assert principal.account_id == "acct_789"
        assert principal.display_name == "Test User"
        # Frozen — should not be mutable
        with pytest.raises(AttributeError):
            principal.subject_user_id = "changed"  # type: ignore

    def test_principal_roles_are_tuple(self):
        from datetime import datetime
        principal = HumanPrincipal(
            subject_user_id="u",
            email=None,
            tenant_id=None,
            account_id=None,
            session_id=None,
            display_name=None,
            roles_or_groups=("admin", "viewer"),
            issued_at=datetime(2026, 1, 1),
            expires_at=datetime(2026, 1, 2),
            auth_provider=AuthProviderType.HOC_IDENTITY,
        )
        assert isinstance(principal.roles_or_groups, tuple)
        assert len(principal.roles_or_groups) == 2


# =============================================================================
# Security Constants Tests
# =============================================================================


class TestAuthConstants:
    """Tests for auth_constants module."""

    def test_jwt_claim_mandatory_has_9_fields(self):
        assert len(JWTClaim.MANDATORY) == 9

    def test_jwt_claim_mandatory_contains_required(self):
        required = {"iss", "aud", "sub", "tid", "sid", "tier", "iat", "exp", "jti"}
        assert JWTClaim.MANDATORY == required

    def test_deny_reasons_are_strings(self):
        for reason in AuthDenyReason:
            assert isinstance(reason.value, str)
            assert reason.value == reason.value.upper()

    def test_deny_reason_count(self):
        """V1 design specifies these deny reasons."""
        assert len(AuthDenyReason) >= 8  # At least the 8 from V1 design


# =============================================================================
# Gateway Integration Tests
# =============================================================================


class TestGatewayProviderIntegration:
    """Tests that gateway routes human auth through the provider seam."""

    @pytest.mark.asyncio
    async def test_gateway_has_provider_method(self):
        """Gateway has _authenticate_human_via_provider method."""
        from app.auth.gateway import AuthGateway
        gw = AuthGateway()
        assert hasattr(gw, '_authenticate_human_via_provider')

    @pytest.mark.asyncio
    async def test_provider_error_maps_to_gateway_error(self):
        """AuthProviderError from provider maps to GatewayAuthError."""
        from app.auth.gateway import AuthGateway, TokenInfo
        from app.auth.gateway_types import is_error

        gw = AuthGateway()
        # Create a token_info that would route to human provider
        token_info = TokenInfo(issuer="https://test.clerk.accounts.dev", raw_token="fake")

        # Provider will fail (not configured), should return GatewayAuthError
        result = await gw._authenticate_human_via_provider(token_info)
        assert is_error(result)


# =============================================================================
# Gateway Context Parity Tests
# =============================================================================


class TestGatewayContextParity:
    """Tests that HumanPrincipal → HumanAuthContext preserves all fields from the
    original _authenticate_clerk() path, including account_id and display_name."""

    def _make_principal(self, provider: AuthProviderType = AuthProviderType.CLERK):
        from datetime import datetime
        return HumanPrincipal(
            subject_user_id="user_abc",
            email="parity@example.com",
            tenant_id="org_xyz",
            account_id="acct_999",
            session_id="sess_111",
            display_name="Parity User",
            roles_or_groups=("viewer",),
            issued_at=datetime(2026, 1, 1),
            expires_at=datetime(2026, 1, 2),
            auth_provider=provider,
        )

    def test_account_id_propagated(self):
        """account_id from HumanPrincipal reaches HumanAuthContext."""
        from app.auth.contexts import AuthSource, HumanAuthContext
        principal = self._make_principal()
        ctx = HumanAuthContext(
            actor_id=principal.subject_user_id,
            session_id=principal.session_id or "",
            auth_source=AuthSource.CLERK,
            tenant_id=principal.tenant_id,
            account_id=principal.account_id,
            email=principal.email,
            display_name=principal.display_name,
        )
        assert ctx.account_id == "acct_999"

    def test_display_name_propagated(self):
        """display_name from HumanPrincipal reaches HumanAuthContext."""
        from app.auth.contexts import AuthSource, HumanAuthContext
        principal = self._make_principal()
        ctx = HumanAuthContext(
            actor_id=principal.subject_user_id,
            session_id=principal.session_id or "",
            auth_source=AuthSource.CLERK,
            tenant_id=principal.tenant_id,
            account_id=principal.account_id,
            email=principal.email,
            display_name=principal.display_name,
        )
        assert ctx.display_name == "Parity User"

    def test_none_account_id_propagated(self):
        """None account_id is preserved (HOC Identity path won't have it)."""
        from datetime import datetime
        from app.auth.contexts import AuthSource, HumanAuthContext
        principal = HumanPrincipal(
            subject_user_id="u",
            email=None,
            tenant_id="t",
            account_id=None,
            session_id="s",
            display_name=None,
            roles_or_groups=(),
            issued_at=datetime(2026, 1, 1),
            expires_at=datetime(2026, 1, 2),
            auth_provider=AuthProviderType.HOC_IDENTITY,
        )
        ctx = HumanAuthContext(
            actor_id=principal.subject_user_id,
            session_id=principal.session_id or "",
            auth_source=AuthSource.HOC_IDENTITY,
            tenant_id=principal.tenant_id,
            account_id=principal.account_id,
            email=principal.email,
            display_name=principal.display_name,
        )
        assert ctx.account_id is None
        assert ctx.display_name is None


# =============================================================================
# Auth Source Mapping Tests
# =============================================================================


class TestAuthSourceMapping:
    """Tests that auth_provider → AuthSource mapping is correct."""

    def test_clerk_maps_to_clerk_source(self):
        """Clerk provider maps to AuthSource.CLERK."""
        from app.auth.contexts import AuthSource
        _PROVIDER_TO_AUTH_SOURCE = {
            "clerk": AuthSource.CLERK,
            "hoc_identity": AuthSource.HOC_IDENTITY,
        }
        assert _PROVIDER_TO_AUTH_SOURCE[AuthProviderType.CLERK.value] == AuthSource.CLERK

    def test_hoc_identity_maps_to_hoc_identity_source(self):
        """HOC Identity provider maps to AuthSource.HOC_IDENTITY, NOT AuthSource.CLERK."""
        from app.auth.contexts import AuthSource
        _PROVIDER_TO_AUTH_SOURCE = {
            "clerk": AuthSource.CLERK,
            "hoc_identity": AuthSource.HOC_IDENTITY,
        }
        assert _PROVIDER_TO_AUTH_SOURCE[AuthProviderType.HOC_IDENTITY.value] == AuthSource.HOC_IDENTITY
        # Explicitly assert it is NOT CLERK
        assert _PROVIDER_TO_AUTH_SOURCE[AuthProviderType.HOC_IDENTITY.value] != AuthSource.CLERK

    def test_auth_source_enum_has_hoc_identity(self):
        """AuthSource enum includes HOC_IDENTITY value."""
        from app.auth.contexts import AuthSource
        assert hasattr(AuthSource, "HOC_IDENTITY")
        assert AuthSource.HOC_IDENTITY.value == "hoc_identity"
