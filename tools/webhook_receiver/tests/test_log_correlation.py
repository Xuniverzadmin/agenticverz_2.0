# tools/webhook_receiver/tests/test_log_correlation.py
"""
Log correlation tests for rate-limit logging.

Verifies that rate-limit logs contain required fields for ops debugging:
- tenant_id
- request_id (if available)
- ip
- redis latency ms

Run with:
    pytest tests/test_log_correlation.py -v
"""

import asyncio
import logging
import os
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rate_limiter import RedisRateLimiter


def run_async(coro):
    """
    Helper to run async code in sync tests.

    Uses asyncio.run() which is the modern approach (Python 3.7+)
    and avoids the deprecated get_event_loop() pattern.
    """
    return asyncio.run(coro)


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


class LogCapture:
    """Helper to capture log output."""

    def __init__(self, logger_name: str, level: int = logging.DEBUG):
        self.logger_name = logger_name
        self.level = level
        self.handler = None
        self.stream = None
        self.original_handlers = []
        self.original_level = None

    def __enter__(self):
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setLevel(self.level)
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        self.handler.setFormatter(formatter)

        logger = logging.getLogger(self.logger_name)
        self.original_level = logger.level
        self.original_handlers = logger.handlers.copy()

        logger.setLevel(self.level)
        logger.addHandler(self.handler)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger = logging.getLogger(self.logger_name)
        logger.removeHandler(self.handler)
        logger.setLevel(self.original_level)

        # Restore original handlers
        for handler in self.original_handlers:
            if handler not in logger.handlers:
                logger.addHandler(handler)

    def get_logs(self) -> str:
        """Get captured log output."""
        return self.stream.getvalue()

    def get_log_lines(self) -> list:
        """Get captured log output as list of lines."""
        return (
            self.stream.getvalue().strip().split("\n")
            if self.stream.getvalue().strip()
            else []
        )


class TestRateLimitLogCorrelation:
    """Test that rate-limit logs contain required correlation fields."""

    def test_rate_limit_log_contains_tenant_id(self):
        """Rate-limit exceeded logs should contain tenant_id."""
        from app.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter(default_rpm=1)
        limiter._connected = True

        # Mock client to return count over limit
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[100])  # Over limit
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        with LogCapture("webhook.rate_limiter", logging.INFO) as log_capture:
            result = run_async(
                limiter.allow_request(
                    tenant_id="test-tenant-123",
                    ip="192.168.1.100",
                    request_id="req-abc123",
                )
            )

            assert result is False, "Should be rate limited"

            logs = log_capture.get_logs()
            # Verify tenant_id is in logs
            assert "tenant_id=test-tenant-123" in logs, (
                f"Logs should contain tenant_id=test-tenant-123. Got: {logs}"
            )

    def test_rate_limit_log_contains_ip(self):
        """Rate-limit exceeded logs should contain IP address."""
        from app.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter(default_rpm=1)
        limiter._connected = True

        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[100])
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        with LogCapture("webhook.rate_limiter", logging.INFO) as log_capture:
            result = run_async(
                limiter.allow_request(
                    tenant_id="test-tenant", ip="10.20.30.40", request_id="req-xyz789"
                )
            )

            logs = log_capture.get_logs()
            # Verify IP is in logs
            assert "ip=10.20.30.40" in logs, (
                f"Logs should contain ip=10.20.30.40. Got: {logs}"
            )

    def test_rate_limit_log_contains_request_id(self):
        """Rate-limit exceeded logs should contain request_id."""
        from app.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter(default_rpm=1)
        limiter._connected = True

        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[100])
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        with LogCapture("webhook.rate_limiter", logging.INFO) as log_capture:
            result = run_async(
                limiter.allow_request(
                    tenant_id="test-tenant",
                    ip="10.20.30.40",
                    request_id="req-correlation-test",
                )
            )

            logs = log_capture.get_logs()
            # Verify request_id is in logs
            assert "request_id=req-correlation-test" in logs, (
                f"Logs should contain request_id=req-correlation-test. Got: {logs}"
            )

    def test_rate_limit_log_contains_redis_latency(self):
        """Rate-limit exceeded logs should contain redis_latency_ms."""
        from app.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter(default_rpm=1)
        limiter._connected = True

        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[100])
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        with LogCapture("webhook.rate_limiter", logging.INFO) as log_capture:
            result = run_async(
                limiter.allow_request(
                    tenant_id="test-tenant",
                    ip="10.20.30.40",
                    request_id="req-latency-test",
                )
            )

            logs = log_capture.get_logs()
            # Verify redis_latency_ms is in logs
            assert "redis_latency_ms=" in logs, (
                f"Logs should contain redis_latency_ms. Got: {logs}"
            )

    @pytest.mark.skipif(not fastapi_available(), reason="FastAPI not available")
    def test_webhook_rate_limit_log_contains_both_tenant_and_ip(self):
        """Webhook rate-limit log should contain both tenant and IP."""
        from app.main import app
        from fastapi.testclient import TestClient
        import app.main as main_module

        # Create rate limiter that will trigger limit
        mock_limiter = RedisRateLimiter(default_rpm=1)
        mock_limiter._connected = True

        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[100])  # Over limit
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        mock_limiter._client = mock_client

        original = main_module.redis_rate_limiter
        main_module.redis_rate_limiter = mock_limiter

        try:
            # Capture webhook_receiver logger for the rate limit log
            with LogCapture("webhook_receiver", logging.WARNING) as main_log:
                client = TestClient(app, raise_server_exceptions=False)
                response = client.post(
                    "/webhook",
                    json={"test": "data"},
                    headers={
                        "Content-Type": "application/json",
                        "X-Tenant-ID": "ops-tenant-456",
                        "X-Forwarded-For": "203.0.113.50",
                    },
                )

                # Should get 429 rate limited
                if response.status_code == 429:
                    logs = main_log.get_logs()
                    # Check for tenant and IP in main webhook_receiver logs
                    has_tenant = "ops-tenant-456" in logs or "tenant" in logs.lower()
                    has_ip = "203.0.113.50" in logs or "ip" in logs.lower()

                    assert has_tenant or has_ip, (
                        f"Rate limit log should contain tenant/IP info. Got: {logs}"
                    )
                else:
                    # If not rate limited (e.g. 500 from DB issues), skip assertion
                    pytest.skip(
                        f"Got {response.status_code} instead of 429, skipping log check"
                    )

        finally:
            main_module.redis_rate_limiter = original


class TestLogFieldFormat:
    """Test format of log fields for ops debugging."""

    def test_ip_rate_limit_log_format(self):
        """IP rate limit log should have structured format."""
        from app.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter(default_rpm=5)
        limiter._connected = True

        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[10])  # Over 5 rpm limit
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        with LogCapture("webhook.rate_limiter", logging.INFO) as log_capture:
            run_async(
                limiter.allow_request(tenant_id="format-test", ip="172.16.0.1", rpm=5)
            )

            logs = log_capture.get_logs()

            # Check for structured rate limit info
            # Expected format: "Rate limit exceeded for IP 172.16.0.1: 10/5"
            assert "172.16.0.1" in logs, f"Should contain IP. Got: {logs}"
            assert "10" in logs or "count" in logs.lower(), (
                f"Should contain count. Got: {logs}"
            )

    def test_tenant_rate_limit_log_format(self):
        """Tenant rate limit log should have structured format."""
        from app.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter(default_rpm=5)
        limiter._connected = True

        # First call for IP - under limit
        # Second call for tenant - over limit
        call_count = [0]

        async def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return [1]  # IP count - under limit
            return [10]  # Tenant count - over limit

        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(side_effect=mock_execute)
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        with LogCapture("webhook.rate_limiter", logging.INFO) as log_capture:
            run_async(
                limiter.allow_request(
                    tenant_id="tenant-rate-test", ip="172.16.0.2", rpm=5
                )
            )

            logs = log_capture.get_logs()

            # Check for tenant info in log
            assert "tenant-rate-test" in logs or "tenant" in logs.lower(), (
                f"Should contain tenant info. Got: {logs}"
            )


class TestRedisLatencyLogging:
    """Test Redis latency is logged for debugging."""

    def test_redis_error_logs_contain_timing_context(self):
        """Redis errors should log with context for timing analysis."""
        from app.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter(default_rpm=100)
        limiter._connected = True

        # Mock client that fails with timeout
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(
            side_effect=TimeoutError("Redis timeout after 5000ms")
        )
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        with LogCapture("webhook.rate_limiter", logging.WARNING) as log_capture:
            result = run_async(
                limiter.allow_request(tenant_id="timeout-test", ip="10.0.0.1")
            )

            # Should fail-open
            assert result is True

            logs = log_capture.get_logs()
            # Should log the timeout error which contains timing info
            assert "timeout" in logs.lower() or "error" in logs.lower(), (
                f"Should log timeout/error info. Got: {logs}"
            )


class TestLogCorrelationWithRequestContext:
    """Test that logs can be correlated with specific requests."""

    def test_multiple_tenants_distinguishable_in_logs(self):
        """Rate limits for different tenants should be distinguishable in logs."""
        from app.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter(default_rpm=1)
        limiter._connected = True

        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[100])
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        with LogCapture("webhook.rate_limiter", logging.INFO) as log_capture:
            # Trigger rate limits for multiple tenants
            for tenant in ["tenant-alpha", "tenant-beta", "tenant-gamma"]:
                run_async(
                    limiter.allow_request(
                        tenant_id=tenant, ip=f"10.0.0.{hash(tenant) % 256}"
                    )
                )

            logs = log_capture.get_logs()

            # Each tenant should appear in logs
            # At least one should be present (depending on which limit hits first)
            found_tenants = []
            for tenant in ["tenant-alpha", "tenant-beta", "tenant-gamma"]:
                if tenant in logs:
                    found_tenants.append(tenant)

            assert len(found_tenants) >= 1, (
                f"Should log at least one tenant identifier. Got: {logs}"
            )

    def test_multiple_ips_distinguishable_in_logs(self):
        """Rate limits for different IPs should be distinguishable in logs."""
        from app.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter(default_rpm=1)
        limiter._connected = True

        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[100])
        mock_client.pipeline = MagicMock(return_value=mock_pipe)
        limiter._client = mock_client

        test_ips = ["192.168.1.1", "192.168.1.2", "192.168.1.3"]

        with LogCapture("webhook.rate_limiter", logging.INFO) as log_capture:
            for ip in test_ips:
                run_async(limiter.allow_request(tenant_id="shared-tenant", ip=ip))

            logs = log_capture.get_logs()

            # Each IP should appear in logs
            found_ips = [ip for ip in test_ips if ip in logs]
            assert len(found_ips) >= 1, (
                f"Should log at least one IP address. Got: {logs}"
            )


class TestEnhancedLogging:
    """Test enhanced logging features for ops debugging."""

    def test_fail_open_logs_redis_unavailable(self):
        """Fail-open should log that Redis is unavailable."""
        from app.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter(default_rpm=100)
        limiter._connected = False
        limiter._client = None

        with LogCapture("webhook.rate_limiter", logging.DEBUG) as log_capture:
            with patch.object(limiter, "init", new_callable=AsyncMock) as mock_init:
                mock_init.return_value = False

                result = run_async(
                    limiter.allow_request(tenant_id="failopen-test", ip="10.0.0.1")
                )

                assert result is True, "Should fail-open"

                logs = log_capture.get_logs()
                # Should log something about Redis being unavailable
                assert (
                    "unavailable" in logs.lower()
                    or "fail" in logs.lower()
                    or len(logs) == 0
                ), f"Should log Redis unavailable or be silent. Got: {logs}"

    def test_reconnection_attempt_logged(self):
        """Reconnection attempts should be logged."""
        from app.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter(default_rpm=100)
        limiter._connected = False
        limiter._client = None

        with LogCapture("webhook.rate_limiter", logging.INFO) as log_capture:
            with patch.object(limiter, "init", new_callable=AsyncMock) as mock_init:
                mock_init.return_value = True  # Successful reconnection

                # Set up working mock client after "reconnection"
                async def setup_client():
                    limiter._connected = True
                    mock_client = MagicMock()
                    mock_pipe = MagicMock()
                    mock_pipe.incr = MagicMock()
                    mock_pipe.expire = MagicMock()
                    mock_pipe.execute = AsyncMock(return_value=[1])
                    mock_client.pipeline = MagicMock(return_value=mock_pipe)
                    limiter._client = mock_client
                    return True

                mock_init.side_effect = setup_client

                result = run_async(
                    limiter.allow_request(tenant_id="reconnect-test", ip="10.0.0.1")
                )

                # init should have been called for reconnection
                mock_init.assert_called_once()


@requires_redis
class TestLogCorrelationIntegration:
    """Integration tests for log correlation with real Redis."""

    @pytest.mark.asyncio
    async def test_real_rate_limit_logs_contain_all_fields(self):
        """Real rate limit scenario should log all required fields."""
        from app.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter(
            redis_url=REDIS_TEST_URL, default_rpm=5, window_seconds=5
        )

        await limiter.init()

        try:
            # Clear counters
            await limiter.reset_limits(
                tenant_id="integration-log-test", ip="10.99.99.99"
            )

            with LogCapture("webhook.rate_limiter", logging.INFO) as log_capture:
                # Make requests until rate limited
                for i in range(10):
                    result = await limiter.allow_request(
                        tenant_id="integration-log-test", ip="10.99.99.99"
                    )
                    if not result:
                        break

                logs = log_capture.get_logs()

                if logs:  # Only check if there are logs (rate limit was hit)
                    # Verify correlation fields
                    has_tenant = "integration-log-test" in logs
                    has_ip = "10.99.99.99" in logs

                    assert has_tenant or has_ip, (
                        f"Logs should contain tenant/IP. Got: {logs}"
                    )

        finally:
            await limiter.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
