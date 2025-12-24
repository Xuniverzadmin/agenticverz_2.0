"""
Category 2: Auth Boundary Verification - CI Guardrails

PIN-148: These tests MUST pass in CI to prevent regression of auth boundaries.

Invariants (from spec):
1. A token belongs to exactly one domain
2. A session belongs to exactly one console
3. A role escalation is impossible by accident
4. Failure must be loud and logged

Test Matrix:
- Console token MUST NOT access /ops/*
- FOPS token MUST NOT access /guard/*
- Cross-access MUST return 403
- All rejections MUST be audited
"""

import os
from unittest.mock import MagicMock

import pytest

# Set test environment variables before imports
os.environ.setdefault("AOS_API_KEY", "test_console_key_12345")
os.environ.setdefault("AOS_FOPS_KEY", "test_fops_key_67890")
os.environ.setdefault("AOS_JWT_SECRET", "test_jwt_secret")


class TestAuthBoundaryInvariants:
    """
    Test auth boundary invariants.

    These tests verify that:
    1. Console keys cannot access FOPS endpoints
    2. FOPS keys cannot access Console endpoints
    3. All rejections return proper error codes
    4. All rejections are logged
    """

    @pytest.fixture
    def console_key(self):
        return os.environ.get("AOS_API_KEY", "test_console_key")

    @pytest.fixture
    def fops_key(self):
        return os.environ.get("AOS_FOPS_KEY", "test_fops_key")

    def test_console_key_rejected_on_fops_endpoint(self, console_key):
        """
        INVARIANT: Console key MUST be rejected on /ops/* endpoints.

        This prevents customer console credentials from accessing founder data.
        """

        from fastapi import Request

        from app.auth.console_auth import verify_fops_token

        # Create mock request with console key
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-API-Key": console_key}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        # Verify rejection
        import asyncio

        with pytest.raises(Exception) as exc_info:
            asyncio.run(verify_fops_token(mock_request, None))

        # Check it's an auth error
        assert "403" in str(exc_info.value.status_code) or "AUTH" in str(exc_info.value.detail)

    def test_fops_key_rejected_on_console_endpoint(self, fops_key):
        """
        INVARIANT: FOPS key MUST be rejected on /guard/* endpoints.

        This prevents founder credentials from being used on customer endpoints.
        """

        from fastapi import Request

        from app.auth.console_auth import verify_console_token

        # Create mock request with fops key
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-API-Key": fops_key}
        mock_request.query_params = {"tenant_id": "test"}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        # Verify rejection
        import asyncio

        with pytest.raises(Exception) as exc_info:
            asyncio.run(verify_console_token(mock_request, None))

        # Check it's an auth error
        assert "403" in str(exc_info.value.status_code) or "AUTH" in str(exc_info.value.detail)

    def test_no_key_rejected_on_fops(self):
        """
        INVARIANT: Missing key MUST be rejected on /ops/* endpoints.
        """
        from fastapi import Request

        from app.auth.console_auth import verify_fops_token

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        import asyncio

        with pytest.raises(Exception) as exc_info:
            asyncio.run(verify_fops_token(mock_request, None))

        assert "403" in str(exc_info.value.status_code) or "AUTH" in str(exc_info.value.detail)

    def test_no_key_rejected_on_console(self):
        """
        INVARIANT: Missing key MUST be rejected on /guard/* endpoints.
        """
        from fastapi import Request

        from app.auth.console_auth import verify_console_token

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.query_params = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        import asyncio

        with pytest.raises(Exception) as exc_info:
            asyncio.run(verify_console_token(mock_request, None))

        assert "403" in str(exc_info.value.status_code) or "AUTH" in str(exc_info.value.detail)

    def test_invalid_key_rejected(self):
        """
        INVARIANT: Invalid keys MUST be rejected on all protected endpoints.
        """
        from fastapi import Request

        from app.auth.console_auth import verify_console_token, verify_fops_token

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-API-Key": "invalid-key-xyz"}
        mock_request.query_params = {"tenant_id": "test"}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        import asyncio

        # Test FOPS
        with pytest.raises(Exception):
            asyncio.run(verify_fops_token(mock_request, None))

        # Test Console
        with pytest.raises(Exception):
            asyncio.run(verify_console_token(mock_request, None))


class TestTokenAudienceSeparation:
    """
    Test token audience separation.

    Tokens with aud="console" MUST NOT work on FOPS.
    Tokens with aud="fops" MUST NOT work on Console.
    """

    def test_token_audiences_are_separate(self):
        """
        INVARIANT: Token audiences must be explicitly different.
        """
        from app.auth.console_auth import TokenAudience

        assert TokenAudience.CONSOLE.value == "console"
        assert TokenAudience.FOPS.value == "fops"
        assert TokenAudience.CONSOLE.value != TokenAudience.FOPS.value

    def test_customer_token_claims(self):
        """
        INVARIANT: Customer tokens must have org_id and valid role.
        """
        from app.auth.console_auth import CustomerRole, CustomerToken

        token = CustomerToken(
            aud="console",
            sub="user_123",
            org_id="org_456",
            role=CustomerRole.ADMIN,
            iss="agenticverz",
            exp=9999999999,
        )

        assert token.aud == "console"
        assert token.org_id == "org_456"
        assert token.role == CustomerRole.ADMIN

    def test_founder_token_requires_mfa(self):
        """
        INVARIANT: Founder tokens MUST have mfa=true.
        """
        from app.auth.console_auth import FounderRole, FounderToken

        token = FounderToken(
            aud="fops",
            sub="founder_x",
            role=FounderRole.FOUNDER,
            mfa=True,
            iss="agenticverz",
            exp=9999999999,
        )

        assert token.aud == "fops"
        assert token.mfa is True
        assert token.role == FounderRole.FOUNDER


class TestAuditLogging:
    """
    Test audit logging for auth rejections.

    INVARIANT: Every rejection MUST be logged with structured data.
    """

    def test_auth_audit_event_schema(self):
        """
        INVARIANT: Audit events must have all required fields.
        """
        from app.auth.console_auth import AuthAuditEvent

        event = AuthAuditEvent(
            actor_id="user_123",
            attempted_domain="fops",
            token_aud="console",
            reason="AUD_MISMATCH",
            ip="192.168.1.1",
        )

        data = event.to_dict()

        assert data["event"] == "AUTH_DOMAIN_REJECT"
        assert data["actor_id"] == "user_123"
        assert data["attempted_domain"] == "fops"
        assert data["token_aud"] == "console"
        assert data["reason"] == "AUD_MISMATCH"
        assert data["ip"] == "192.168.1.1"
        assert "ts" in data

    def test_reject_reasons_are_explicit(self):
        """
        INVARIANT: Rejection reasons must be explicit, not generic.
        """
        from app.auth.console_auth import AuthRejectReason

        reasons = [r.value for r in AuthRejectReason]

        assert "MISSING_TOKEN" in reasons
        assert "INVALID_TOKEN" in reasons
        assert "EXPIRED_TOKEN" in reasons
        assert "AUD_MISMATCH" in reasons
        assert "ROLE_INVALID" in reasons
        assert "MFA_REQUIRED" in reasons
        assert "ORG_ID_MISSING" in reasons


class TestCookieSeparation:
    """
    Test cookie configuration separation.

    INVARIANT: Console and FOPS must use different cookie names and domains.
    """

    def test_cookie_names_are_separate(self):
        """
        INVARIANT: Cookie names must be different per console.
        """
        from app.auth.console_auth import CONSOLE_COOKIE_NAME, FOPS_COOKIE_NAME

        assert CONSOLE_COOKIE_NAME == "aos_console_session"
        assert FOPS_COOKIE_NAME == "aos_fops_session"
        assert CONSOLE_COOKIE_NAME != FOPS_COOKIE_NAME

    def test_cookie_settings_per_domain(self):
        """
        INVARIANT: Cookie settings must be domain-specific.
        """
        from app.auth.console_auth import get_cookie_settings

        console_settings = get_cookie_settings("console", is_production=True)
        fops_settings = get_cookie_settings("fops", is_production=True)

        # Different cookie names
        assert console_settings["key"] != fops_settings["key"]

        # Different domains
        assert console_settings["domain"] != fops_settings["domain"]

        # Both secure in production
        assert console_settings["secure"] is True
        assert fops_settings["secure"] is True

        # Both strict same-site
        assert console_settings["samesite"] == "strict"
        assert fops_settings["samesite"] == "strict"


# Run tests with: pytest tests/test_category2_auth_boundary.py -v
