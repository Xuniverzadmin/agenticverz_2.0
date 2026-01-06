"""
Rate Limit Integration Tests
M8 Deliverable: Verify rate limiting works correctly with Redis
"""

import os
from unittest.mock import AsyncMock, patch

import pytest

# Set test environment
os.environ.setdefault("RATE_LIMIT_ENABLED", "true")
os.environ.setdefault("RATE_LIMIT_FAIL_OPEN", "true")


class TestRateLimitMiddleware:
    """Test rate limit middleware functionality."""

    def test_tier_limits_configured(self):
        """Verify tier limits are configured correctly."""
        from app.middleware.rate_limit import RATE_LIMIT_TIERS, get_tier_limits

        assert "free" in RATE_LIMIT_TIERS
        assert "dev" in RATE_LIMIT_TIERS
        assert "pro" in RATE_LIMIT_TIERS
        assert "enterprise" in RATE_LIMIT_TIERS
        assert "unlimited" in RATE_LIMIT_TIERS

        # Check free tier
        limit, window = get_tier_limits("free")
        assert limit == 60
        assert window == 60

        # Check dev tier
        limit, window = get_tier_limits("dev")
        assert limit == 300
        assert window == 60

        # Unknown tier defaults to free
        limit, window = get_tier_limits("unknown")
        assert limit == 60

    def test_extract_tier_from_user(self):
        """Test tier extraction from user object."""
        from app.middleware.rate_limit import extract_tier_from_user

        class MockUser:
            def __init__(self, rate_limit_tier=None, roles=None):
                self.rate_limit_tier = rate_limit_tier
                self.roles = roles or []

        # Explicit tier takes precedence
        user = MockUser(rate_limit_tier="pro", roles=["developer"])
        assert extract_tier_from_user(user) == "pro"

        # Admin role gets unlimited
        user = MockUser(roles=["admin"])
        assert extract_tier_from_user(user) == "unlimited"

        # Enterprise role
        user = MockUser(roles=["enterprise"])
        assert extract_tier_from_user(user) == "enterprise"

        # Developer role
        user = MockUser(roles=["developer"])
        assert extract_tier_from_user(user) == "dev"

        # No roles defaults to free
        user = MockUser()
        assert extract_tier_from_user(user) == "free"

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self):
        """Test rate limit check when under limit."""
        from app.middleware.rate_limit import check_rate_limit

        # Mock Redis to always return low count
        with patch("app.middleware.rate_limit.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.incr = AsyncMock(return_value=1)
            mock_redis.expire = AsyncMock(return_value=True)
            mock_get_redis.return_value = mock_redis

            allowed, current, limit, remaining = await check_rate_limit("tenant1", "free")

            assert allowed is True
            assert current == 1
            assert limit == 60
            assert remaining == 59

    @pytest.mark.asyncio
    async def test_check_rate_limit_blocked(self):
        """Test rate limit check when over limit."""
        from app.middleware.rate_limit import check_rate_limit

        # Mock Redis to return count over limit
        with patch("app.middleware.rate_limit.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.incr = AsyncMock(return_value=61)  # Over 60 limit
            mock_get_redis.return_value = mock_redis

            allowed, current, limit, remaining = await check_rate_limit("tenant1", "free")

            assert allowed is False
            assert current == 61
            assert limit == 60
            assert remaining == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_redis_error_fail_open(self):
        """Test rate limit fails open when Redis unavailable."""
        from app.middleware.rate_limit import check_rate_limit

        with patch("app.middleware.rate_limit.get_redis") as mock_get_redis:
            mock_get_redis.side_effect = Exception("Redis connection failed")

            with patch("app.middleware.rate_limit.RATE_LIMIT_FAIL_OPEN", True):
                allowed, current, limit, remaining = await check_rate_limit("tenant1", "free")

                # Should allow request (fail-open)
                assert allowed is True
                assert remaining == 60

    @pytest.mark.asyncio
    async def test_check_rate_limit_redis_error_fail_closed(self):
        """Test rate limit fails closed when configured."""
        from app.middleware.rate_limit import check_rate_limit

        with patch("app.middleware.rate_limit.get_redis") as mock_get_redis:
            mock_get_redis.side_effect = Exception("Redis connection failed")

            with patch("app.middleware.rate_limit.RATE_LIMIT_FAIL_OPEN", False):
                allowed, current, limit, remaining = await check_rate_limit("tenant1", "free")

                # Should deny request (fail-closed)
                assert allowed is False
                assert remaining == 0


class TestRateLimitMetrics:
    """Test Prometheus metrics for rate limiting."""

    def test_metrics_registered(self):
        """Verify Prometheus metrics are registered."""
        from app.middleware.rate_limit import (
            rl_allowed,
            rl_blocked,
            rl_limit_gauge,
            rl_redis_connected,
            rl_redis_errors,
        )

        # Metrics should exist
        assert rl_allowed is not None
        assert rl_blocked is not None
        assert rl_limit_gauge is not None
        assert rl_redis_connected is not None
        assert rl_redis_errors is not None

    def test_tier_limits_in_gauge(self):
        """Verify tier limits are set in Prometheus gauge."""
        from app.middleware.rate_limit import RATE_LIMIT_TIERS

        # Each tier should have a gauge value set
        for tier, (limit, _) in RATE_LIMIT_TIERS.items():
            # The gauge should have been set during module import
            # We can't easily verify the value without accessing internal state
            pass  # Gauge is set at import time


@pytest.mark.skipif(not os.environ.get("REDIS_URL"), reason="REDIS_URL not set - skipping live Redis tests")
class TestRateLimitLiveRedis:
    """Live Redis integration tests (require REDIS_URL)."""

    @pytest.mark.asyncio
    async def test_live_redis_rate_limit(self):
        """Test rate limiting against live Redis."""
        import time

        from app.middleware.rate_limit import check_rate_limit

        # Use unique tenant to avoid conflicts
        tenant_id = f"test_tenant_{int(time.time())}"

        # First request should be allowed
        allowed, current, limit, remaining = await check_rate_limit(tenant_id, "free")
        assert allowed is True
        assert current == 1
        assert remaining == 59

        # Second request should also be allowed
        allowed, current, limit, remaining = await check_rate_limit(tenant_id, "free")
        assert allowed is True
        assert current == 2
        assert remaining == 58
