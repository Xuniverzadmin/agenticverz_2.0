# tools/webhook_receiver/tests/test_rate_limiter.py
"""
Unit tests for Redis-backed rate limiter.

Run with:
    REDIS_TEST_URL=redis://localhost:6379/1 pytest tests/test_rate_limiter.py -v

Or run without Redis (tests fail-open behavior):
    pytest tests/test_rate_limiter.py -v -k "not requires_redis"
"""

import asyncio
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Import rate limiter
from app.rate_limiter import (
    RedisRateLimiter,
    get_rate_limiter,
    init_rate_limiter,
    RATE_LIMIT_EXCEEDED,
    RATE_LIMIT_REDIS_ERRORS,
    RATE_LIMIT_ALLOWED,
    RATE_LIMIT_REDIS_CONNECTED,
    RATE_LIMIT_REDIS_LATENCY,
)


# Check if Redis is available for integration tests
REDIS_TEST_URL = os.getenv("REDIS_TEST_URL", "redis://localhost:6379/1")


def redis_available():
    """Check if Redis is available for testing."""
    try:
        import redis
        client = redis.from_url(REDIS_TEST_URL, socket_connect_timeout=1)
        client.ping()
        client.close()
        return True
    except Exception:
        return False


requires_redis = pytest.mark.skipif(
    not redis_available(),
    reason="Redis not available at REDIS_TEST_URL"
)


class TestRedisRateLimiterUnit:
    """Unit tests that don't require Redis."""

    def test_init_defaults(self):
        """Test default initialization."""
        limiter = RedisRateLimiter()
        assert limiter.default_rpm == 100
        assert limiter.window_seconds == 60
        assert limiter._client is None
        assert limiter._connected is False

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        limiter = RedisRateLimiter(
            redis_url="redis://custom:6379/5",
            default_rpm=50,
            window_seconds=30
        )
        assert limiter.redis_url == "redis://custom:6379/5"
        assert limiter.default_rpm == 50
        assert limiter.window_seconds == 30

    @pytest.mark.asyncio
    async def test_fail_open_when_not_connected(self):
        """Test that requests are allowed when Redis is not connected."""
        limiter = RedisRateLimiter(redis_url="redis://nonexistent:6379/0")
        limiter._connected = False
        limiter._client = None

        # Should return True (allow) even though Redis is not connected
        with patch.object(limiter, 'init', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = False  # Simulate failed reconnection
            result = await limiter.allow_request(
                tenant_id="test-tenant",
                ip="1.2.3.4",
                rpm=100
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_fail_open_on_redis_error(self):
        """Test fail-open behavior when Redis operations fail."""
        limiter = RedisRateLimiter()
        limiter._connected = True

        # Create mock client that raises errors
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(side_effect=Exception("Redis error"))
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        # Should return True (allow) despite Redis error
        result = await limiter.allow_request(
            tenant_id="test-tenant",
            ip="1.2.3.4"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_get_current_counts_not_connected(self):
        """Test get_current_counts when not connected."""
        limiter = RedisRateLimiter()
        limiter._connected = False

        result = await limiter.get_current_counts("tenant", "1.2.3.4")
        assert result["error"] == "not_connected"
        assert result["ip_count"] == -1
        assert result["tenant_count"] == -1

    @pytest.mark.asyncio
    async def test_close_when_not_connected(self):
        """Test close when already disconnected."""
        limiter = RedisRateLimiter()
        limiter._connected = False
        limiter._client = None

        # Should not raise
        await limiter.close()
        assert limiter._connected is False

    @pytest.mark.asyncio
    async def test_reset_limits_when_not_connected(self):
        """Test reset_limits when not connected."""
        limiter = RedisRateLimiter()
        limiter._connected = False

        # Should not raise
        await limiter.reset_limits(tenant_id="test", ip="1.2.3.4")


class TestSingletonPattern:
    """Test singleton pattern for rate limiter."""

    def test_get_rate_limiter_returns_singleton(self):
        """Test that get_rate_limiter returns the same instance."""
        # Reset singleton for test
        import app.rate_limiter as rl_module
        rl_module._rate_limiter = None

        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2

    @pytest.mark.asyncio
    async def test_init_rate_limiter(self):
        """Test init_rate_limiter function."""
        import app.rate_limiter as rl_module
        rl_module._rate_limiter = None

        with patch.object(RedisRateLimiter, 'init', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = True
            limiter = await init_rate_limiter()
            assert limiter is not None
            mock_init.assert_called_once()


@requires_redis
class TestRedisRateLimiterIntegration:
    """Integration tests that require a real Redis connection."""

    @pytest_asyncio.fixture
    async def limiter(self):
        """Create and initialize a rate limiter for testing."""
        limiter = RedisRateLimiter(
            redis_url=REDIS_TEST_URL,
            default_rpm=10,  # Low limit for testing
            window_seconds=5  # Short window for testing
        )
        await limiter.init()

        # Clear any existing test keys
        await limiter.reset_limits(tenant_id="test-tenant", ip="10.0.0.1")

        yield limiter

        # Cleanup
        await limiter.close()

    @pytest.mark.asyncio
    async def test_init_connects_to_redis(self, limiter):
        """Test that init connects to Redis."""
        assert limiter._connected is True
        assert limiter._client is not None

    @pytest.mark.asyncio
    async def test_allow_request_increments_counter(self, limiter):
        """Test that allow_request increments counters."""
        # First request should be allowed
        result = await limiter.allow_request(
            tenant_id="test-tenant",
            ip="10.0.0.1"
        )
        assert result is True

        # Check counts
        counts = await limiter.get_current_counts("test-tenant", "10.0.0.1")
        assert counts["ip_count"] == 1
        assert counts["tenant_count"] == 1

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_by_ip(self, limiter):
        """Test that IP-based rate limiting works."""
        tenant_id = "test-tenant-ip"
        ip = "10.0.0.2"

        # Make requests up to the limit
        for i in range(10):
            result = await limiter.allow_request(tenant_id=tenant_id, ip=ip)
            assert result is True, f"Request {i+1} should be allowed"

        # Next request should be rate limited
        result = await limiter.allow_request(tenant_id=tenant_id, ip=ip)
        assert result is False, "Request 11 should be rate limited"

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_by_tenant(self, limiter):
        """Test that tenant-based rate limiting works."""
        tenant_id = "test-tenant-limit"

        # Make requests from different IPs but same tenant
        for i in range(10):
            ip = f"10.0.1.{i}"
            result = await limiter.allow_request(tenant_id=tenant_id, ip=ip)
            assert result is True, f"Request {i+1} should be allowed"

        # Next request should be rate limited (tenant limit exceeded)
        result = await limiter.allow_request(tenant_id=tenant_id, ip="10.0.1.99")
        assert result is False, "Request 11 should be rate limited by tenant"

    @pytest.mark.asyncio
    async def test_different_tenants_independent(self, limiter):
        """Test that different tenants have independent limits."""
        ip = "10.0.0.3"

        # Fill up tenant1's limit
        for i in range(10):
            result = await limiter.allow_request(tenant_id="tenant1", ip=ip)
            assert result is True

        # tenant1 should be rate limited
        result = await limiter.allow_request(tenant_id="tenant1", ip=ip)
        assert result is False

        # tenant2 should still be allowed (different tenant counter)
        result = await limiter.allow_request(tenant_id="tenant2", ip="10.0.0.4")
        assert result is True

    @pytest.mark.asyncio
    async def test_custom_rpm_limit(self, limiter):
        """Test custom RPM limit per request."""
        tenant_id = "test-custom-rpm"
        ip = "10.0.0.5"

        # With custom limit of 5
        for i in range(5):
            result = await limiter.allow_request(
                tenant_id=tenant_id,
                ip=ip,
                rpm=5
            )
            assert result is True

        # 6th request should be rate limited
        result = await limiter.allow_request(
            tenant_id=tenant_id,
            ip=ip,
            rpm=5
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_reset_limits_clears_counters(self, limiter):
        """Test that reset_limits clears counters."""
        tenant_id = "test-reset-unique"
        ip = "10.0.99.6"

        # First clear any existing counters to ensure test isolation
        await limiter.reset_limits(tenant_id=tenant_id, ip=ip)

        # Make some requests
        for _ in range(5):
            await limiter.allow_request(tenant_id=tenant_id, ip=ip)

        # Verify counts
        counts = await limiter.get_current_counts(tenant_id, ip)
        assert counts["ip_count"] == 5

        # Reset
        await limiter.reset_limits(tenant_id=tenant_id, ip=ip)

        # Counts should be 0
        counts = await limiter.get_current_counts(tenant_id, ip)
        assert counts["ip_count"] == 0
        assert counts["tenant_count"] == 0

    @pytest.mark.asyncio
    async def test_window_expires(self, limiter):
        """Test that counters expire after window."""
        tenant_id = "test-expire"
        ip = "10.0.0.7"

        # Fill up limit
        for _ in range(10):
            await limiter.allow_request(tenant_id=tenant_id, ip=ip)

        # Should be rate limited
        result = await limiter.allow_request(tenant_id=tenant_id, ip=ip)
        assert result is False

        # Wait for window to expire (window is 5 seconds in test fixture)
        await asyncio.sleep(6)

        # Should be allowed again
        result = await limiter.allow_request(tenant_id=tenant_id, ip=ip)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_current_counts(self, limiter):
        """Test get_current_counts returns accurate info."""
        tenant_id = "test-counts"
        ip = "10.0.0.8"

        # Make 3 requests
        for _ in range(3):
            await limiter.allow_request(tenant_id=tenant_id, ip=ip)

        counts = await limiter.get_current_counts(tenant_id, ip)
        assert counts["ip_count"] == 3
        assert counts["tenant_count"] == 3
        assert counts["rpm_limit"] == 10
        assert "window" in counts


class TestPrometheusMetrics:
    """Test Prometheus metrics are properly defined."""

    def test_metrics_exist(self):
        """Test that all expected metrics are defined."""
        assert RATE_LIMIT_EXCEEDED is not None
        assert RATE_LIMIT_REDIS_ERRORS is not None
        assert RATE_LIMIT_ALLOWED is not None
        assert RATE_LIMIT_REDIS_CONNECTED is not None
        assert RATE_LIMIT_REDIS_LATENCY is not None

    def test_rate_limit_exceeded_has_labels(self):
        """Test RATE_LIMIT_EXCEEDED has correct labels."""
        # Access the metric's label names
        assert "limit_type" in RATE_LIMIT_EXCEEDED._labelnames

    @pytest.mark.asyncio
    async def test_metrics_increment_on_rate_limit(self):
        """Test that metrics increment when rate limit is exceeded."""
        limiter = RedisRateLimiter(default_rpm=2, window_seconds=60)
        limiter._connected = True

        # Mock Redis client to return high counts
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        # Return counts that exceed limit
        mock_pipe.execute = AsyncMock(return_value=[100, 100])
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        # This should trigger rate limit exceeded
        result = await limiter.allow_request(
            tenant_id="test",
            ip="1.2.3.4",
            rpm=10
        )

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
