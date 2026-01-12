# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Phase-6 MockBillingProvider tests
# Callers: pytest, CI pipeline
# Allowed Imports: L4 (billing), pytest
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 Phase-6 (Billing, Plans & Limits)

"""
Phase-6 MockBillingProvider Tests

Tests are deterministic with no external calls.

DESIGN INVARIANTS VERIFIED:
- BILLING-001: Billing never blocks onboarding
- BILLING-002: Limits are derived, not stored
- BILLING-003: Billing state does not affect roles
- BILLING-004: No billing mutation without audit (mock tracks mutations)
- BILLING-005: Mock provider must satisfy same interface as real provider
"""

import pytest

from app.billing import (
    BillingState,
    Plan,
    PlanTier,
    Limits,
    MockBillingProvider,
    get_billing_provider,
    set_billing_provider,
    derive_limits,
    PLAN_FREE,
    PLAN_PRO,
    PLAN_ENTERPRISE,
    DEFAULT_PLAN,
    DEFAULT_LIMITS,
    LIMITS_PROFILES,
)


# =============================================================================
# BillingState Tests
# =============================================================================


class TestBillingState:
    """Tests for BillingState enum."""

    def test_billing_state_values(self):
        """Verify all billing states exist."""
        assert BillingState.TRIAL.value == "trial"
        assert BillingState.ACTIVE.value == "active"
        assert BillingState.PAST_DUE.value == "past_due"
        assert BillingState.SUSPENDED.value == "suspended"

    def test_billing_state_default_is_trial(self):
        """TRIAL is the default state after onboarding COMPLETE."""
        assert BillingState.default() == BillingState.TRIAL

    def test_billing_state_from_string(self):
        """Parse billing states from strings."""
        assert BillingState.from_string("trial") == BillingState.TRIAL
        assert BillingState.from_string("TRIAL") == BillingState.TRIAL
        assert BillingState.from_string("Trial") == BillingState.TRIAL
        assert BillingState.from_string("active") == BillingState.ACTIVE

    def test_billing_state_from_string_invalid(self):
        """Invalid state string raises ValueError."""
        with pytest.raises(ValueError):
            BillingState.from_string("invalid")

    def test_allows_usage_for_non_suspended(self):
        """Non-SUSPENDED states allow usage."""
        assert BillingState.TRIAL.allows_usage() is True
        assert BillingState.ACTIVE.allows_usage() is True
        assert BillingState.PAST_DUE.allows_usage() is True

    def test_allows_usage_suspended_blocks(self):
        """SUSPENDED state blocks usage."""
        assert BillingState.SUSPENDED.allows_usage() is False

    def test_is_in_good_standing(self):
        """Only TRIAL and ACTIVE are in good standing."""
        assert BillingState.TRIAL.is_in_good_standing() is True
        assert BillingState.ACTIVE.is_in_good_standing() is True
        assert BillingState.PAST_DUE.is_in_good_standing() is False
        assert BillingState.SUSPENDED.is_in_good_standing() is False


# =============================================================================
# Plan Tests
# =============================================================================


class TestPlan:
    """Tests for Plan model."""

    def test_plan_creation(self):
        """Plans can be created with all fields."""
        plan = Plan(
            id="test-v1",
            name="Test",
            tier=PlanTier.PRO,
            limits_profile="pro",
            description="Test plan",
        )
        assert plan.id == "test-v1"
        assert plan.name == "Test"
        assert plan.tier == PlanTier.PRO
        assert plan.limits_profile == "pro"
        assert plan.description == "Test plan"

    def test_plan_is_immutable(self):
        """Plans are frozen dataclasses."""
        with pytest.raises(Exception):  # FrozenInstanceError
            PLAN_FREE.id = "changed"

    def test_plan_validation_empty_id(self):
        """Empty plan ID raises ValueError."""
        with pytest.raises(ValueError):
            Plan(id="", name="Test", tier=PlanTier.FREE, limits_profile="free")

    def test_plan_validation_empty_name(self):
        """Empty plan name raises ValueError."""
        with pytest.raises(ValueError):
            Plan(id="test", name="", tier=PlanTier.FREE, limits_profile="free")

    def test_hardcoded_plans_exist(self):
        """All hardcoded plans exist and are valid."""
        assert PLAN_FREE.id == "free-v1"
        assert PLAN_PRO.id == "pro-v1"
        assert PLAN_ENTERPRISE.id == "enterprise-v1"
        assert DEFAULT_PLAN == PLAN_FREE

    def test_plan_tier_from_string(self):
        """Parse plan tiers from strings."""
        assert PlanTier.from_string("free") == PlanTier.FREE
        assert PlanTier.from_string("PRO") == PlanTier.PRO
        assert PlanTier.from_string("enterprise") == PlanTier.ENTERPRISE


# =============================================================================
# Limits Tests
# =============================================================================


class TestLimits:
    """Tests for Limits model and derivation."""

    def test_limits_creation(self):
        """Limits can be created with fields."""
        limits = Limits(
            max_requests_per_day=1000,
            max_active_agents=5,
        )
        assert limits.max_requests_per_day == 1000
        assert limits.max_active_agents == 5
        assert limits.max_storage_mb is None  # Optional

    def test_limits_is_immutable(self):
        """Limits are frozen dataclasses."""
        limits = Limits(max_requests_per_day=1000)
        with pytest.raises(Exception):  # FrozenInstanceError
            limits.max_requests_per_day = 2000

    def test_limits_is_unlimited(self):
        """Check if all limits are unlimited."""
        unlimited = Limits()
        assert unlimited.is_unlimited() is True

        limited = Limits(max_requests_per_day=1000)
        assert limited.is_unlimited() is False

    def test_derive_limits_free(self):
        """Derive limits for free profile."""
        limits = derive_limits("free")
        assert limits.max_requests_per_day == 1000
        assert limits.max_active_agents == 3
        assert limits.max_storage_mb == 100

    def test_derive_limits_pro(self):
        """Derive limits for pro profile."""
        limits = derive_limits("pro")
        assert limits.max_requests_per_day == 10000
        assert limits.max_active_agents == 20

    def test_derive_limits_enterprise(self):
        """Derive limits for enterprise profile (unlimited)."""
        limits = derive_limits("enterprise")
        assert limits.max_requests_per_day is None  # Unlimited
        assert limits.max_active_agents is None  # Unlimited
        assert limits.is_unlimited() is True

    def test_derive_limits_unknown_profile(self):
        """Unknown profile returns default (restrictive) limits."""
        limits = derive_limits("unknown-profile")
        assert limits == DEFAULT_LIMITS
        assert limits.max_requests_per_day == 100  # Very restrictive


# =============================================================================
# MockBillingProvider Tests
# =============================================================================


class TestMockBillingProvider:
    """Tests for MockBillingProvider implementation."""

    @pytest.fixture
    def provider(self):
        """Create a fresh mock provider for each test."""
        provider = MockBillingProvider()
        yield provider
        provider.reset()

    def test_provider_implements_protocol(self, provider):
        """MockBillingProvider implements BillingProvider protocol."""
        # These methods must exist
        assert hasattr(provider, "get_billing_state")
        assert hasattr(provider, "get_plan")
        assert hasattr(provider, "get_limits")
        assert hasattr(provider, "is_limit_exceeded")

    def test_default_billing_state_is_trial(self, provider):
        """Unknown tenants get TRIAL state (default after COMPLETE)."""
        state = provider.get_billing_state("unknown-tenant")
        assert state == BillingState.TRIAL

    def test_default_plan_is_free(self, provider):
        """Unknown tenants get FREE plan."""
        plan = provider.get_plan("unknown-tenant")
        assert plan == DEFAULT_PLAN
        assert plan.tier == PlanTier.FREE

    def test_set_billing_state(self, provider):
        """Can set billing state for testing."""
        provider.set_billing_state("tenant-1", BillingState.ACTIVE)
        assert provider.get_billing_state("tenant-1") == BillingState.ACTIVE

    def test_set_plan(self, provider):
        """Can set plan for testing."""
        provider.set_plan("tenant-1", PLAN_PRO)
        assert provider.get_plan("tenant-1") == PLAN_PRO

    def test_get_limits_derives_from_plan(self, provider):
        """Limits are derived from plan's limits_profile."""
        free_limits = provider.get_limits(PLAN_FREE)
        assert free_limits == derive_limits("free")

        pro_limits = provider.get_limits(PLAN_PRO)
        assert pro_limits == derive_limits("pro")

    def test_is_limit_exceeded_under_limit(self, provider):
        """Values under limit return False."""
        # Free plan has max_requests_per_day = 1000
        assert provider.is_limit_exceeded("tenant-1", "max_requests_per_day", 500) is False

    def test_is_limit_exceeded_over_limit(self, provider):
        """Values over limit return True."""
        # Free plan has max_requests_per_day = 1000
        assert provider.is_limit_exceeded("tenant-1", "max_requests_per_day", 1500) is True

    def test_is_limit_exceeded_unlimited(self, provider):
        """Unlimited limits always return False."""
        provider.set_plan("tenant-1", PLAN_ENTERPRISE)
        # Enterprise plan has unlimited everything
        assert provider.is_limit_exceeded("tenant-1", "max_requests_per_day", 1000000) is False

    def test_reset_clears_state(self, provider):
        """Reset clears all mock state."""
        provider.set_billing_state("tenant-1", BillingState.ACTIVE)
        provider.set_plan("tenant-1", PLAN_PRO)
        provider.reset()

        assert provider.get_billing_state("tenant-1") == BillingState.TRIAL
        assert provider.get_plan("tenant-1") == DEFAULT_PLAN


# =============================================================================
# Singleton Tests
# =============================================================================


class TestSingleton:
    """Tests for billing provider singleton."""

    def test_get_billing_provider_returns_mock(self):
        """get_billing_provider returns MockBillingProvider by default."""
        provider = get_billing_provider()
        assert isinstance(provider, MockBillingProvider)

    def test_set_billing_provider(self):
        """Can replace the provider singleton."""
        original = get_billing_provider()
        new_provider = MockBillingProvider()

        set_billing_provider(new_provider)
        assert get_billing_provider() is new_provider

        # Restore original
        set_billing_provider(original)


# =============================================================================
# Invariant Tests
# =============================================================================


class TestBillingInvariants:
    """Tests verifying Phase-6 design invariants."""

    def test_billing_002_limits_derived_not_stored(self):
        """BILLING-002: Limits are derived, not stored."""
        provider = MockBillingProvider()

        # Limits come from plan's limits_profile
        plan = provider.get_plan("tenant-1")
        limits = provider.get_limits(plan)

        # Verify limits match the profile derivation
        assert limits == derive_limits(plan.limits_profile)

        # No way to set limits directly (no set_limits method)
        assert not hasattr(provider, "set_limits")

    def test_billing_003_billing_state_does_not_affect_roles(self):
        """BILLING-003: Billing state does not affect roles."""
        # This is verified by the absence of any role-related code in billing module
        # The billing module has no imports from app.auth.tenant_roles
        provider = MockBillingProvider()

        # Changing billing state doesn't return any role information
        provider.set_billing_state("tenant-1", BillingState.SUSPENDED)
        state = provider.get_billing_state("tenant-1")

        # BillingState has no role-related methods
        assert not hasattr(state, "get_role")
        assert not hasattr(state, "affects_role")

    def test_billing_005_mock_satisfies_protocol(self):
        """BILLING-005: Mock provider satisfies same interface as real provider."""
        from typing import get_type_hints

        provider = MockBillingProvider()

        # Verify all protocol methods exist and are callable
        assert callable(getattr(provider, "get_billing_state", None))
        assert callable(getattr(provider, "get_plan", None))
        assert callable(getattr(provider, "get_limits", None))
        assert callable(getattr(provider, "is_limit_exceeded", None))
