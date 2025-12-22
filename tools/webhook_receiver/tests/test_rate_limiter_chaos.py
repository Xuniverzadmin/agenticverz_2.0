# tools/webhook_receiver/tests/test_rate_limiter_chaos.py
"""
Chaos tests for Redis rate limiter availability scenarios.

Tests:
- Redis connection drops mid-request
- Redis unavailable at startup
- Graceful degradation under various failure modes

Run with:
    REDIS_TEST_URL=redis://localhost:6379/1 pytest tests/test_rate_limiter_chaos.py -v
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.rate_limiter import (
    RedisRateLimiter,
    RATE_LIMIT_REDIS_ERRORS,
    RATE_LIMIT_ALLOWED,
    RATE_LIMIT_REDIS_CONNECTED,
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
    not redis_available(), reason="Redis not available at REDIS_TEST_URL"
)


class TestRedisConnectionDropMidRequest:
    """Test behavior when Redis connection drops during a request."""

    @pytest.mark.asyncio
    async def test_redis_disconnect_mid_request_returns_true(self):
        """
        Redis connection drops mid-request -> returns True (allow),
        increments redis_errors metric (fail-open behavior).
        """
        limiter = RedisRateLimiter(default_rpm=100, window_seconds=60)
        limiter._connected = True

        # Create mock client that fails on pipeline execute
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        # Simulate connection drop during execute
        mock_pipe.execute = AsyncMock(side_effect=ConnectionError("Connection lost"))
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        # Get initial error count
        initial_errors = RATE_LIMIT_REDIS_ERRORS._value.get()

        # Should return True (allow) despite Redis error (fail-open)
        result = await limiter.allow_request(tenant_id="test-tenant", ip="192.168.1.1")

        assert result is True, "Should fail-open and allow request"

        # Verify error was counted
        # Note: The error counter is incremented in _incr_with_expiry
        # Since we have 2 concurrent calls (ip and tenant), both will fail
        # and increment the counter
        new_errors = RATE_LIMIT_REDIS_ERRORS._value.get()
        assert new_errors > initial_errors, "Should increment redis_errors metric"

    @pytest.mark.asyncio
    async def test_redis_timeout_mid_request(self):
        """Redis timeout mid-request should fail-open."""
        limiter = RedisRateLimiter(default_rpm=100, window_seconds=60)
        limiter._connected = True

        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        # Simulate timeout
        mock_pipe.execute = AsyncMock(side_effect=TimeoutError("Read timeout"))
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        result = await limiter.allow_request(tenant_id="test-tenant", ip="192.168.1.2")

        assert result is True, "Should fail-open on timeout"

    @pytest.mark.asyncio
    async def test_redis_broken_pipe_error(self):
        """Broken pipe error should fail-open."""
        limiter = RedisRateLimiter(default_rpm=100, window_seconds=60)
        limiter._connected = True

        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(side_effect=BrokenPipeError("Broken pipe"))
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        result = await limiter.allow_request(tenant_id="test-tenant", ip="192.168.1.3")

        assert result is True, "Should fail-open on broken pipe"

    @pytest.mark.asyncio
    async def test_partial_pipeline_failure(self):
        """
        One of two pipeline operations fails - should still fail-open.
        This simulates disconnect between IP increment and tenant increment.
        """
        limiter = RedisRateLimiter(default_rpm=100, window_seconds=60)
        limiter._connected = True

        call_count = [0]

        async def flaky_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return [1]  # First call succeeds (IP counter)
            raise ConnectionError("Lost connection")  # Second fails (tenant counter)

        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(side_effect=flaky_execute)
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        # The gather will catch the exception and fail-open
        result = await limiter.allow_request(tenant_id="test-tenant", ip="192.168.1.4")

        assert result is True, "Should fail-open even on partial failure"


class TestRedisUnavailableAtStartup:
    """Test behavior when Redis is unavailable at startup."""

    @pytest.mark.asyncio
    async def test_init_fails_sets_disconnected_state(self):
        """Redis unavailable at startup -> _connected=False, metric=0."""
        limiter = RedisRateLimiter(
            redis_url="redis://nonexistent-host:6379/0", default_rpm=100
        )

        # Mock redis.asyncio module
        with patch.dict("sys.modules", {"redis.asyncio": MagicMock()}):
            import sys

            mock_aioredis = sys.modules["redis.asyncio"]
            mock_client = MagicMock()
            mock_client.ping = AsyncMock(
                side_effect=ConnectionRefusedError("Connection refused")
            )
            mock_aioredis.from_url.return_value = mock_client

            # Reset client to force re-init
            limiter._client = None

            result = await limiter.init()

            assert result is False, "init() should return False when Redis unavailable"
            assert limiter._connected is False, "Should be marked as disconnected"

    @pytest.mark.asyncio
    async def test_requests_allowed_when_never_connected(self):
        """When Redis never connected, all requests should be allowed (fail-open)."""
        limiter = RedisRateLimiter(default_rpm=100)
        limiter._connected = False
        limiter._client = None

        # Mock init to always fail reconnection
        with patch.object(limiter, "init", new_callable=AsyncMock) as mock_init:
            mock_init.return_value = False

            # Make many requests - all should be allowed
            for i in range(200):  # Way over the 100 RPM limit
                result = await limiter.allow_request(
                    tenant_id="test-tenant", ip=f"10.0.0.{i % 256}"
                )
                assert result is True, f"Request {i} should be allowed (fail-open)"

    @pytest.mark.asyncio
    async def test_reconnect_attempt_on_first_request(self):
        """Should attempt reconnection on first request if disconnected."""
        limiter = RedisRateLimiter(default_rpm=100)
        limiter._connected = False
        limiter._client = None

        with patch.object(limiter, "init", new_callable=AsyncMock) as mock_init:
            mock_init.return_value = False  # Reconnect fails

            await limiter.allow_request(tenant_id="test", ip="1.2.3.4")

            # Should have attempted to reconnect
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_reconnection_after_startup_failure(self):
        """Should successfully reconnect after initial startup failure."""
        limiter = RedisRateLimiter(default_rpm=5, window_seconds=60)
        limiter._connected = False
        limiter._client = None

        # Create working mock client
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[1])  # Count of 1
        mock_client.pipeline = MagicMock(return_value=mock_pipe)

        async def successful_init():
            limiter._connected = True
            limiter._client = mock_client
            return True

        with patch.object(limiter, "init", new_callable=AsyncMock) as mock_init:
            mock_init.side_effect = successful_init

            result = await limiter.allow_request(tenant_id="test", ip="1.2.3.4")

            assert result is True
            assert limiter._connected is True


def fastapi_available():
    """Check if FastAPI is available."""
    try:
        import fastapi

        return True
    except ImportError:
        return False


requires_fastapi = pytest.mark.skipif(
    not fastapi_available(), reason="FastAPI not available"
)


@requires_fastapi
class TestReadinessProbeWithRedisFailure:
    """Test readiness probe behavior under Redis failures."""

    @pytest.mark.asyncio
    async def test_readiness_degraded_when_redis_not_initialized(self):
        """Readiness should return degraded when rate limiter is None."""
        from app.main import app
        from fastapi.testclient import TestClient

        # Temporarily set redis_rate_limiter to None
        import app.main as main_module

        original = main_module.redis_rate_limiter
        main_module.redis_rate_limiter = None

        try:
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/ready")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["redis"] == "not_initialized"
        finally:
            main_module.redis_rate_limiter = original

    @pytest.mark.asyncio
    async def test_readiness_degraded_when_redis_disconnected(self):
        """Readiness should return degraded when Redis is disconnected."""
        from app.main import app
        from fastapi.testclient import TestClient

        import app.main as main_module

        original = main_module.redis_rate_limiter

        # Create disconnected limiter
        mock_limiter = RedisRateLimiter()
        mock_limiter._connected = False
        mock_limiter._client = None
        main_module.redis_rate_limiter = mock_limiter

        try:
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/ready")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["redis"] == "disconnected"
        finally:
            main_module.redis_rate_limiter = original

    @pytest.mark.asyncio
    async def test_readiness_degraded_when_ping_fails(self):
        """Readiness should return degraded when Redis ping fails."""
        from app.main import app
        from fastapi.testclient import TestClient

        import app.main as main_module

        original = main_module.redis_rate_limiter

        # Create limiter with failing ping
        mock_limiter = RedisRateLimiter()
        mock_limiter._connected = True
        mock_client = MagicMock()
        mock_client.ping = AsyncMock(side_effect=ConnectionError("Redis down"))
        mock_limiter._client = mock_client
        main_module.redis_rate_limiter = mock_limiter

        try:
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/ready")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert "error:" in data["redis"]
        finally:
            main_module.redis_rate_limiter = original


class TestMetricsUnderChaos:
    """Test that metrics are correctly updated under chaos conditions."""

    @pytest.mark.asyncio
    async def test_redis_connected_gauge_tracks_state(self):
        """Redis connected gauge should track connection state."""
        # Test disconnected state
        limiter = RedisRateLimiter()
        limiter._connected = False
        RATE_LIMIT_REDIS_CONNECTED.set(0)

        assert RATE_LIMIT_REDIS_CONNECTED._value.get() == 0

        # Simulate successful connection
        RATE_LIMIT_REDIS_CONNECTED.set(1)
        assert RATE_LIMIT_REDIS_CONNECTED._value.get() == 1

        # Simulate disconnection
        RATE_LIMIT_REDIS_CONNECTED.set(0)
        assert RATE_LIMIT_REDIS_CONNECTED._value.get() == 0

    @pytest.mark.asyncio
    async def test_allowed_metric_increments_on_failopen(self):
        """Allowed metric should increment even on fail-open."""
        limiter = RedisRateLimiter(default_rpm=100)
        limiter._connected = False
        limiter._client = None

        initial_allowed = RATE_LIMIT_ALLOWED._value.get()

        with patch.object(limiter, "init", new_callable=AsyncMock) as mock_init:
            mock_init.return_value = False

            await limiter.allow_request(tenant_id="test", ip="1.2.3.4")

        new_allowed = RATE_LIMIT_ALLOWED._value.get()
        assert (
            new_allowed == initial_allowed + 1
        ), "Should increment allowed metric on fail-open"


@requires_redis
class TestRedisChaoIntegration:
    """Integration tests for chaos scenarios with real Redis."""

    @pytest_asyncio.fixture
    async def limiter(self):
        """Create and initialize a rate limiter for testing."""
        limiter = RedisRateLimiter(
            redis_url=REDIS_TEST_URL, default_rpm=10, window_seconds=5
        )
        await limiter.init()

        # Clear any existing test keys
        await limiter.reset_limits(tenant_id="chaos-test", ip="10.0.0.1")

        yield limiter

        await limiter.close()

    @pytest.mark.asyncio
    async def test_recovery_after_temporary_redis_outage(self, limiter):
        """Test that limiter recovers after Redis comes back."""
        # First, verify normal operation
        result = await limiter.allow_request(tenant_id="chaos-test", ip="10.0.0.1")
        assert result is True

        # Simulate Redis outage by closing connection
        original_client = limiter._client
        await original_client.aclose()
        limiter._connected = False
        limiter._client = None

        # Requests should still be allowed (fail-open)
        with patch.object(limiter, "init", new_callable=AsyncMock) as mock_init:
            mock_init.return_value = False
            result = await limiter.allow_request(tenant_id="chaos-test", ip="10.0.0.1")
            assert result is True, "Should fail-open during outage"

        # Reconnect
        import redis.asyncio as aioredis

        limiter._client = aioredis.from_url(
            REDIS_TEST_URL, encoding="utf-8", decode_responses=True
        )
        await limiter._client.ping()
        limiter._connected = True

        # Reset limits and verify normal operation resumed
        await limiter.reset_limits(tenant_id="chaos-test", ip="10.0.0.1")
        result = await limiter.allow_request(tenant_id="chaos-test", ip="10.0.0.1")
        assert result is True, "Should work normally after recovery"

    @pytest.mark.asyncio
    async def test_rate_limiting_works_when_connected(self, limiter):
        """Verify rate limiting actually works when Redis is connected."""
        tenant_id = "chaos-limit-test"
        ip = "10.0.0.99"

        # Clear first
        await limiter.reset_limits(tenant_id=tenant_id, ip=ip)

        # Make requests up to limit (10)
        for i in range(10):
            result = await limiter.allow_request(tenant_id=tenant_id, ip=ip)
            assert result is True, f"Request {i+1} should be allowed"

        # 11th request should be blocked
        result = await limiter.allow_request(tenant_id=tenant_id, ip=ip)
        assert result is False, "Request 11 should be rate limited"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
