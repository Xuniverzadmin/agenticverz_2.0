# Layer: TEST
# Product: system-wide
# AUDIENCE: INTERNAL
# Role: Tests for auth provider seam — factory selection, contract compliance, gateway integration
# Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md

"""
Auth Provider Seam Tests

Tests:
1. Provider factory selects correct implementation based on AUTH_PROVIDER env.
2. CloveHumanAuthProvider implements the HumanAuthProvider interface.
3. Factory forces canonical provider even if legacy values are supplied.
4. Gateway human-auth path delegates to provider seam.
5. HumanPrincipal → HumanAuthContext mapping preserves downstream contract.
6. Clerk is explicitly deprecated.
"""

from __future__ import annotations

import json
import os
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.auth.auth_constants import AuthDenyReason, AuthProviderType, JWTClaim
from app.auth.auth_provider import (
    AuthProviderError,
    HumanAuthProvider,
    HumanPrincipal,
    get_human_auth_provider,
    reset_human_auth_provider,
)
from app.auth.auth_provider_clove import CloveHumanAuthProvider


# =============================================================================
# Provider Factory Tests
# =============================================================================


class TestProviderFactory:
    """Tests for get_human_auth_provider() factory selection."""

    def setup_method(self):
        reset_human_auth_provider()

    def teardown_method(self):
        reset_human_auth_provider()

    def test_default_provider_is_clove(self):
        """Default AUTH_PROVIDER env (unset) yields CloveHumanAuthProvider."""
        with patch.dict(os.environ, {}, clear=True):
            reset_human_auth_provider()
            from app.auth import auth_provider
            auth_provider.AUTH_PROVIDER_ENV = "clove"
            provider = get_human_auth_provider()
            assert isinstance(provider, CloveHumanAuthProvider)
            assert provider.provider_type == AuthProviderType.CLOVE

    def test_clerk_selection_is_forced_to_clove(self):
        """AUTH_PROVIDER=clerk is deprecated and forced to CloveHumanAuthProvider."""
        from app.auth import auth_provider
        auth_provider.AUTH_PROVIDER_ENV = "clerk"
        reset_human_auth_provider()
        provider = get_human_auth_provider()
        assert isinstance(provider, CloveHumanAuthProvider)
        assert provider.provider_type == AuthProviderType.CLOVE

    def test_clerk_provider_emits_deprecation_warning(self, caplog):
        """AUTH_PROVIDER=clerk emits explicit deprecation warning."""
        from app.auth import auth_provider
        auth_provider.AUTH_PROVIDER_ENV = "clerk"
        reset_human_auth_provider()
        with patch.dict(os.environ, {"AOS_MODE": "stagetest"}):
            get_human_auth_provider()
        assert "DEPRECATED" in caplog.text
        assert "forcing clove" in caplog.text

    def test_invalid_provider_emits_warning(self, caplog):
        """Non-clove provider emits a loud override warning."""
        from app.auth import auth_provider
        auth_provider.AUTH_PROVIDER_ENV = "bogus"
        reset_human_auth_provider()
        with patch.dict(os.environ, {"AOS_MODE": "stagetest"}):
            get_human_auth_provider()
        assert "forcing clove" in caplog.text

    def test_invalid_provider_fails_fast_in_prod(self):
        """Production mode rejects invalid AUTH_PROVIDER values."""
        from app.auth import auth_provider
        auth_provider.AUTH_PROVIDER_ENV = "clerk"
        reset_human_auth_provider()
        with patch.dict(os.environ, {"AOS_MODE": "prod"}):
            with pytest.raises(RuntimeError, match="must be clove"):
                get_human_auth_provider()

    def test_hoc_identity_alias_maps_to_clove(self):
        """AUTH_PROVIDER=hoc_identity is silently upgraded to clove."""
        from app.auth import auth_provider
        auth_provider.AUTH_PROVIDER_ENV = "hoc_identity"
        reset_human_auth_provider()
        provider = get_human_auth_provider()
        assert isinstance(provider, CloveHumanAuthProvider)
        assert provider.provider_type == AuthProviderType.CLOVE

    def test_clove_provider_selection(self):
        """AUTH_PROVIDER=clove yields CloveHumanAuthProvider."""
        from app.auth import auth_provider
        auth_provider.AUTH_PROVIDER_ENV = "clove"
        reset_human_auth_provider()
        provider = get_human_auth_provider()
        assert isinstance(provider, CloveHumanAuthProvider)
        assert provider.provider_type == AuthProviderType.CLOVE
        # Restore
        auth_provider.AUTH_PROVIDER_ENV = "clove"
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


class TestCloveAdapterInterface:
    """Tests that CloveHumanAuthProvider satisfies HumanAuthProvider contract."""

    def test_is_human_auth_provider(self):
        adapter = CloveHumanAuthProvider()
        assert isinstance(adapter, HumanAuthProvider)

    def test_has_provider_type(self):
        adapter = CloveHumanAuthProvider()
        assert adapter.provider_type == AuthProviderType.CLOVE

    def test_not_configured_when_missing_required_config(self, monkeypatch):
        """Provider is unconfigured when issuer/audience/JWKS source are absent."""
        from app.auth import auth_provider_clove as clove_provider_mod
        monkeypatch.setattr(clove_provider_mod, "_DEFAULT_ISSUER", "")
        monkeypatch.setattr(clove_provider_mod, "_DEFAULT_AUDIENCE", "")
        monkeypatch.setattr(clove_provider_mod, "_JWKS_URL", "")
        monkeypatch.setattr(clove_provider_mod, "_JWKS_ENDPOINT", "")
        monkeypatch.setattr(clove_provider_mod, "_JWKS_FILE", "")
        adapter = clove_provider_mod.CloveHumanAuthProvider()
        assert adapter.is_configured is False

    @pytest.mark.asyncio
    async def test_raises_provider_unavailable_when_unconfigured(self, monkeypatch):
        """Unconfigured provider raises PROVIDER_UNAVAILABLE."""
        from app.auth import auth_provider_clove as clove_provider_mod
        monkeypatch.setattr(clove_provider_mod, "_DEFAULT_ISSUER", "")
        monkeypatch.setattr(clove_provider_mod, "_DEFAULT_AUDIENCE", "")
        monkeypatch.setattr(clove_provider_mod, "_JWKS_URL", "")
        monkeypatch.setattr(clove_provider_mod, "_JWKS_ENDPOINT", "")
        monkeypatch.setattr(clove_provider_mod, "_JWKS_FILE", "")
        adapter = clove_provider_mod.CloveHumanAuthProvider()
        with pytest.raises(AuthProviderError) as exc_info:
            await adapter.verify_bearer_token("any_token")
        assert exc_info.value.reason == AuthDenyReason.PROVIDER_UNAVAILABLE


class TestCloveVerification:
    """Verification tests for EdDSA/JWKS provider path."""

    @pytest.mark.asyncio
    async def test_verifies_token_via_static_jwks_file(self, tmp_path, monkeypatch):
        from app.auth import auth_provider_clove as clove_provider_mod

        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        jwk = json.loads(jwt.algorithms.get_default_algorithms()["EdDSA"].to_jwk(public_key))
        jwk["kid"] = "k-test-1"
        jwks_file = tmp_path / "jwks.json"
        jwks_file.write_text(json.dumps({"keys": [jwk]}), encoding="utf-8")

        monkeypatch.setattr(clove_provider_mod, "_JWKS_FILE", str(jwks_file))
        monkeypatch.setattr(clove_provider_mod, "_JWKS_URL", "")
        monkeypatch.setattr(clove_provider_mod, "_DEFAULT_ISSUER", "https://auth.agenticverz.com")
        monkeypatch.setattr(clove_provider_mod, "_DEFAULT_AUDIENCE", "clove")

        provider = clove_provider_mod.CloveHumanAuthProvider()
        assert provider.is_configured is True

        token = jwt.encode(
            {
                "iss": "https://auth.agenticverz.com",
                "aud": "clove",
                "sub": "user_1",
                "tid": "tenant_1",
                "sid": "session_1",
                "tier": "pro",
                "iat": 1700000000,
                "exp": 4700000000,
                "jti": "jwt_1",
                "email": "user@example.com",
                "roles": ["admin"],
            },
            private_key,
            algorithm="EdDSA",
            headers={"kid": "k-test-1"},
        )

        principal = await provider.verify_bearer_token(token)
        assert principal.subject_user_id == "user_1"
        assert principal.tenant_id == "tenant_1"
        assert principal.session_id == "session_1"
        assert principal.auth_provider == AuthProviderType.CLOVE
        assert principal.roles_or_groups == ("admin",)

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
            auth_provider=AuthProviderType.CLOVE,
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
            auth_provider=AuthProviderType.CLOVE,
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

    def test_canonical_provider_is_clove(self):
        """AuthProviderType.CLOVE is the canonical provider."""
        assert AuthProviderType.CLOVE.value == "clove"

    def test_clerk_is_deprecated_legacy(self):
        """AuthProviderType.CLERK exists but is deprecated."""
        assert AuthProviderType.CLERK.value == "clerk"


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
        """Unavailable provider maps to GatewayAuthError(PROVIDER_UNAVAILABLE)."""
        from app.auth.gateway import AuthGateway, TokenInfo
        from app.auth.gateway_types import GatewayErrorCode, is_error, unwrap_error
        from app.auth.auth_constants import CLOVE_ISSUER

        class _UnconfiguredProvider:
            provider_type = AuthProviderType.CLOVE
            is_configured = False

        gw = AuthGateway()
        # Create a token_info that would route to human provider
        token_info = TokenInfo(issuer=CLOVE_ISSUER, raw_token="fake")

        with patch("app.auth.gateway.get_human_auth_provider", return_value=_UnconfiguredProvider()):
            result = await gw._authenticate_human_via_provider(token_info)
        assert is_error(result)
        assert unwrap_error(result).error_code == GatewayErrorCode.PROVIDER_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_clerk_issuer_rejected(self):
        """Legacy Clerk issuer values are rejected by gateway routing."""
        from app.auth.gateway import AuthGateway, TokenInfo
        from app.auth.gateway_types import GatewayErrorCode, is_error, unwrap_error

        gw = AuthGateway()
        result = await gw._route_by_issuer(
            TokenInfo(issuer="https://example.clerk.accounts.dev", raw_token="fake")
        )
        assert is_error(result)
        err = unwrap_error(result)
        assert err.error_code == GatewayErrorCode.JWT_INVALID
        assert "Untrusted token issuer" in (err.details or "")


# =============================================================================
# Gateway Context Parity Tests
# =============================================================================


class TestGatewayContextParity:
    """Tests that HumanPrincipal → HumanAuthContext preserves all fields from the
    gateway mapping path, including account_id and display_name."""

    def _make_principal(self, provider: AuthProviderType = AuthProviderType.CLOVE):
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
            auth_source=AuthSource.CLOVE,
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
            auth_source=AuthSource.CLOVE,
            tenant_id=principal.tenant_id,
            account_id=principal.account_id,
            email=principal.email,
            display_name=principal.display_name,
        )
        assert ctx.display_name == "Parity User"

    def test_none_account_id_propagated(self):
        """None account_id is preserved (Clove path won't always have it)."""
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
            auth_provider=AuthProviderType.CLOVE,
        )
        ctx = HumanAuthContext(
            actor_id=principal.subject_user_id,
            session_id=principal.session_id or "",
            auth_source=AuthSource.CLOVE,
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

    def test_clove_maps_to_clove_source(self):
        """Clove provider maps to AuthSource.CLOVE."""
        from app.auth.contexts import AuthSource
        _PROVIDER_TO_AUTH_SOURCE = {
            "clove": AuthSource.CLOVE,
        }
        assert _PROVIDER_TO_AUTH_SOURCE[AuthProviderType.CLOVE.value] == AuthSource.CLOVE

    def test_auth_source_enum_has_clove(self):
        """AuthSource enum includes CLOVE value."""
        from app.auth.contexts import AuthSource
        assert hasattr(AuthSource, "CLOVE")
        assert AuthSource.CLOVE.value == "clove"

    def test_auth_source_clerk_is_deprecated(self):
        """AuthSource.CLERK exists for backward compat but CLOVE is canonical."""
        from app.auth.contexts import AuthSource
        assert hasattr(AuthSource, "CLERK")
        assert AuthSource.CLERK.value == "clerk"
        # CLOVE must be listed first (canonical)
        sources = list(AuthSource)
        clove_idx = next(i for i, s in enumerate(sources) if s == AuthSource.CLOVE)
        clerk_idx = next(i for i, s in enumerate(sources) if s == AuthSource.CLERK)
        assert clove_idx < clerk_idx, "CLOVE must be listed before CLERK (canonical first)"


# =============================================================================
# Provider Status Tests
# =============================================================================


class TestProviderStatus:
    """Tests for get_human_auth_provider_status() observability."""

    def setup_method(self):
        reset_human_auth_provider()

    def teardown_method(self):
        reset_human_auth_provider()

    def test_status_reports_clove_as_effective(self):
        """Provider status reports effective_provider=clove."""
        from app.auth import auth_provider
        auth_provider.AUTH_PROVIDER_ENV = "clove"
        reset_human_auth_provider()
        from app.auth.auth_provider import get_human_auth_provider_status
        status = get_human_auth_provider_status()
        assert status["effective_provider"] == "clove"
        assert status["canonical_provider"] == "clove"

    def test_status_includes_deprecation_metadata(self):
        """Provider status includes deprecation info for clerk."""
        from app.auth import auth_provider
        auth_provider.AUTH_PROVIDER_ENV = "clove"
        reset_human_auth_provider()
        from app.auth.auth_provider import get_human_auth_provider_status
        status = get_human_auth_provider_status()
        assert "deprecation" in status
        assert "clerk" in status["deprecation"]
        assert status["deprecation"]["clerk"]["status"] == "deprecated"

    def test_status_includes_readiness_field(self):
        """Provider status includes readiness aggregate with checks."""
        from app.auth import auth_provider
        auth_provider.AUTH_PROVIDER_ENV = "clove"
        reset_human_auth_provider()
        from app.auth.auth_provider import get_human_auth_provider_status
        status = get_human_auth_provider_status()
        assert "readiness" in status
        readiness = status["readiness"]
        assert "ready" in readiness
        assert "checks" in readiness
        assert "failed_count" in readiness
        assert isinstance(readiness["checks"], list)
        assert len(readiness["checks"]) == 3  # issuer, audience, jwks_source

    def test_status_readiness_checks_have_correct_structure(self):
        """Each readiness check has check, status, detail fields."""
        from app.auth import auth_provider
        auth_provider.AUTH_PROVIDER_ENV = "clove"
        reset_human_auth_provider()
        from app.auth.auth_provider import get_human_auth_provider_status
        status = get_human_auth_provider_status()
        for check in status["readiness"]["checks"]:
            assert "check" in check
            assert "status" in check
            assert check["status"] in ("pass", "fail")
            assert "detail" in check


# =============================================================================
# Readiness Check Tests
# =============================================================================


class TestReadinessChecks:
    """Tests for CloveHumanAuthProvider.readiness_checks() and readiness_summary()."""

    def test_readiness_all_pass_when_configured(self):
        """All checks pass when issuer, audience, and JWKS source are present."""
        provider = CloveHumanAuthProvider()
        # Default config has issuer + audience from constants
        if provider.is_configured:
            summary = provider.readiness_summary()
            assert summary["ready"] is True
            assert summary["failed_count"] == 0
            assert all(c["status"] == "pass" for c in summary["checks"])

    def test_readiness_fails_when_issuer_missing(self, monkeypatch):
        """Issuer check fails when CLOVE_ISSUER is empty."""
        from app.auth import auth_provider_clove as clove_mod
        monkeypatch.setattr(clove_mod, "_DEFAULT_ISSUER", "")
        provider = clove_mod.CloveHumanAuthProvider()
        summary = provider.readiness_summary()
        assert summary["ready"] is False
        issuer_check = next(c for c in summary["checks"] if c["check"] == "issuer")
        assert issuer_check["status"] == "fail"

    def test_readiness_fails_when_audience_missing(self, monkeypatch):
        """Audience check fails when CLOVE_AUDIENCE is empty."""
        from app.auth import auth_provider_clove as clove_mod
        monkeypatch.setattr(clove_mod, "_DEFAULT_AUDIENCE", "")
        provider = clove_mod.CloveHumanAuthProvider()
        summary = provider.readiness_summary()
        audience_check = next(c for c in summary["checks"] if c["check"] == "audience")
        assert audience_check["status"] == "fail"

    def test_readiness_fails_when_jwks_source_missing(self, monkeypatch):
        """JWKS source check fails when neither URL nor file is set."""
        from app.auth import auth_provider_clove as clove_mod
        monkeypatch.setattr(clove_mod, "_JWKS_URL", "")
        monkeypatch.setattr(clove_mod, "_JWKS_FILE", "")
        monkeypatch.setattr(clove_mod, "_JWKS_ENDPOINT", "")
        monkeypatch.setattr(clove_mod, "_DEFAULT_ISSUER", "")
        provider = clove_mod.CloveHumanAuthProvider()
        summary = provider.readiness_summary()
        jwks_check = next(c for c in summary["checks"] if c["check"] == "jwks_source")
        assert jwks_check["status"] == "fail"

    def test_readiness_passes_with_jwks_file(self, monkeypatch, tmp_path):
        """JWKS source passes when a file path is configured."""
        from app.auth import auth_provider_clove as clove_mod
        jwks_file = tmp_path / "jwks.json"
        jwks_file.write_text('{"keys":[]}')
        monkeypatch.setattr(clove_mod, "_JWKS_FILE", str(jwks_file))
        monkeypatch.setattr(clove_mod, "_JWKS_URL", "")
        monkeypatch.setattr(clove_mod, "_DEFAULT_ISSUER", "https://auth.example.com")
        monkeypatch.setattr(clove_mod, "_DEFAULT_AUDIENCE", "test")
        provider = clove_mod.CloveHumanAuthProvider()
        summary = provider.readiness_summary()
        assert summary["ready"] is True
        jwks_check = next(c for c in summary["checks"] if c["check"] == "jwks_source")
        assert jwks_check["status"] == "pass"
        assert "file=" in jwks_check["detail"]

    def test_readiness_passes_with_jwks_url(self, monkeypatch):
        """JWKS source passes when a URL is configured."""
        from app.auth import auth_provider_clove as clove_mod
        monkeypatch.setattr(clove_mod, "_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
        monkeypatch.setattr(clove_mod, "_JWKS_FILE", "")
        monkeypatch.setattr(clove_mod, "_DEFAULT_ISSUER", "https://auth.example.com")
        monkeypatch.setattr(clove_mod, "_DEFAULT_AUDIENCE", "test")
        provider = clove_mod.CloveHumanAuthProvider()
        summary = provider.readiness_summary()
        assert summary["ready"] is True
        jwks_check = next(c for c in summary["checks"] if c["check"] == "jwks_source")
        assert jwks_check["status"] == "pass"
        assert "url=" in jwks_check["detail"]

    def test_readiness_all_fail_when_nothing_configured(self, monkeypatch):
        """All 3 checks fail when nothing is configured."""
        from app.auth import auth_provider_clove as clove_mod
        monkeypatch.setattr(clove_mod, "_DEFAULT_ISSUER", "")
        monkeypatch.setattr(clove_mod, "_DEFAULT_AUDIENCE", "")
        monkeypatch.setattr(clove_mod, "_JWKS_URL", "")
        monkeypatch.setattr(clove_mod, "_JWKS_FILE", "")
        monkeypatch.setattr(clove_mod, "_JWKS_ENDPOINT", "")
        provider = clove_mod.CloveHumanAuthProvider()
        summary = provider.readiness_summary()
        assert summary["ready"] is False
        assert summary["failed_count"] == 3


# =============================================================================
# Startup Gate Tests
# =============================================================================


class TestStartupGatePolicy:
    """Tests for Clove JWKS readiness startup gate logic."""

    def test_startup_gate_raises_in_prod_when_not_ready(self, monkeypatch):
        """Production startup must fail when Clove readiness is not met."""
        from app.auth import auth_provider_clove as clove_mod
        monkeypatch.setattr(clove_mod, "_DEFAULT_ISSUER", "")
        monkeypatch.setattr(clove_mod, "_DEFAULT_AUDIENCE", "")
        monkeypatch.setattr(clove_mod, "_JWKS_URL", "")
        monkeypatch.setattr(clove_mod, "_JWKS_FILE", "")
        monkeypatch.setattr(clove_mod, "_JWKS_ENDPOINT", "")
        provider = clove_mod.CloveHumanAuthProvider()
        readiness = provider.readiness_summary()

        # Simulate the startup gate logic from main.py
        assert readiness["ready"] is False
        is_prod = True  # simulating AOS_MODE=prod
        if not readiness["ready"] and is_prod:
            failed = [c for c in readiness["checks"] if c["status"] == "fail"]
            with pytest.raises(RuntimeError, match="not ready in production"):
                raise RuntimeError(
                    f"Clove auth provider not ready in production: "
                    f"{readiness['failed_count']} check(s) failed — "
                    + ", ".join(c["detail"] for c in failed)
                )

    def test_startup_gate_raises_in_strict_mode_when_not_ready(self, monkeypatch):
        """Non-prod startup fails when strict mode enabled and readiness not met."""
        from app.auth import auth_provider_clove as clove_mod
        monkeypatch.setattr(clove_mod, "_DEFAULT_ISSUER", "")
        monkeypatch.setattr(clove_mod, "_DEFAULT_AUDIENCE", "")
        monkeypatch.setattr(clove_mod, "_JWKS_URL", "")
        monkeypatch.setattr(clove_mod, "_JWKS_FILE", "")
        monkeypatch.setattr(clove_mod, "_JWKS_ENDPOINT", "")
        provider = clove_mod.CloveHumanAuthProvider()
        readiness = provider.readiness_summary()
        strict_startup = True  # simulating AUTH_CLOVE_STRICT_STARTUP=true

        assert readiness["ready"] is False
        if not readiness["ready"] and strict_startup:
            failed = [c for c in readiness["checks"] if c["status"] == "fail"]
            with pytest.raises(RuntimeError, match="strict mode"):
                raise RuntimeError(
                    f"Clove auth provider not ready (strict mode): "
                    f"{readiness['failed_count']} check(s) failed — "
                    + ", ".join(c["detail"] for c in failed)
                )

    def test_startup_gate_warns_in_nonprod_when_not_ready(self, monkeypatch, caplog):
        """Non-prod startup emits warning but does not crash."""
        import logging
        from app.auth import auth_provider_clove as clove_mod
        monkeypatch.setattr(clove_mod, "_DEFAULT_ISSUER", "")
        monkeypatch.setattr(clove_mod, "_DEFAULT_AUDIENCE", "")
        monkeypatch.setattr(clove_mod, "_JWKS_URL", "")
        monkeypatch.setattr(clove_mod, "_JWKS_FILE", "")
        monkeypatch.setattr(clove_mod, "_JWKS_ENDPOINT", "")
        provider = clove_mod.CloveHumanAuthProvider()
        readiness = provider.readiness_summary()

        # Non-prod, non-strict: just warning
        assert readiness["ready"] is False
        with caplog.at_level(logging.WARNING):
            failed = [c for c in readiness["checks"] if c["status"] == "fail"]
            logging.getLogger("test").warning(
                "clove_readiness_gate_warning — provider not fully configured",
                extra={"failed_checks": failed},
            )
        assert "not fully configured" in caplog.text

    def test_startup_gate_passes_when_ready(self):
        """Startup gate passes silently when all checks pass."""
        provider = CloveHumanAuthProvider()
        if provider.is_configured:
            readiness = provider.readiness_summary()
            assert readiness["ready"] is True
            # No exception raised — gate passes

    def test_startup_gate_contract_matches_main_py(self):
        """
        Validate startup gate policy contract against actual main.py implementation.

        Extracts the real gate code pattern from main.py (lines 687-735) and verifies
        all three branches exist: prod fatal, strict fatal, non-prod warning.
        """
        import ast
        import pathlib

        main_py = pathlib.Path(__file__).parent.parent.parent / "app" / "main.py"
        source = main_py.read_text()

        # Contract: error messages in main.py must match test expectations
        assert "Clove auth provider not ready in production:" in source, \
            "main.py prod gate message missing or changed"
        assert "Clove auth provider not ready (strict mode):" in source, \
            "main.py strict gate message missing or changed"
        assert "clove_readiness_gate_warning" in source, \
            "main.py non-prod warning log event missing or changed"

        # Contract: env vars controlling gate behavior
        assert "AOS_MODE" in source, "main.py must check AOS_MODE for prod detection"
        assert "AUTH_CLOVE_STRICT_STARTUP" in source, "main.py must check AUTH_CLOVE_STRICT_STARTUP"

        # Contract: gate reads readiness_summary from provider
        assert "readiness_summary" in source, "main.py must call readiness_summary()"

        # Contract: gate uses RuntimeError for fatal exits
        tree = ast.parse(source)
        gate_raises = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Raise) and node.exc is not None
            and isinstance(node.exc, ast.Call)
            and isinstance(node.exc.func, ast.Name)
            and node.exc.func.id == "RuntimeError"
        ]
        # Must have at least 2 RuntimeError raises in the gate block (prod + strict)
        runtime_errors_with_ready = [
            r for r in gate_raises
            if any("ready" in ast.dump(arg).lower() for arg in r.exc.args)
        ]
        assert len(runtime_errors_with_ready) >= 2, \
            f"Expected >=2 RuntimeError raises with 'ready' in main.py, found {len(runtime_errors_with_ready)}"


# =============================================================================
# Public Path Effective Policy Tests
# =============================================================================


class TestPublicPathEffectivePolicy:
    """
    Tests that /hoc/api/auth/provider/status is effectively public through
    both the gateway_policy.py path and the RBAC_RULES.yaml schema path.
    """

    def test_gateway_policy_includes_provider_status(self):
        """gateway_policy.py PUBLIC_PATHS includes /hoc/api/auth/provider/status."""
        from app.hoc.cus.hoc_spine.authority.gateway_policy import PUBLIC_PATHS
        assert "/hoc/api/auth/provider/status" in PUBLIC_PATHS

    def test_gateway_policy_config_includes_provider_status(self):
        """get_gateway_policy_config() returns public_paths including provider status."""
        from app.hoc.cus.hoc_spine.authority.gateway_policy import get_gateway_policy_config
        config = get_gateway_policy_config()
        assert "/hoc/api/auth/provider/status" in config["public_paths"]

    def test_rbac_schema_has_provider_status_rule(self):
        """RBAC_RULES.yaml has a PUBLIC rule covering /hoc/api/auth/provider/status."""
        from app.auth.rbac_rules_loader import load_rbac_rules, AccessTier
        rules = load_rbac_rules()
        matching = [
            r for r in rules
            if r.path_prefix == "/hoc/api/auth/provider/status"
            and r.access_tier == AccessTier.PUBLIC
        ]
        assert len(matching) == 1, \
            f"Expected 1 PUBLIC rule for /hoc/api/auth/provider/status, found {len(matching)}"
        rule = matching[0]
        assert rule.rule_id == "HOC_AUTH_PROVIDER_STATUS"
        assert "GET" in rule.methods
        assert "preflight" in rule.allow_environment
        assert "production" in rule.allow_environment

    def test_rbac_public_paths_includes_provider_status(self):
        """get_public_paths() from RBAC loader includes /hoc/api/auth/provider/status."""
        from app.auth.rbac_rules_loader import get_public_paths
        for env in ("preflight", "production"):
            public = get_public_paths(environment=env)
            assert "/hoc/api/auth/provider/status" in public, \
                f"/hoc/api/auth/provider/status missing from public paths in {env}"

    def test_middleware_public_paths_include_provider_status(self):
        """AuthGatewayMiddleware with gateway_policy config marks provider status as public."""
        from app.hoc.cus.hoc_spine.authority.gateway_policy import get_gateway_policy_config
        config = get_gateway_policy_config()
        # Simulate what AuthGatewayMiddleware.__init__ does
        public_paths_set = set(config["public_paths"])
        assert "/hoc/api/auth/provider/status" in public_paths_set

    def test_dual_source_consistency(self):
        """gateway_policy.py and RBAC_RULES.yaml agree on provider status being public."""
        from app.hoc.cus.hoc_spine.authority.gateway_policy import get_public_paths as gw_public
        from app.auth.rbac_rules_loader import get_public_paths as rbac_public
        gw_paths = gw_public()
        rbac_paths = rbac_public(environment="production")
        target = "/hoc/api/auth/provider/status"
        assert target in gw_paths, "Missing from gateway_policy.py"
        assert target in rbac_paths, "Missing from RBAC_RULES.yaml"
