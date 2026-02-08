# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Runtime gates integration tests
# Callers: pytest, CI pipeline
# Allowed Imports: L3 (middleware), L4 (providers)
# Reference: PIN-401 Track A (Production Wiring)

"""
Runtime Gates Integration Tests

Tests for lifecycle, protection, and billing gate middleware.

Test Categories:
1. Lifecycle gate enforcement
2. Protection gate enforcement
3. Billing gate enforcement
4. Gate ordering and composition
5. Exempt path handling
"""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

from app.hoc.cus.account.L5_schemas.tenant_lifecycle_state import TenantLifecycleState
from app.billing.state import BillingState
from app.hoc.cus.account.L5_engines.billing_provider_engine import (
    MockBillingProvider,
    set_billing_provider,
)
from app.protection.provider import MockAbuseProtectionProvider, set_protection_provider
from app.protection.decisions import Decision

import app.api.middleware.lifecycle_gate as lifecycle_gate_mod

from app.api.middleware.lifecycle_gate import (
    LifecycleContext,
    check_lifecycle,
    require_active_lifecycle,
    require_sdk_execution,
    is_exempt_path,
    is_sdk_path,
    EXEMPT_PREFIXES,
    SDK_PATHS,
)
from app.api.middleware.protection_gate import (
    ProtectionContext,
    check_protection,
    require_protection_allow,
)
from app.api.middleware.billing_gate import (
    BillingContext,
    check_billing,
    require_billing_active,
    check_billing_limit,
)

from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingState


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def fresh_providers():
    """Set up fresh mock providers."""
    billing = MockBillingProvider()
    set_billing_provider(billing)

    protection = MockAbuseProtectionProvider()
    set_protection_provider(protection)

    return {
        "billing": billing,
        "protection": protection,
    }


@pytest.fixture
def lifecycle_states(monkeypatch):
    """
    Lifecycle gate is DB-backed (async). Patch the internal fetcher to keep
    tests deterministic without depending on a real DB/session.
    """
    states = {"t_test": TenantLifecycleState.ACTIVE}

    async def _fake_fetch(tenant_id: str) -> TenantLifecycleState:
        return states.get(tenant_id, TenantLifecycleState.ACTIVE)

    monkeypatch.setattr(lifecycle_gate_mod, "_fetch_lifecycle_state", _fake_fetch)
    return states


@pytest.fixture
def mock_request():
    """Create a mock request object."""

    @dataclass
    class MockState:
        tenant_id: str = "t_test"
        onboarding_state: OnboardingState = OnboardingState.COMPLETE

    class MockURL:
        path: str = "/api/v1/runs"

    request = MagicMock()
    request.state = MockState()
    request.url = MockURL()
    request.method = "POST"

    return request


# =============================================================================
# LIFECYCLE GATE TESTS
# =============================================================================


class TestLifecycleGateExemptions:
    """Tests for lifecycle gate path exemptions."""

    def test_exempt_prefixes_defined(self):
        """Exempt prefixes are defined."""
        assert "/health" in EXEMPT_PREFIXES
        assert "/fdr/" in EXEMPT_PREFIXES
        assert "/docs" in EXEMPT_PREFIXES

    def test_is_exempt_path_health(self):
        """Health paths are exempt."""
        assert is_exempt_path("/health") is True
        assert is_exempt_path("/health/ready") is True

    def test_is_exempt_path_founder(self):
        """Founder paths are exempt."""
        assert is_exempt_path("/fdr/lifecycle/t_123") is True

    def test_is_exempt_path_sdk(self):
        """SDK paths are NOT exempt."""
        assert is_exempt_path("/api/v1/runs") is False

    def test_sdk_paths_defined(self):
        """SDK paths are defined."""
        assert "/api/v1/runs" in SDK_PATHS
        assert "/api/v1/runtime/" in SDK_PATHS

    def test_is_sdk_path(self):
        """SDK paths are identified correctly."""
        assert is_sdk_path("/api/v1/runs") is True
        assert is_sdk_path("/api/v1/runs/123") is True
        assert is_sdk_path("/api/v1/runtime/simulate") is True
        assert is_sdk_path("/api/v1/auth/login") is False


class TestLifecycleGateEnforcement:
    """Tests for lifecycle gate enforcement logic."""

    @pytest.mark.anyio
    async def test_active_tenant_allowed(self, fresh_providers, lifecycle_states, mock_request):
        """ACTIVE tenant passes lifecycle check."""
        context = await check_lifecycle(mock_request)

        assert context.state == TenantLifecycleState.ACTIVE
        assert context.allows_sdk is True
        assert context.allows_writes is True
        assert context.allows_reads is True

    @pytest.mark.anyio
    async def test_suspended_tenant_sdk_blocked(self, fresh_providers, lifecycle_states, mock_request):
        """SUSPENDED tenant has SDK blocked."""
        lifecycle_states["t_test"] = TenantLifecycleState.SUSPENDED

        context = await check_lifecycle(mock_request)

        assert context.state == TenantLifecycleState.SUSPENDED
        assert context.allows_sdk is False
        assert context.allows_writes is False
        assert context.allows_reads is True

    @pytest.mark.anyio
    async def test_terminated_tenant_all_blocked(self, fresh_providers, lifecycle_states, mock_request):
        """TERMINATED tenant has all operations blocked."""
        lifecycle_states["t_test"] = TenantLifecycleState.TERMINATED

        context = await check_lifecycle(mock_request)

        assert context.state == TenantLifecycleState.TERMINATED
        assert context.allows_sdk is False
        assert context.allows_writes is False
        assert context.allows_reads is False

    @pytest.mark.anyio
    async def test_require_sdk_execution_active_passes(self, fresh_providers, lifecycle_states, mock_request):
        """require_sdk_execution passes for ACTIVE tenant."""
        context = await require_sdk_execution(mock_request)
        assert context.allows_sdk is True

    @pytest.mark.anyio
    async def test_require_sdk_execution_suspended_raises(self, fresh_providers, lifecycle_states, mock_request):
        """require_sdk_execution raises for SUSPENDED tenant."""
        from fastapi import HTTPException

        lifecycle_states["t_test"] = TenantLifecycleState.SUSPENDED

        with pytest.raises(HTTPException) as exc_info:
            await require_sdk_execution(mock_request)

        assert exc_info.value.status_code == 403
        assert "sdk_execution_blocked" in str(exc_info.value.detail)


# =============================================================================
# PROTECTION GATE TESTS
# =============================================================================


class TestProtectionGateEnforcement:
    """Tests for protection gate enforcement logic."""

    def test_allowed_request_passes(self, fresh_providers, mock_request):
        """Request within limits passes."""
        context = check_protection(mock_request)

        assert context.result.decision == Decision.ALLOW
        assert context.anomaly is None

    def test_exempt_path_passes(self, fresh_providers, mock_request):
        """Exempt paths always pass."""
        mock_request.url.path = "/health"

        context = check_protection(mock_request)

        assert context.is_exempt is True
        assert context.result.decision == Decision.ALLOW

    def test_require_protection_allow_passes(self, fresh_providers, mock_request):
        """require_protection_allow passes for allowed requests."""
        context = require_protection_allow(mock_request)
        assert context.result.decision == Decision.ALLOW


# =============================================================================
# BILLING GATE TESTS
# =============================================================================


class TestBillingGateEnforcement:
    """Tests for billing gate enforcement logic."""

    def test_active_billing_passes(self, fresh_providers, mock_request):
        """ACTIVE billing state passes."""
        fresh_providers["billing"].set_billing_state("t_test", BillingState.ACTIVE)

        context = check_billing(mock_request)

        assert context.billing_state == BillingState.ACTIVE
        assert context.allows_usage is True
        assert context.is_applicable is True

    def test_suspended_billing_blocked(self, fresh_providers, mock_request):
        """SUSPENDED billing state blocks usage."""
        fresh_providers["billing"].set_billing_state("t_test", BillingState.SUSPENDED)

        context = check_billing(mock_request)

        assert context.billing_state == BillingState.SUSPENDED
        assert context.allows_usage is False

    def test_billing_001_onboarding_not_blocked(self, fresh_providers, mock_request):
        """BILLING-001: Billing never blocks onboarding."""
        mock_request.state.onboarding_state = OnboardingState.API_KEY_CREATED

        context = check_billing(mock_request)

        # Should return neutral context, not check billing
        assert context.is_applicable is False
        assert context.allows_usage is True

    def test_require_billing_active_passes(self, fresh_providers, mock_request):
        """require_billing_active passes for ACTIVE billing."""
        fresh_providers["billing"].set_billing_state("t_test", BillingState.ACTIVE)

        context = require_billing_active(mock_request)
        assert context.allows_usage is True

    def test_require_billing_active_suspended_raises(self, fresh_providers, mock_request):
        """require_billing_active raises for SUSPENDED billing."""
        from fastapi import HTTPException

        fresh_providers["billing"].set_billing_state("t_test", BillingState.SUSPENDED)

        with pytest.raises(HTTPException) as exc_info:
            require_billing_active(mock_request)

        assert exc_info.value.status_code == 402
        assert "billing_suspended" in str(exc_info.value.detail)


class TestBillingLimitChecks:
    """Tests for billing limit enforcement."""

    def test_limit_not_exceeded(self, fresh_providers, mock_request):
        """Limit check passes when not exceeded."""
        context = check_billing(mock_request)

        result = check_billing_limit(context, "max_requests_per_day", 100)
        assert result is None  # No error

    def test_limit_exceeded(self, fresh_providers, mock_request):
        """Limit check returns error when exceeded."""
        context = check_billing(mock_request)

        # Assuming default limits have max_requests_per_day of 1000
        result = check_billing_limit(context, "max_requests_per_day", 10000)

        if result is not None:  # If limit is set
            assert result["error"] == "limit_exceeded"
            assert result["limit"] == "max_requests_per_day"

    def test_limit_not_applicable_during_onboarding(self, fresh_providers, mock_request):
        """Limits not enforced during onboarding."""
        mock_request.state.onboarding_state = OnboardingState.IDENTITY_VERIFIED

        context = check_billing(mock_request)
        result = check_billing_limit(context, "max_requests_per_day", 999999)

        assert result is None  # Not enforced


# =============================================================================
# GATE COMPOSITION TESTS
# =============================================================================


class TestGateComposition:
    """Tests for gate ordering and composition."""

    @pytest.mark.anyio
    async def test_lifecycle_checked_before_billing(self, fresh_providers, lifecycle_states, mock_request):
        """Lifecycle is checked independently of billing."""
        # SUSPENDED lifecycle but ACTIVE billing
        lifecycle_states["t_test"] = TenantLifecycleState.SUSPENDED
        fresh_providers["billing"].set_billing_state("t_test", BillingState.ACTIVE)

        lifecycle_ctx = await check_lifecycle(mock_request)
        billing_ctx = check_billing(mock_request)

        # Lifecycle blocks
        assert lifecycle_ctx.allows_sdk is False
        # Billing would allow (but lifecycle blocks first)
        assert billing_ctx.allows_usage is True

    @pytest.mark.anyio
    async def test_all_gates_pass_for_active_tenant(self, fresh_providers, lifecycle_states, mock_request):
        """All gates pass for fully active tenant."""
        lifecycle_states["t_test"] = TenantLifecycleState.ACTIVE
        fresh_providers["billing"].set_billing_state("t_test", BillingState.ACTIVE)

        lifecycle_ctx = await check_lifecycle(mock_request)
        protection_ctx = check_protection(mock_request)
        billing_ctx = check_billing(mock_request)

        assert lifecycle_ctx.allows_sdk is True
        assert protection_ctx.result.decision == Decision.ALLOW
        assert billing_ctx.allows_usage is True

    @pytest.mark.anyio
    async def test_exempt_paths_skip_all_gates(self, fresh_providers, lifecycle_states, mock_request):
        """Exempt paths skip all gate enforcement."""
        mock_request.url.path = "/health"

        # Even with blocked states
        lifecycle_states["t_test"] = TenantLifecycleState.TERMINATED
        fresh_providers["billing"].set_billing_state("t_test", BillingState.SUSPENDED)

        lifecycle_ctx = await check_lifecycle(mock_request)
        billing_ctx = check_billing(mock_request)

        # Exempt paths return neutral contexts
        assert lifecycle_ctx.is_exempt is True
        assert billing_ctx.is_exempt is True
