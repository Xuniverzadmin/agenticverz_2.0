# tests/chaos/test_http_call_chaos.py
"""
Chaos Tests for HTTP Call Skill

Tests retry behavior under various failure conditions:
- Transient failures (503, 502)
- Rate limiting (429)
- Timeouts
- Connection errors
- Deterministic retry with seeded backoff

These tests validate error_contract.md compliance.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# Path setup
_backend = Path(__file__).parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.skills.http_call_v2 import (
    http_call_execute,
    compute_retry_delay,
    RetryConfig,
    HTTP_ERROR_MAP,
    NETWORK_ERROR_MAP,
    ErrorCategory,
    MockResponse,
    set_mock_response,
    clear_mock_responses,
)


class TestTransientFailureRetry:
    """Test retry behavior for transient failures."""

    @pytest.fixture(autouse=True)
    def setup(self):
        clear_mock_responses()
        yield
        clear_mock_responses()

    @pytest.mark.asyncio
    async def test_503_triggers_retry(self):
        """503 Service Unavailable should trigger retry."""
        # First call: 503, second call: 200
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (503, {}, {"error": "Service Unavailable"}, 100)
            return (200, {}, {"success": True}, 50)

        with patch('app.skills.http_call_v2._make_request', mock_request):
            result = await http_call_execute({
                "url": "https://api.example.com/data",
                "retry_config": {"max_retries": 3, "initial_delay_ms": 1}
            })

        assert result.ok is True
        assert result.result["retries"] == 1
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_502_triggers_retry(self):
        """502 Bad Gateway should trigger retry."""
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return (502, {}, {"error": "Bad Gateway"}, 100)
            return (200, {}, {"success": True}, 50)

        with patch('app.skills.http_call_v2._make_request', mock_request):
            result = await http_call_execute({
                "url": "https://api.example.com/data",
                "retry_config": {"max_retries": 3, "initial_delay_ms": 1}
            })

        assert result.ok is True
        assert result.result["retries"] == 2

    @pytest.mark.asyncio
    async def test_exhausted_retries_returns_error(self):
        """After exhausting retries, return structured error."""
        async def always_fail(*args, **kwargs):
            return (503, {}, {"error": "Always fail"}, 100)

        with patch('app.skills.http_call_v2._make_request', always_fail):
            result = await http_call_execute({
                "url": "https://api.example.com/data",
                "retry_config": {"max_retries": 2, "initial_delay_ms": 1}
            })

        assert result.ok is False
        assert result.error["code"] == "ERR_HTTP_503_UNAVAILABLE"
        # Note: retryable reflects the error type, not whether retries were exhausted
        # The error type 503 is inherently retryable; caller used up their retry budget
        assert result.error["retryable"] is True  # Error type is retryable
        assert result.error["details"]["retries"] == 2  # But we exhausted our budget


class TestRateLimitHandling:
    """Test rate limit (429) handling."""

    @pytest.mark.asyncio
    async def test_429_triggers_retry(self):
        """429 Too Many Requests should trigger retry."""
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (429, {"Retry-After": "1"}, {"error": "Rate limited"}, 50)
            return (200, {}, {"success": True}, 50)

        with patch('app.skills.http_call_v2._make_request', mock_request):
            result = await http_call_execute({
                "url": "https://api.example.com/data",
                "retry_config": {"max_retries": 3, "initial_delay_ms": 1}
            })

        assert result.ok is True
        assert result.result["retries"] == 1

    @pytest.mark.asyncio
    async def test_429_error_category_is_rate_limit(self):
        """429 error should have RATE_LIMIT category."""
        set_mock_response("https://api.example.com/limited", MockResponse(
            status_code=429,
            body={"error": "Rate limited"}
        ))

        result = await http_call_execute({
            "url": "https://api.example.com/limited",
            "retry_config": {"max_retries": 0}  # No retries
        })

        assert result.ok is False
        assert result.error["category"] == "RATE_LIMIT"


class TestTimeoutHandling:
    """Test timeout handling."""

    @pytest.mark.asyncio
    async def test_timeout_triggers_retry(self):
        """Timeout should trigger retry."""
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("Request timed out")
            return (200, {}, {"success": True}, 50)

        with patch('app.skills.http_call_v2._make_request', mock_request):
            result = await http_call_execute({
                "url": "https://api.example.com/data",
                "retry_config": {"max_retries": 3, "initial_delay_ms": 1}
            })

        assert result.ok is True
        assert result.result["retries"] == 1

    @pytest.mark.asyncio
    async def test_timeout_error_category(self):
        """Timeout should have TIMEOUT category."""
        async def always_timeout(*args, **kwargs):
            raise TimeoutError("Request timed out")

        with patch('app.skills.http_call_v2._make_request', always_timeout):
            result = await http_call_execute({
                "url": "https://api.example.com/data",
                "retry_config": {"max_retries": 0, "initial_delay_ms": 1}
            })

        assert result.ok is False
        assert result.error["code"] == "ERR_TIMEOUT"
        assert result.error["category"] == "TIMEOUT"


class TestConnectionErrors:
    """Test connection error handling."""

    @pytest.mark.asyncio
    async def test_connection_refused_triggers_retry(self):
        """Connection refused should trigger retry."""
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Connection refused")
            return (200, {}, {"success": True}, 50)

        with patch('app.skills.http_call_v2._make_request', mock_request):
            result = await http_call_execute({
                "url": "https://api.example.com/data",
                "retry_config": {"max_retries": 3, "initial_delay_ms": 1}
            })

        assert result.ok is True

    @pytest.mark.asyncio
    async def test_dns_failure_triggers_retry(self):
        """DNS failure should trigger retry."""
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("getaddrinfo failed")
            return (200, {}, {"success": True}, 50)

        with patch('app.skills.http_call_v2._make_request', mock_request):
            result = await http_call_execute({
                "url": "https://api.example.com/data",
                "retry_config": {"max_retries": 3, "initial_delay_ms": 1}
            })

        assert result.ok is True

    @pytest.mark.asyncio
    async def test_ssl_error_not_retryable(self):
        """SSL error should NOT be retryable."""
        async def ssl_error(*args, **kwargs):
            raise Exception("SSL certificate verify failed")

        with patch('app.skills.http_call_v2._make_request', ssl_error):
            result = await http_call_execute({
                "url": "https://api.example.com/data",
                "retry_config": {"max_retries": 3, "initial_delay_ms": 1}
            })

        assert result.ok is False
        assert result.error["code"] == "ERR_SSL_ERROR"
        # SSL errors should not retry (retries == 0 or very few)


class TestDeterministicRetryBackoff:
    """Test deterministic retry with seeded backoff."""

    def test_seeded_delays_are_deterministic(self):
        """Same seed produces same delay sequence."""
        config = RetryConfig(
            initial_delay_ms=100,
            max_delay_ms=5000,
            backoff_multiplier=2.0,
            retry_seed=12345
        )

        # Generate delays twice
        delays1 = [compute_retry_delay(i, config) for i in range(5)]
        delays2 = [compute_retry_delay(i, config) for i in range(5)]

        assert delays1 == delays2

    def test_different_seeds_different_delays(self):
        """Different seeds produce different delays."""
        config1 = RetryConfig(retry_seed=12345)
        config2 = RetryConfig(retry_seed=54321)

        delays1 = [compute_retry_delay(i, config1) for i in range(5)]
        delays2 = [compute_retry_delay(i, config2) for i in range(5)]

        assert delays1 != delays2

    def test_exponential_backoff_pattern(self):
        """Delays follow exponential backoff pattern."""
        config = RetryConfig(
            initial_delay_ms=100,
            backoff_multiplier=2.0,
            retry_seed=None  # No jitter
        )

        delay0 = compute_retry_delay(0, config)
        delay1 = compute_retry_delay(1, config)
        delay2 = compute_retry_delay(2, config)

        assert delay0 == 100
        assert delay1 == 200
        assert delay2 == 400

    def test_max_delay_cap(self):
        """Delays are capped at max_delay_ms."""
        config = RetryConfig(
            initial_delay_ms=1000,
            max_delay_ms=2000,
            backoff_multiplier=2.0,
            retry_seed=None
        )

        # After many retries, should still be capped
        delay = compute_retry_delay(10, config)
        assert delay <= 2000


class TestNonRetryableErrors:
    """Test that non-retryable errors don't trigger retry."""

    @pytest.fixture(autouse=True)
    def setup(self):
        clear_mock_responses()
        yield
        clear_mock_responses()

    @pytest.mark.asyncio
    async def test_400_not_retried(self):
        """400 Bad Request should NOT be retried."""
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return (400, {}, {"error": "Bad Request"}, 50)

        with patch('app.skills.http_call_v2._make_request', mock_request):
            result = await http_call_execute({
                "url": "https://api.example.com/data",
                "retry_config": {"max_retries": 3}
            })

        assert result.ok is False
        assert call_count == 1  # Only one call, no retries
        assert result.error["code"] == "ERR_HTTP_400_BAD_REQUEST"

    @pytest.mark.asyncio
    async def test_401_not_retried(self):
        """401 Unauthorized should NOT be retried."""
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return (401, {}, {"error": "Unauthorized"}, 50)

        with patch('app.skills.http_call_v2._make_request', mock_request):
            result = await http_call_execute({
                "url": "https://api.example.com/data",
                "retry_config": {"max_retries": 3}
            })

        assert result.ok is False
        assert call_count == 1
        assert result.error["category"] == "AUTH_FAIL"

    @pytest.mark.asyncio
    async def test_404_not_retried(self):
        """404 Not Found should NOT be retried."""
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return (404, {}, {"error": "Not Found"}, 50)

        with patch('app.skills.http_call_v2._make_request', mock_request):
            result = await http_call_execute({
                "url": "https://api.example.com/data",
                "retry_config": {"max_retries": 3}
            })

        assert result.ok is False
        assert call_count == 1


class TestErrorContractCompliance:
    """Verify error_contract.md compliance."""

    def test_all_retryable_status_codes_in_map(self):
        """All retryable status codes are in HTTP_ERROR_MAP."""
        retryable_codes = [408, 429, 500, 502, 503, 504]
        for code in retryable_codes:
            assert code in HTTP_ERROR_MAP
            assert HTTP_ERROR_MAP[code].retryable is True

    def test_all_non_retryable_status_codes_in_map(self):
        """All non-retryable status codes are in HTTP_ERROR_MAP."""
        non_retryable_codes = [400, 401, 403, 404, 409, 422]
        for code in non_retryable_codes:
            assert code in HTTP_ERROR_MAP
            assert HTTP_ERROR_MAP[code].retryable is False

    def test_network_error_categories(self):
        """Network errors have correct categories."""
        assert NETWORK_ERROR_MAP["timeout"].category == ErrorCategory.TIMEOUT
        assert NETWORK_ERROR_MAP["connection"].category == ErrorCategory.NETWORK
        assert NETWORK_ERROR_MAP["dns"].category == ErrorCategory.NETWORK
        assert NETWORK_ERROR_MAP["ssl"].category == ErrorCategory.NETWORK

    def test_ssl_not_retryable(self):
        """SSL errors are not retryable."""
        assert NETWORK_ERROR_MAP["ssl"].retryable is False


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
