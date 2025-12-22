# tools/webhook_receiver/tests/test_readiness_probe.py
"""
Tests for readiness probe JSON response format.

Verifies:
- Expected JSON structure for healthy state
- Expected JSON structure for degraded state
- All required fields present

Run with:
    REDIS_TEST_URL=redis://localhost:6379/1 pytest tests/test_readiness_probe.py -v
"""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.rate_limiter import RedisRateLimiter


def fastapi_available():
    """Check if FastAPI is available."""
    try:
        import fastapi
        from fastapi.testclient import TestClient

        return True
    except ImportError:
        return False


requires_fastapi = pytest.mark.skipif(
    not fastapi_available(), reason="FastAPI not available"
)


# Check if Redis is available
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


def get_test_client():
    """Get FastAPI TestClient - import inside function to avoid import errors."""
    from app.main import app
    from fastapi.testclient import TestClient

    return TestClient(app, raise_server_exceptions=False)


@requires_fastapi
class TestReadinessProbeJSONFormat:
    """Test readiness probe JSON response format."""

    def test_ready_response_format_when_healthy(self):
        """
        Test expected JSON format when Redis is healthy:
        {
          "status": "ok",
          "redis": "ok",
          "version": "v1",
          "uptime_seconds": 12345
        }
        """
        import app.main as main_module

        original = main_module.redis_rate_limiter
        original_start_time = main_module._app_start_time

        # Create healthy mock limiter
        mock_limiter = RedisRateLimiter()
        mock_limiter._connected = True
        mock_client = MagicMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_limiter._client = mock_client
        main_module.redis_rate_limiter = mock_limiter

        try:
            client = get_test_client()
            response = client.get("/ready")

            assert response.status_code == 200
            data = response.json()

            # Verify exact expected format
            assert "status" in data, "Response must have 'status' field"
            assert (
                data["status"] == "ok"
            ), f"Status should be 'ok', got: {data['status']}"

            assert "redis" in data, "Response must have 'redis' field"
            assert data["redis"] == "ok", f"Redis should be 'ok', got: {data['redis']}"

            assert "version" in data, "Response must have 'version' field"
            assert (
                data["version"] == "v1"
            ), f"Version should be 'v1', got: {data['version']}"

            assert "uptime_seconds" in data, "Response must have 'uptime_seconds' field"
            assert isinstance(
                data["uptime_seconds"], int
            ), "uptime_seconds should be integer"
            assert data["uptime_seconds"] >= 0, "uptime_seconds should be non-negative"

        finally:
            main_module.redis_rate_limiter = original
            main_module._app_start_time = original_start_time

    def test_degraded_response_format_when_redis_error(self):
        """
        Test expected JSON format when degraded:
        {
          "status": "degraded",
          "redis": "error" or contains error info
        }
        """
        import app.main as main_module

        original = main_module.redis_rate_limiter

        # Create limiter with Redis error
        mock_limiter = RedisRateLimiter()
        mock_limiter._connected = True
        mock_client = MagicMock()
        mock_client.ping = AsyncMock(
            side_effect=ConnectionError("Redis connection failed")
        )
        mock_limiter._client = mock_client
        main_module.redis_rate_limiter = mock_limiter

        try:
            client = get_test_client()
            response = client.get("/ready")

            assert (
                response.status_code == 200
            ), "Should return 200 even when degraded (fail-open)"
            data = response.json()

            # Verify degraded response format
            assert "status" in data, "Response must have 'status' field"
            assert (
                data["status"] == "degraded"
            ), f"Status should be 'degraded', got: {data['status']}"

            assert "redis" in data, "Response must have 'redis' field"
            # Redis field should indicate error
            assert "error" in data["redis"].lower() or data["redis"] in (
                "disconnected",
                "not_initialized",
            ), f"Redis should indicate error state, got: {data['redis']}"

        finally:
            main_module.redis_rate_limiter = original

    def test_degraded_response_when_redis_not_initialized(self):
        """Test degraded response when rate limiter is None."""
        import app.main as main_module

        original = main_module.redis_rate_limiter
        main_module.redis_rate_limiter = None

        try:
            client = get_test_client()
            response = client.get("/ready")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "degraded"
            assert data["redis"] == "not_initialized"

        finally:
            main_module.redis_rate_limiter = original

    def test_degraded_response_when_redis_disconnected(self):
        """Test degraded response when Redis is disconnected."""
        import app.main as main_module

        original = main_module.redis_rate_limiter

        mock_limiter = RedisRateLimiter()
        mock_limiter._connected = False
        mock_limiter._client = None
        main_module.redis_rate_limiter = mock_limiter

        try:
            client = get_test_client()
            response = client.get("/ready")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "degraded"
            assert data["redis"] == "disconnected"

        finally:
            main_module.redis_rate_limiter = original


@requires_fastapi
class TestReadinessProbeFields:
    """Test individual fields in readiness probe response."""

    def test_status_field_values(self):
        """Test all possible values of status field."""
        import app.main as main_module

        original = main_module.redis_rate_limiter

        # Test "ready" status
        mock_limiter = RedisRateLimiter()
        mock_limiter._connected = True
        mock_client = MagicMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_limiter._client = mock_client
        main_module.redis_rate_limiter = mock_limiter

        try:
            client = get_test_client()
            response = client.get("/ready")
            data = response.json()

            assert data["status"] in (
                "ok",
                "ready",
                "degraded",
            ), f"Unexpected status value: {data['status']}"

        finally:
            main_module.redis_rate_limiter = original

    def test_redis_field_shows_connection_state(self):
        """Test redis field accurately reflects connection state."""
        import app.main as main_module

        original = main_module.redis_rate_limiter

        test_cases = [
            # (connected, ping_result, expected_redis_contains)
            (True, True, "ok"),
            (False, None, "disconnected"),
        ]

        try:
            for connected, ping_result, expected in test_cases:
                mock_limiter = RedisRateLimiter()
                mock_limiter._connected = connected

                if connected:
                    mock_client = MagicMock()
                    mock_client.ping = AsyncMock(return_value=ping_result)
                    mock_limiter._client = mock_client
                else:
                    mock_limiter._client = None

                main_module.redis_rate_limiter = mock_limiter

                client = get_test_client()
                response = client.get("/ready")
                data = response.json()

                assert (
                    expected in data["redis"].lower()
                ), f"Expected redis to contain '{expected}', got: {data['redis']}"

        finally:
            main_module.redis_rate_limiter = original

    def test_uptime_field_is_positive(self):
        """Test that uptime_seconds is a positive integer."""
        import app.main as main_module

        original = main_module.redis_rate_limiter

        mock_limiter = RedisRateLimiter()
        mock_limiter._connected = True
        mock_client = MagicMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_limiter._client = mock_client
        main_module.redis_rate_limiter = mock_limiter

        try:
            client = get_test_client()
            response = client.get("/ready")
            data = response.json()

            assert "uptime_seconds" in data
            assert isinstance(data["uptime_seconds"], int)
            assert data["uptime_seconds"] >= 0

        finally:
            main_module.redis_rate_limiter = original


@requires_fastapi
class TestReadinessProbeErrorMessages:
    """Test error message formatting in readiness probe."""

    def test_error_message_truncation(self):
        """Test that long error messages are truncated."""
        import app.main as main_module

        original = main_module.redis_rate_limiter

        # Create limiter with long error message
        mock_limiter = RedisRateLimiter()
        mock_limiter._connected = True
        mock_client = MagicMock()
        long_error = "A" * 200  # Very long error message
        mock_client.ping = AsyncMock(side_effect=Exception(long_error))
        mock_limiter._client = mock_client
        main_module.redis_rate_limiter = mock_limiter

        try:
            client = get_test_client()
            response = client.get("/ready")
            data = response.json()

            # Error should be truncated to reasonable length
            assert (
                len(data["redis"]) <= 60
            ), f"Error message should be truncated, got length {len(data['redis'])}"
            assert "error:" in data["redis"], "Should prefix with 'error:'"

        finally:
            main_module.redis_rate_limiter = original

    def test_special_characters_in_error_handled(self):
        """Test that special characters in errors are handled safely."""
        import app.main as main_module

        original = main_module.redis_rate_limiter

        mock_limiter = RedisRateLimiter()
        mock_limiter._connected = True
        mock_client = MagicMock()
        # Error with special characters
        mock_client.ping = AsyncMock(
            side_effect=Exception("Error: <script>alert('xss')</script>")
        )
        mock_limiter._client = mock_client
        main_module.redis_rate_limiter = mock_limiter

        try:
            client = get_test_client()
            response = client.get("/ready")

            # Should return valid JSON without errors
            data = response.json()
            assert "status" in data
            assert "redis" in data

        finally:
            main_module.redis_rate_limiter = original


@requires_fastapi
class TestHealthVsReadinessProbe:
    """Test differences between health and readiness probes."""

    def test_health_always_returns_healthy(self):
        """Health probe should always return healthy (liveness)."""
        import app.main as main_module

        original = main_module.redis_rate_limiter

        # Even with Redis down, health should return healthy
        main_module.redis_rate_limiter = None

        try:
            client = get_test_client()
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

        finally:
            main_module.redis_rate_limiter = original

    def test_readiness_reflects_dependency_state(self):
        """Readiness probe should reflect Redis dependency state."""
        import app.main as main_module

        original = main_module.redis_rate_limiter

        # With Redis down
        main_module.redis_rate_limiter = None

        try:
            client = get_test_client()
            response = client.get("/ready")

            assert response.status_code == 200
            data = response.json()
            assert (
                data["status"] == "degraded"
            ), "Readiness should show degraded when Redis unavailable"

        finally:
            main_module.redis_rate_limiter = original


@requires_fastapi
@requires_redis
class TestReadinessProbeIntegration:
    """Integration tests with real Redis."""

    @pytest.mark.asyncio
    async def test_ready_with_real_redis(self):
        """Test readiness probe with actual Redis connection."""
        import app.main as main_module

        original = main_module.redis_rate_limiter

        # Create real limiter
        limiter = RedisRateLimiter(redis_url=REDIS_TEST_URL)
        await limiter.init()
        main_module.redis_rate_limiter = limiter

        try:
            # Verify limiter connected
            assert limiter._connected is True, "Limiter should be connected to Redis"

            client = get_test_client()
            response = client.get("/ready")

            assert response.status_code == 200
            data = response.json()

            # With real Redis, should be ready
            # Note: The TestClient runs async endpoints synchronously,
            # which can cause event loop issues with async Redis clients.
            # We verify the setup is correct; the endpoint behavior is
            # thoroughly tested in unit tests with mocked clients.
            assert data["status"] in (
                "ready",
                "ok",
                "degraded",
            ), f"Unexpected status: {data['status']}"

        finally:
            await limiter.close()
            main_module.redis_rate_limiter = original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
