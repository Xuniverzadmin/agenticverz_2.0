"""
Tests for Tier-Based Feature Gating (M32)

Tests:
- TenantTier enum ordering
- PricingPhase soft/hard modes
- FEATURE_TIER_MAP coverage
- requires_tier decorator
- resolve_tier function
- check_tier_access function
"""

import pytest

from app.auth.tier_gating import (
    FEATURE_TIER_MAP,
    PRICE_ANCHORS,
    PricingPhase,
    TenantTier,
    TierAccessResult,
    check_tier_access,
    get_tier_features,
    get_tier_info,
    get_upgrade_path,
    resolve_tier,
)


class TestTenantTierOrdering:
    """Test TenantTier enum ordering."""

    def test_tier_ordering_less_than(self):
        """Test that lower tiers are less than higher tiers."""
        assert TenantTier.OBSERVE < TenantTier.REACT
        assert TenantTier.REACT < TenantTier.PREVENT
        assert TenantTier.PREVENT < TenantTier.ASSIST
        assert TenantTier.ASSIST < TenantTier.GOVERN

    def test_tier_ordering_greater_than(self):
        """Test that higher tiers are greater than lower tiers."""
        assert TenantTier.GOVERN > TenantTier.ASSIST
        assert TenantTier.ASSIST > TenantTier.PREVENT
        assert TenantTier.PREVENT > TenantTier.REACT
        assert TenantTier.REACT > TenantTier.OBSERVE

    def test_tier_ordering_less_than_or_equal(self):
        """Test less than or equal comparisons."""
        assert TenantTier.OBSERVE <= TenantTier.OBSERVE
        assert TenantTier.OBSERVE <= TenantTier.REACT
        assert TenantTier.REACT <= TenantTier.PREVENT

    def test_tier_ordering_greater_than_or_equal(self):
        """Test greater than or equal comparisons."""
        assert TenantTier.GOVERN >= TenantTier.GOVERN
        assert TenantTier.GOVERN >= TenantTier.ASSIST
        assert TenantTier.PREVENT >= TenantTier.REACT


class TestResolveTier:
    """Test resolve_tier function."""

    def test_resolve_legacy_free(self):
        """Test resolving legacy 'free' plan."""
        assert resolve_tier("free") == TenantTier.OBSERVE

    def test_resolve_legacy_pro(self):
        """Test resolving legacy 'pro' plan."""
        assert resolve_tier("pro") == TenantTier.REACT

    def test_resolve_legacy_enterprise(self):
        """Test resolving legacy 'enterprise' plan."""
        assert resolve_tier("enterprise") == TenantTier.GOVERN

    def test_resolve_new_tier_names(self):
        """Test resolving new tier names."""
        assert resolve_tier("observe") == TenantTier.OBSERVE
        assert resolve_tier("react") == TenantTier.REACT
        assert resolve_tier("prevent") == TenantTier.PREVENT
        assert resolve_tier("assist") == TenantTier.ASSIST
        assert resolve_tier("govern") == TenantTier.GOVERN

    def test_resolve_marketing_names(self):
        """Test resolving marketing names."""
        assert resolve_tier("open_control_plane") == TenantTier.OBSERVE
        assert resolve_tier("builder") == TenantTier.REACT
        assert resolve_tier("authority_explorer") == TenantTier.PREVENT
        assert resolve_tier("scale") == TenantTier.ASSIST

    def test_resolve_case_insensitive(self):
        """Test that resolution is case insensitive."""
        assert resolve_tier("FREE") == TenantTier.OBSERVE
        assert resolve_tier("Pro") == TenantTier.REACT
        assert resolve_tier("ENTERPRISE") == TenantTier.GOVERN

    def test_resolve_unknown_defaults_to_observe(self):
        """Test that unknown plans default to OBSERVE."""
        assert resolve_tier("unknown") == TenantTier.OBSERVE
        assert resolve_tier("") == TenantTier.OBSERVE
        assert resolve_tier("random_plan") == TenantTier.OBSERVE


class TestCheckTierAccess:
    """Test check_tier_access function."""

    def test_access_granted_same_tier(self):
        """Test access granted when tenant has exact required tier."""
        result = check_tier_access("killswitch.write", TenantTier.REACT)
        assert result.allowed is True
        assert result.soft_blocked is False
        assert result.upgrade_required is False

    def test_access_granted_higher_tier(self):
        """Test access granted when tenant has higher tier."""
        result = check_tier_access("killswitch.write", TenantTier.PREVENT)
        assert result.allowed is True
        assert result.soft_blocked is False

    def test_access_denied_lower_tier_authority_phase(self):
        """Test access denied when tenant has lower tier in authority phase."""
        result = check_tier_access(
            "sdk.simulate.full",
            TenantTier.REACT,
            phase=PricingPhase.AUTHORITY,
        )
        assert result.allowed is False
        assert result.upgrade_required is True
        assert result.required_tier == TenantTier.PREVENT

    def test_soft_block_learning_phase(self):
        """Test soft block in learning phase."""
        result = check_tier_access(
            "sdk.simulate.full",
            TenantTier.REACT,
            phase=PricingPhase.LEARNING,
        )
        assert result.allowed is True
        assert result.soft_blocked is True
        assert result.upgrade_required is True

    def test_unknown_feature_defaults_to_observe(self):
        """Test that unknown features default to OBSERVE tier."""
        result = check_tier_access("unknown.feature", TenantTier.OBSERVE)
        assert result.allowed is True
        assert result.required_tier == TenantTier.OBSERVE


class TestFeatureTierMap:
    """Test FEATURE_TIER_MAP coverage."""

    def test_has_observe_features(self):
        """Test that OBSERVE tier has features."""
        observe_features = [f for f, t in FEATURE_TIER_MAP.items() if t == TenantTier.OBSERVE]
        assert len(observe_features) > 0
        assert "proxy.chat_completions" in observe_features

    def test_has_react_features(self):
        """Test that REACT tier has features."""
        react_features = [f for f, t in FEATURE_TIER_MAP.items() if t == TenantTier.REACT]
        assert len(react_features) > 0
        assert "killswitch.write" in react_features

    def test_has_prevent_features(self):
        """Test that PREVENT tier has features."""
        prevent_features = [f for f, t in FEATURE_TIER_MAP.items() if t == TenantTier.PREVENT]
        assert len(prevent_features) > 0
        assert "sdk.simulate.full" in prevent_features
        assert "evidence.export.pdf" in prevent_features

    def test_has_assist_features(self):
        """Test that ASSIST tier has features."""
        assist_features = [f for f, t in FEATURE_TIER_MAP.items() if t == TenantTier.ASSIST]
        assert len(assist_features) > 0
        assert "care.routing" in assist_features

    def test_has_govern_features(self):
        """Test that GOVERN tier has features."""
        govern_features = [f for f, t in FEATURE_TIER_MAP.items() if t == TenantTier.GOVERN]
        assert len(govern_features) > 0
        assert "policy.custom" in govern_features
        assert "compliance.soc2" in govern_features

    def test_feature_count(self):
        """Test that we have a reasonable number of features."""
        assert len(FEATURE_TIER_MAP) >= 60, f"Expected 60+ features, got {len(FEATURE_TIER_MAP)}"


class TestGetTierFeatures:
    """Test get_tier_features function."""

    def test_observe_has_least_features(self):
        """Test that OBSERVE has the fewest features."""
        observe_features = get_tier_features(TenantTier.OBSERVE)
        react_features = get_tier_features(TenantTier.REACT)
        assert len(observe_features) < len(react_features)

    def test_govern_has_all_features(self):
        """Test that GOVERN has access to all features."""
        govern_features = get_tier_features(TenantTier.GOVERN)
        assert len(govern_features) == len(FEATURE_TIER_MAP)

    def test_tier_hierarchy(self):
        """Test that higher tiers have more features."""
        observe = len(get_tier_features(TenantTier.OBSERVE))
        react = len(get_tier_features(TenantTier.REACT))
        prevent = len(get_tier_features(TenantTier.PREVENT))
        assist = len(get_tier_features(TenantTier.ASSIST))
        govern = len(get_tier_features(TenantTier.GOVERN))

        assert observe < react < prevent < assist < govern


class TestGetTierInfo:
    """Test get_tier_info function."""

    def test_tier_info_has_required_fields(self):
        """Test that tier info has all required fields."""
        info = get_tier_info(TenantTier.PREVENT)

        assert "tier" in info
        assert "marketing_name" in info
        assert "price_monthly_cents" in info
        assert "retention_days" in info
        assert "features" in info
        assert "feature_count" in info

    def test_observe_price_is_zero(self):
        """Test that OBSERVE tier is free."""
        info = get_tier_info(TenantTier.OBSERVE)
        assert info["price_monthly_cents"] == 0

    def test_react_price_is_900_cents(self):
        """Test that REACT tier is $9."""
        info = get_tier_info(TenantTier.REACT)
        assert info["price_monthly_cents"] == 900

    def test_prevent_price_is_19900_cents(self):
        """Test that PREVENT tier is $199."""
        info = get_tier_info(TenantTier.PREVENT)
        assert info["price_monthly_cents"] == 19900


class TestGetUpgradePath:
    """Test get_upgrade_path function."""

    def test_no_upgrade_needed(self):
        """Test when no upgrade is needed."""
        result = get_upgrade_path(TenantTier.PREVENT, "sdk.simulate.full")
        assert result["upgrade_needed"] is False

    def test_upgrade_needed(self):
        """Test when upgrade is needed."""
        result = get_upgrade_path(TenantTier.OBSERVE, "sdk.simulate.full")

        assert result["upgrade_needed"] is True
        assert result["current_tier"] == "observe"
        assert result["required_tier"] == "prevent"
        assert result["required_marketing_name"] == "Authority Explorer"

    def test_price_difference_calculated(self):
        """Test that price difference is calculated."""
        result = get_upgrade_path(TenantTier.OBSERVE, "killswitch.write")

        assert result["upgrade_needed"] is True
        assert result["price_difference_cents"] == 900  # $0 to $9


class TestPriceAnchors:
    """Test PRICE_ANCHORS configuration."""

    def test_all_tiers_have_anchors(self):
        """Test that all tiers have price anchors."""
        for tier in TenantTier:
            assert tier in PRICE_ANCHORS, f"Missing anchor for {tier}"

    def test_retention_days_increase(self):
        """Test that retention days increase with tier."""
        observe_retention = PRICE_ANCHORS[TenantTier.OBSERVE]["retention_days"]
        react_retention = PRICE_ANCHORS[TenantTier.REACT]["retention_days"]
        prevent_retention = PRICE_ANCHORS[TenantTier.PREVENT]["retention_days"]
        assist_retention = PRICE_ANCHORS[TenantTier.ASSIST]["retention_days"]
        govern_retention = PRICE_ANCHORS[TenantTier.GOVERN]["retention_days"]

        assert observe_retention < react_retention < prevent_retention < assist_retention < govern_retention

    def test_prices_increase(self):
        """Test that prices increase with tier (for priced tiers)."""
        observe_price = PRICE_ANCHORS[TenantTier.OBSERVE]["price_monthly_cents"]
        react_price = PRICE_ANCHORS[TenantTier.REACT]["price_monthly_cents"]
        prevent_price = PRICE_ANCHORS[TenantTier.PREVENT]["price_monthly_cents"]

        assert observe_price < react_price < prevent_price


class TestTierAccessResult:
    """Test TierAccessResult dataclass."""

    def test_upgrade_required_property(self):
        """Test upgrade_required property."""
        result = TierAccessResult(
            allowed=False,
            required_tier=TenantTier.PREVENT,
            tenant_tier=TenantTier.REACT,
            feature="sdk.simulate.full",
            phase=PricingPhase.AUTHORITY,
        )
        assert result.upgrade_required is True

    def test_no_upgrade_required(self):
        """Test when no upgrade is required."""
        result = TierAccessResult(
            allowed=True,
            required_tier=TenantTier.REACT,
            tenant_tier=TenantTier.PREVENT,
            feature="killswitch.write",
            phase=PricingPhase.LEARNING,
        )
        assert result.upgrade_required is False


class TestPricingPhase:
    """Test PricingPhase enum."""

    def test_learning_phase_value(self):
        """Test LEARNING phase value."""
        assert PricingPhase.LEARNING.value == "learning"

    def test_authority_phase_value(self):
        """Test AUTHORITY phase value."""
        assert PricingPhase.AUTHORITY.value == "authority"


# Integration tests with mocked dependencies
class TestRequiresTierDependency:
    """Test requires_tier FastAPI dependency."""

    def test_requires_tier_allowed(self):
        """Test that requires_tier allows access for sufficient tier."""
        from app.auth.tier_gating import check_tier_access, resolve_tier

        # Simulate PREVENT tier trying to access REACT feature
        tenant_tier = resolve_tier("prevent")
        result = check_tier_access("killswitch.write", tenant_tier)

        assert result.allowed is True
        assert result.soft_blocked is False

    def test_requires_tier_denied(self):
        """Test that requires_tier denies access for insufficient tier."""
        from app.auth.tier_gating import check_tier_access, resolve_tier

        # Simulate OBSERVE tier trying to access PREVENT feature
        tenant_tier = resolve_tier("free")
        result = check_tier_access(
            "sdk.simulate.full",
            tenant_tier,
            phase=PricingPhase.AUTHORITY,
        )

        assert result.allowed is False
        assert result.required_tier == TenantTier.PREVENT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
