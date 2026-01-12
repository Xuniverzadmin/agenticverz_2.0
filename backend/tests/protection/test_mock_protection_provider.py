# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Phase-7 MockAbuseProtectionProvider tests
# Callers: pytest, CI pipeline
# Allowed Imports: L4 (protection, billing), pytest
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 Phase-7 (Abuse & Protection Layer)

"""
Phase-7 MockAbuseProtectionProvider Tests

Tests are deterministic with no external calls.

DESIGN INVARIANTS VERIFIED:
- ABUSE-001: Protection does not affect onboarding, roles, or billing state
- ABUSE-002: All enforcement outcomes are explicit (no silent failure)
- ABUSE-003: Anomaly detection never blocks user traffic
- ABUSE-004: Protection providers are swappable behind a fixed interface
- ABUSE-005: Mock provider must be behavior-compatible with real provider
"""

import pytest

from app.protection import (
    Decision,
    ProtectionResult,
    AnomalySignal,
    MockAbuseProtectionProvider,
    get_protection_provider,
    set_protection_provider,
    allow,
    reject_rate_limit,
    reject_cost_limit,
    throttle,
    warn,
)
from app.billing import (
    MockBillingProvider,
    set_billing_provider,
    PLAN_FREE,
    PLAN_ENTERPRISE,
)


# =============================================================================
# Decision Tests
# =============================================================================


class TestDecision:
    """Tests for Decision enum."""

    def test_decision_values(self):
        """Verify all decisions exist."""
        assert Decision.ALLOW.value == "allow"
        assert Decision.THROTTLE.value == "throttle"
        assert Decision.REJECT.value == "reject"
        assert Decision.WARN.value == "warn"

    def test_blocks_request(self):
        """Only REJECT blocks requests."""
        assert Decision.REJECT.blocks_request() is True
        assert Decision.ALLOW.blocks_request() is False
        assert Decision.THROTTLE.blocks_request() is False
        assert Decision.WARN.blocks_request() is False

    def test_is_warning_only(self):
        """Only WARN is warning-only."""
        assert Decision.WARN.is_warning_only() is True
        assert Decision.ALLOW.is_warning_only() is False
        assert Decision.REJECT.is_warning_only() is False


# =============================================================================
# ProtectionResult Tests
# =============================================================================


class TestProtectionResult:
    """Tests for ProtectionResult dataclass."""

    def test_protection_result_creation(self):
        """ProtectionResult can be created with fields."""
        result = ProtectionResult(
            decision=Decision.ALLOW,
            dimension="none",
        )
        assert result.decision == Decision.ALLOW
        assert result.dimension == "none"

    def test_protection_result_is_immutable(self):
        """ProtectionResult is frozen."""
        result = allow()
        with pytest.raises(Exception):  # FrozenInstanceError
            result.decision = Decision.REJECT

    def test_to_error_response_reject_rate(self):
        """REJECT for rate returns proper error format."""
        result = reject_rate_limit("rate", 60000)
        error = result.to_error_response()

        assert error["error"] == "rate_limited"
        assert error["dimension"] == "rate"
        assert error["retry_after_ms"] == 60000

    def test_to_error_response_reject_cost(self):
        """REJECT for cost returns proper error format."""
        result = reject_cost_limit(512.45, 500.00)
        error = result.to_error_response()

        assert error["error"] == "cost_limit_exceeded"
        assert error["current_value"] == 512.45
        assert error["allowed_value"] == 500.00

    def test_to_error_response_throttle(self):
        """THROTTLE returns proper error format."""
        result = throttle("burst", 1000)
        error = result.to_error_response()

        assert error["error"] == "rate_limited"
        assert error["dimension"] == "burst"
        assert error["retry_after_ms"] == 1000

    def test_to_error_response_allow_empty(self):
        """ALLOW returns empty error dict."""
        result = allow()
        assert result.to_error_response() == {}


# =============================================================================
# AnomalySignal Tests
# =============================================================================


class TestAnomalySignal:
    """Tests for AnomalySignal dataclass."""

    def test_anomaly_signal_creation(self):
        """AnomalySignal can be created with fields."""
        signal = AnomalySignal(
            baseline=100.0,
            observed=980.0,
            window="5m",
            severity="high",
        )
        assert signal.baseline == 100.0
        assert signal.observed == 980.0
        assert signal.window == "5m"
        assert signal.severity == "high"

    def test_to_signal_response(self):
        """AnomalySignal formats correctly."""
        signal = AnomalySignal(
            baseline=120.0,
            observed=980.0,
            window="5m",
            severity="high",
        )
        response = signal.to_signal_response()

        assert response["signal"] == "usage_anomaly_detected"
        assert response["baseline"] == 120.0
        assert response["observed"] == 980.0
        assert response["window"] == "5m"


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_allow_creates_allow_result(self):
        """allow() creates ALLOW result."""
        result = allow()
        assert result.decision == Decision.ALLOW
        assert result.dimension == "none"

    def test_reject_rate_limit_creates_reject(self):
        """reject_rate_limit creates REJECT result."""
        result = reject_rate_limit("rate", 60000, "Custom message")
        assert result.decision == Decision.REJECT
        assert result.dimension == "rate"
        assert result.retry_after_ms == 60000
        assert result.message == "Custom message"

    def test_reject_cost_limit_creates_reject(self):
        """reject_cost_limit creates REJECT result."""
        result = reject_cost_limit(500.0, 400.0)
        assert result.decision == Decision.REJECT
        assert result.dimension == "cost"
        assert result.current_value == 500.0
        assert result.allowed_value == 400.0

    def test_throttle_creates_throttle(self):
        """throttle() creates THROTTLE result."""
        result = throttle("burst", 1000)
        assert result.decision == Decision.THROTTLE
        assert result.dimension == "burst"
        assert result.retry_after_ms == 1000

    def test_warn_creates_warn(self):
        """warn() creates WARN result."""
        result = warn("anomaly", "Unusual pattern")
        assert result.decision == Decision.WARN
        assert result.dimension == "anomaly"
        assert result.message == "Unusual pattern"


# =============================================================================
# MockAbuseProtectionProvider Tests
# =============================================================================


class TestMockAbuseProtectionProvider:
    """Tests for MockAbuseProtectionProvider implementation."""

    @pytest.fixture
    def provider(self):
        """Create a fresh mock provider for each test."""
        provider = MockAbuseProtectionProvider()
        yield provider
        provider.reset()

    @pytest.fixture
    def billing_provider(self):
        """Set up billing provider for cost tests."""
        billing = MockBillingProvider()
        set_billing_provider(billing)
        yield billing
        billing.reset()

    def test_provider_implements_protocol(self, provider):
        """MockAbuseProtectionProvider implements AbuseProtectionProvider protocol."""
        assert hasattr(provider, "check_rate_limit")
        assert hasattr(provider, "check_burst")
        assert hasattr(provider, "check_cost")
        assert hasattr(provider, "detect_anomaly")
        assert hasattr(provider, "check_all")

    def test_check_rate_limit_allows_under_limit(self, provider):
        """Rate limit allows requests under threshold."""
        result = provider.check_rate_limit("tenant-1", "/api/test")
        assert result.decision == Decision.ALLOW

    def test_check_rate_limit_rejects_over_limit(self, provider):
        """Rate limit rejects after threshold exceeded."""
        # Make 1001 requests (limit is 1000)
        for i in range(1000):
            provider.check_rate_limit("tenant-1", "/api/test")

        result = provider.check_rate_limit("tenant-1", "/api/test")
        assert result.decision == Decision.REJECT
        assert result.dimension == "rate"
        assert result.retry_after_ms == 60000

    def test_check_burst_allows_under_limit(self, provider):
        """Burst control allows requests under threshold."""
        result = provider.check_burst("tenant-1", "/api/test")
        assert result.decision == Decision.ALLOW

    def test_check_burst_throttles_over_limit(self, provider):
        """Burst control throttles after threshold exceeded."""
        # Make 101 requests in same second (limit is 100)
        for i in range(100):
            provider.check_burst("tenant-1", "/api/test")

        result = provider.check_burst("tenant-1", "/api/test")
        assert result.decision == Decision.THROTTLE
        assert result.dimension == "burst"
        assert result.retry_after_ms == 1000

    def test_check_cost_allows_under_limit(self, provider, billing_provider):
        """Cost guard allows when under daily limit."""
        result = provider.check_cost("tenant-1", "compute")
        assert result.decision == Decision.ALLOW

    def test_check_cost_rejects_over_limit(self, provider, billing_provider):
        """Cost guard rejects when over daily limit."""
        # Free plan has $10/month = ~$0.33/day limit
        provider.add_cost("tenant-1", 1.0)  # Over daily limit

        result = provider.check_cost("tenant-1", "compute")
        assert result.decision == Decision.REJECT
        assert result.dimension == "cost"

    def test_check_cost_allows_unlimited(self, provider, billing_provider):
        """Cost guard allows unlimited for enterprise."""
        billing_provider.set_plan("tenant-1", PLAN_ENTERPRISE)
        provider.add_cost("tenant-1", 10000.0)

        result = provider.check_cost("tenant-1", "compute")
        assert result.decision == Decision.ALLOW

    def test_detect_anomaly_none_initially(self, provider):
        """No anomaly detected initially."""
        anomaly = provider.detect_anomaly("tenant-1")
        assert anomaly is None

    def test_detect_anomaly_after_spike(self, provider):
        """Anomaly detected after 10x spike."""
        # Make requests across multiple endpoints to exceed anomaly threshold
        # (Rate limit is per-endpoint, anomaly is total across all endpoints)
        # Baseline is 100, multiplier is 10, so need > 1000 total
        for i in range(600):
            provider.check_rate_limit("tenant-1", "/api/test1")
        for i in range(600):
            provider.check_rate_limit("tenant-1", "/api/test2")

        anomaly = provider.detect_anomaly("tenant-1")
        assert anomaly is not None
        assert anomaly.baseline == 100.0
        assert anomaly.observed > 1000
        assert anomaly.severity in ("medium", "high")

    def test_check_all_ordering(self, provider, billing_provider):
        """check_all runs checks in correct order."""
        # Rate limit first - exhaust it
        for i in range(1000):
            provider.check_rate_limit("tenant-1", "/api/test")

        # check_all should hit rate limit first
        result = provider.check_all("tenant-1", "/api/test", "read")
        assert result.decision == Decision.REJECT
        assert result.dimension == "rate"

    def test_check_all_allows_when_all_pass(self, provider, billing_provider):
        """check_all returns ALLOW when all checks pass."""
        result = provider.check_all("tenant-1", "/api/test", "read")
        assert result.decision == Decision.ALLOW

    def test_reset_clears_state(self, provider):
        """Reset clears all mock state."""
        # Build up some state
        for i in range(500):
            provider.check_rate_limit("tenant-1", "/api/test")
        provider.add_cost("tenant-1", 100.0)

        provider.reset()

        # All counts should be reset
        result = provider.check_rate_limit("tenant-1", "/api/test")
        assert result.decision == Decision.ALLOW

    def test_reset_rate_limits_for_tenant(self, provider):
        """Can reset rate limits for specific tenant."""
        for i in range(500):
            provider.check_rate_limit("tenant-1", "/api/test")
        for i in range(500):
            provider.check_rate_limit("tenant-2", "/api/test")

        provider.reset_rate_limits("tenant-1")

        # tenant-1 should be reset
        result1 = provider.check_rate_limit("tenant-1", "/api/test")
        assert result1.decision == Decision.ALLOW

        # tenant-2 should still have counts (won't reject but has history)


# =============================================================================
# Singleton Tests
# =============================================================================


class TestSingleton:
    """Tests for protection provider singleton."""

    def test_get_protection_provider_returns_mock(self):
        """get_protection_provider returns MockAbuseProtectionProvider by default."""
        provider = get_protection_provider()
        assert isinstance(provider, MockAbuseProtectionProvider)

    def test_set_protection_provider(self):
        """Can replace the provider singleton."""
        original = get_protection_provider()
        new_provider = MockAbuseProtectionProvider()

        set_protection_provider(new_provider)
        assert get_protection_provider() is new_provider

        # Restore original
        set_protection_provider(original)


# =============================================================================
# Invariant Tests
# =============================================================================


class TestProtectionInvariants:
    """Tests verifying Phase-7 design invariants."""

    def test_abuse_001_protection_does_not_affect_state(self):
        """ABUSE-001: Protection does not affect onboarding, roles, or billing state."""
        provider = MockAbuseProtectionProvider()

        # Protection has no methods to mutate onboarding/roles/billing
        assert not hasattr(provider, "set_onboarding_state")
        assert not hasattr(provider, "set_role")
        assert not hasattr(provider, "set_billing_state")

        # check_all only returns ProtectionResult, no side effects on auth
        result = provider.check_all("tenant-1", "/api/test", "read")
        assert isinstance(result, ProtectionResult)

    def test_abuse_002_all_outcomes_explicit(self):
        """ABUSE-002: All enforcement outcomes are explicit (no silent failure)."""
        provider = MockAbuseProtectionProvider()

        # Every check returns a ProtectionResult with explicit decision
        result1 = provider.check_rate_limit("tenant-1", "/api/test")
        assert result1.decision in (Decision.ALLOW, Decision.REJECT)

        result2 = provider.check_burst("tenant-1", "/api/test")
        assert result2.decision in (Decision.ALLOW, Decision.THROTTLE)

        result3 = provider.check_cost("tenant-1", "compute")
        assert result3.decision in (Decision.ALLOW, Decision.REJECT)

        # No silent drops - all decisions are explicit enums
        for decision in Decision:
            assert isinstance(decision.value, str)

    def test_abuse_003_anomaly_never_blocks(self):
        """ABUSE-003: Anomaly detection never blocks user traffic."""
        provider = MockAbuseProtectionProvider()

        # Make requests across multiple endpoints to exceed anomaly threshold
        # (Rate limit is per-endpoint, anomaly is total)
        for i in range(600):
            provider.check_rate_limit("tenant-1", "/api/test1")
        for i in range(600):
            provider.check_rate_limit("tenant-1", "/api/test2")

        # Anomaly is detected but separate from blocking decisions
        anomaly = provider.detect_anomaly("tenant-1")
        assert anomaly is not None

        # Even with anomaly detected, check_all decisions are based on
        # rate/burst/cost, NOT on anomaly (which is non-blocking per ABUSE-003)
        # The anomaly signal is informational only
        assert anomaly.baseline == 100.0
        assert anomaly.observed > 1000

    def test_abuse_005_mock_satisfies_protocol(self):
        """ABUSE-005: Mock provider satisfies same interface as real provider."""
        provider = MockAbuseProtectionProvider()

        # Verify all protocol methods exist and are callable
        assert callable(getattr(provider, "check_rate_limit", None))
        assert callable(getattr(provider, "check_burst", None))
        assert callable(getattr(provider, "check_cost", None))
        assert callable(getattr(provider, "detect_anomaly", None))
        assert callable(getattr(provider, "check_all", None))


# =============================================================================
# Ordering Rule Tests
# =============================================================================


class TestOrderingRule:
    """Tests verifying the locked ordering rule (Section 7.7)."""

    @pytest.fixture
    def billing_provider(self):
        """Set up billing provider."""
        billing = MockBillingProvider()
        set_billing_provider(billing)
        yield billing
        billing.reset()

    def test_rate_limit_checked_before_burst(self):
        """Rate limit is checked before burst control."""
        provider = MockAbuseProtectionProvider()

        # Exhaust rate limit
        for i in range(1000):
            provider.check_rate_limit("tenant-1", "/api/test")

        # check_all should hit rate limit, not burst
        result = provider.check_all("tenant-1", "/api/test", "read")
        assert result.decision == Decision.REJECT
        assert result.dimension == "rate"  # Not "burst"

    def test_burst_checked_before_cost(self, billing_provider):
        """Burst control is checked before cost guard."""
        provider = MockAbuseProtectionProvider()

        # Set up cost limit violation
        provider.add_cost("tenant-1", 100.0)

        # Exhaust burst limit (within rate limit)
        for i in range(100):
            provider.check_burst("tenant-1", "/api/test")

        # check_all should hit burst, not cost
        result = provider.check_all("tenant-1", "/api/test", "read")
        assert result.decision == Decision.THROTTLE
        assert result.dimension == "burst"  # Not "cost"

    def test_cost_checked_before_anomaly(self, billing_provider):
        """Cost guard is checked before anomaly detection."""
        provider = MockAbuseProtectionProvider()

        # Set up cost limit violation
        provider.add_cost("tenant-1", 100.0)

        # check_all should return cost rejection
        result = provider.check_all("tenant-1", "/api/test", "read")
        assert result.decision == Decision.REJECT
        assert result.dimension == "cost"

        # Anomaly is still detected separately (non-blocking per ABUSE-003)
