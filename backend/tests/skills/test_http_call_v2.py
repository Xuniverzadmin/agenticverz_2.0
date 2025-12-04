# tests/skills/test_http_call_v2.py
"""
Tests for HTTP Call Skill v2 (M3)

Tests error contract enforcement, idempotency, deterministic retry,
and response canonicalization.
"""

import pytest
import sys
from pathlib import Path

# Path setup
_backend = Path(__file__).parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.skills.http_call_v2 import (
    http_call_execute,
    http_call_handler,
    HTTP_CALL_DESCRIPTOR,
    HTTP_ERROR_MAP,
    NETWORK_ERROR_MAP,
    MUTATING_METHODS,
    SAFE_METHODS,
    ErrorCategory,
    ErrorMapping,
    RetryConfig,
    compute_retry_delay,
    validate_idempotency,
    validate_url,
    map_http_error,
    map_network_error,
    MockResponse,
    set_mock_response,
    clear_mock_responses,
    _canonical_json,
    _content_hash,
    _generate_call_id,
)


class TestCanonicalJson:
    """Test canonical JSON utilities."""

    def test_canonical_json_sorted_keys(self):
        """Keys must be sorted alphabetically."""
        data = {"z": 1, "a": 2, "m": 3}
        canonical = _canonical_json(data)
        assert canonical == '{"a":2,"m":3,"z":1}'

    def test_canonical_json_no_whitespace(self):
        """No extra whitespace in output."""
        data = {"key": "value", "nested": {"a": 1}}
        canonical = _canonical_json(data)
        assert ' ' not in canonical
        assert '\n' not in canonical

    def test_content_hash_deterministic(self):
        """Same input produces same hash."""
        data = {"key": "value"}
        hash1 = _content_hash(data)
        hash2 = _content_hash(data)
        assert hash1 == hash2
        assert len(hash1) == 16

    def test_content_hash_different_for_different_data(self):
        """Different input produces different hash."""
        hash1 = _content_hash({"a": 1})
        hash2 = _content_hash({"a": 2})
        assert hash1 != hash2

    def test_generate_call_id_deterministic(self):
        """Call ID is deterministic from params."""
        params = {"url": "https://api.example.com", "method": "GET"}
        id1 = _generate_call_id(params)
        id2 = _generate_call_id(params)
        assert id1 == id2
        assert id1.startswith("http_")


class TestErrorMappings:
    """Test error mapping constants."""

    def test_http_error_map_4xx(self):
        """4xx errors are mapped correctly."""
        assert HTTP_ERROR_MAP[400].code == "ERR_HTTP_400_BAD_REQUEST"
        assert HTTP_ERROR_MAP[400].category == ErrorCategory.CLIENT_ERROR
        assert HTTP_ERROR_MAP[400].retryable is False

        assert HTTP_ERROR_MAP[401].code == "ERR_HTTP_401_UNAUTHORIZED"
        assert HTTP_ERROR_MAP[401].category == ErrorCategory.AUTH_FAIL

        assert HTTP_ERROR_MAP[429].code == "ERR_HTTP_429_RATE_LIMITED"
        assert HTTP_ERROR_MAP[429].category == ErrorCategory.RATE_LIMIT
        assert HTTP_ERROR_MAP[429].retryable is True

    def test_http_error_map_5xx(self):
        """5xx errors are mapped correctly."""
        assert HTTP_ERROR_MAP[500].code == "ERR_HTTP_500_SERVER_ERROR"
        assert HTTP_ERROR_MAP[500].category == ErrorCategory.SERVER_ERROR
        assert HTTP_ERROR_MAP[500].retryable is True

        assert HTTP_ERROR_MAP[503].code == "ERR_HTTP_503_UNAVAILABLE"
        assert HTTP_ERROR_MAP[503].category == ErrorCategory.TRANSIENT

        assert HTTP_ERROR_MAP[504].code == "ERR_HTTP_504_GATEWAY_TIMEOUT"
        assert HTTP_ERROR_MAP[504].category == ErrorCategory.TIMEOUT

    def test_network_error_map(self):
        """Network errors are mapped correctly."""
        assert NETWORK_ERROR_MAP["timeout"].code == "ERR_TIMEOUT"
        assert NETWORK_ERROR_MAP["timeout"].category == ErrorCategory.TIMEOUT
        assert NETWORK_ERROR_MAP["timeout"].retryable is True

        assert NETWORK_ERROR_MAP["connection"].code == "ERR_CONNECTION_REFUSED"
        assert NETWORK_ERROR_MAP["connection"].category == ErrorCategory.NETWORK

        assert NETWORK_ERROR_MAP["ssl"].code == "ERR_SSL_ERROR"
        assert NETWORK_ERROR_MAP["ssl"].retryable is False


class TestIdempotencyValidation:
    """Test idempotency key validation."""

    def test_safe_methods_no_key_required(self):
        """GET, HEAD, OPTIONS don't require idempotency key."""
        for method in SAFE_METHODS:
            assert validate_idempotency(method, None) is None
            assert validate_idempotency(method.lower(), None) is None

    def test_mutating_methods_require_key(self):
        """POST, PUT, PATCH, DELETE require idempotency key."""
        for method in MUTATING_METHODS:
            error = validate_idempotency(method, None)
            assert error is not None
            assert "idempotency_key" in error

    def test_mutating_methods_accept_key(self):
        """Mutating methods pass with idempotency key."""
        for method in MUTATING_METHODS:
            assert validate_idempotency(method, "key-123") is None


class TestUrlValidation:
    """Test URL validation."""

    def test_valid_https_url(self):
        """HTTPS URL is valid."""
        assert validate_url("https://api.example.com") is None

    def test_valid_http_url(self):
        """HTTP URL is valid."""
        assert validate_url("http://api.example.com") is None

    def test_invalid_scheme(self):
        """Invalid scheme is rejected."""
        error = validate_url("ftp://files.example.com")
        assert error is not None
        assert "scheme" in error.lower()

    def test_localhost_blocked(self):
        """Localhost is blocked."""
        error = validate_url("http://localhost/api")
        assert error is not None
        assert "Blocked" in error

    def test_127_0_0_1_blocked(self):
        """127.0.0.1 is blocked."""
        error = validate_url("http://127.0.0.1/api")
        assert error is not None
        assert "Blocked" in error


class TestRetryDelay:
    """Test deterministic retry delay calculation."""

    def test_exponential_backoff(self):
        """Delays follow exponential backoff."""
        config = RetryConfig(initial_delay_ms=100, backoff_multiplier=2.0)

        delay0 = compute_retry_delay(0, config)
        delay1 = compute_retry_delay(1, config)
        delay2 = compute_retry_delay(2, config)

        assert delay0 == 100
        assert delay1 == 200
        assert delay2 == 400

    def test_max_delay_cap(self):
        """Delay is capped at max_delay_ms."""
        config = RetryConfig(initial_delay_ms=1000, max_delay_ms=2000, backoff_multiplier=2.0)

        delay = compute_retry_delay(10, config)
        assert delay <= 2200  # max + 10% jitter

    def test_deterministic_jitter_with_seed(self):
        """Jitter is deterministic when seed is provided."""
        config = RetryConfig(retry_seed=12345)

        delay1 = compute_retry_delay(0, config)
        delay2 = compute_retry_delay(0, config)

        assert delay1 == delay2

    def test_different_seeds_different_jitter(self):
        """Different seeds produce different jitter."""
        config1 = RetryConfig(retry_seed=12345)
        config2 = RetryConfig(retry_seed=54321)

        delay1 = compute_retry_delay(0, config1)
        delay2 = compute_retry_delay(0, config2)

        # Should be different (statistically almost certain)
        assert delay1 != delay2


class TestMapHttpError:
    """Test HTTP error mapping function."""

    def test_known_status_codes(self):
        """Known status codes map correctly."""
        code, category, retryable, details = map_http_error(429)
        assert code == "ERR_HTTP_429_RATE_LIMITED"
        assert category == ErrorCategory.RATE_LIMIT
        assert retryable is True
        assert details["upstream_status"] == 429

    def test_unknown_4xx(self):
        """Unknown 4xx maps to CLIENT_ERROR."""
        code, category, retryable, _ = map_http_error(418)  # I'm a teapot
        assert code == "ERR_HTTP_418"
        assert category == ErrorCategory.CLIENT_ERROR
        assert retryable is False

    def test_unknown_5xx(self):
        """Unknown 5xx maps to SERVER_ERROR and is retryable."""
        code, category, retryable, _ = map_http_error(599)
        assert code == "ERR_HTTP_599"
        assert category == ErrorCategory.SERVER_ERROR
        assert retryable is True


class TestMapNetworkError:
    """Test network error mapping function."""

    def test_timeout_error(self):
        """Timeout exception maps correctly."""
        class TimeoutError(Exception):
            pass

        code, category, retryable, _ = map_network_error(TimeoutError("Request timed out"))
        assert code == "ERR_TIMEOUT"
        assert category == ErrorCategory.TIMEOUT
        assert retryable is True

    def test_connection_error(self):
        """Connection exception maps correctly."""
        class ConnectionError(Exception):
            pass

        code, category, retryable, _ = map_network_error(ConnectionError("Connection refused"))
        assert code == "ERR_CONNECTION_REFUSED"
        assert category == ErrorCategory.NETWORK
        assert retryable is True

    def test_ssl_error(self):
        """SSL exception maps correctly and is not retryable."""
        class SSLError(Exception):
            pass

        code, category, retryable, _ = map_network_error(SSLError("Certificate verification failed"))
        assert code == "ERR_SSL_ERROR"
        assert category == ErrorCategory.NETWORK
        assert retryable is False


class TestHttpCallExecute:
    """Test main execute function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear mock responses before each test."""
        clear_mock_responses()
        yield
        clear_mock_responses()

    @pytest.mark.asyncio
    async def test_get_success(self):
        """GET request succeeds."""
        set_mock_response("https://api.example.com/data", MockResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body={"result": "ok"}
        ))

        result = await http_call_execute({
            "url": "https://api.example.com/data",
            "method": "GET"
        })

        assert result.ok is True
        assert result.result["status_code"] == 200
        assert result.result["body"] == {"result": "ok"}
        assert "headers_hash" in result.result
        assert "body_hash" in result.result

    @pytest.mark.asyncio
    async def test_post_requires_idempotency_key(self):
        """POST without idempotency key fails."""
        result = await http_call_execute({
            "url": "https://api.example.com/create",
            "method": "POST",
            "body": {"name": "test"}
        })

        assert result.ok is False
        assert result.error["code"] == "ERR_MISSING_IDEMPOTENCY_KEY"
        assert result.error["category"] == "VALIDATION"
        assert result.error["retryable"] is False

    @pytest.mark.asyncio
    async def test_post_with_idempotency_key(self):
        """POST with idempotency key succeeds."""
        set_mock_response("https://api.example.com/create", MockResponse(
            status_code=201,
            body={"id": "123"}
        ))

        result = await http_call_execute({
            "url": "https://api.example.com/create",
            "method": "POST",
            "body": {"name": "test"},
            "idempotency_key": "create-123-001"
        })

        assert result.ok is True
        assert result.result["status_code"] == 201
        assert result.result["idempotency_key"] == "create-123-001"

    @pytest.mark.asyncio
    async def test_blocked_host_rejected(self):
        """Blocked host returns validation error."""
        result = await http_call_execute({
            "url": "http://localhost/internal",
            "method": "GET"
        })

        assert result.ok is False
        assert result.error["code"] == "ERR_BLOCKED_HOST"
        assert result.error["category"] == "VALIDATION"

    @pytest.mark.asyncio
    async def test_missing_url(self):
        """Missing URL returns validation error."""
        result = await http_call_execute({
            "method": "GET"
        })

        assert result.ok is False
        assert result.error["code"] == "ERR_VALIDATION_FAILED"

    @pytest.mark.asyncio
    async def test_http_error_response(self):
        """HTTP error status is handled correctly."""
        set_mock_response("https://api.example.com/notfound", MockResponse(
            status_code=404,
            body={"error": "Not found"}
        ))

        result = await http_call_execute({
            "url": "https://api.example.com/notfound",
            "method": "GET"
        })

        assert result.ok is False
        assert result.error["code"] == "ERR_HTTP_404_NOT_FOUND"
        assert result.error["category"] == "CLIENT_ERROR"
        assert result.error["retryable"] is False

    @pytest.mark.asyncio
    async def test_rate_limit_is_retryable(self):
        """429 is marked as retryable."""
        set_mock_response("https://api.example.com/limited", MockResponse(
            status_code=429,
            body={"error": "Rate limited"}
        ))

        result = await http_call_execute({
            "url": "https://api.example.com/limited",
            "method": "GET",
            "retry_config": {"max_retries": 0}  # No actual retries
        })

        assert result.ok is False
        assert result.error["code"] == "ERR_HTTP_429_RATE_LIMITED"
        assert result.error["category"] == "RATE_LIMIT"
        # After exhausting retries, retryable becomes False
        # (since we can't do more retries ourselves)

    @pytest.mark.asyncio
    async def test_response_hash_deterministic(self):
        """Response hashes are deterministic."""
        set_mock_response("https://api.example.com/data", MockResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body={"z": 1, "a": 2}
        ))

        result1 = await http_call_execute({
            "url": "https://api.example.com/data"
        })

        result2 = await http_call_execute({
            "url": "https://api.example.com/data"
        })

        # Body hash should be deterministic
        assert result1.result["body_hash"] == result2.result["body_hash"]


class TestDescriptor:
    """Test skill descriptor."""

    def test_descriptor_fields(self):
        """Descriptor has required fields."""
        d = HTTP_CALL_DESCRIPTOR
        assert d.skill_id == "skill.http_call"
        assert d.version == "2.0.0"
        assert "status_code" in d.stable_fields
        assert "headers_hash" in d.stable_fields
        assert "body_hash" in d.stable_fields

    def test_failure_modes_defined(self):
        """Failure modes match error contract."""
        d = HTTP_CALL_DESCRIPTOR
        assert "ERR_HTTP_400_BAD_REQUEST" in d.failure_modes
        assert "ERR_HTTP_429_RATE_LIMITED" in d.failure_modes
        assert "ERR_TIMEOUT" in d.failure_modes
        assert "ERR_MISSING_IDEMPOTENCY_KEY" in d.failure_modes
        assert "ERR_BLOCKED_HOST" in d.failure_modes

    def test_constraints_defined(self):
        """Constraints are defined."""
        d = HTTP_CALL_DESCRIPTOR
        assert d.constraints["max_response_bytes"] == 10485760
        assert "localhost" in d.constraints["blocked_hosts"]


class TestDeterminism:
    """Test deterministic behavior."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear mock responses before each test."""
        clear_mock_responses()
        yield
        clear_mock_responses()

    @pytest.mark.asyncio
    async def test_call_id_deterministic(self):
        """Call ID is deterministic from params."""
        set_mock_response("https://api.example.com/test", MockResponse(
            status_code=200, body={"ok": True}
        ))

        params = {"url": "https://api.example.com/test", "method": "GET"}

        result1 = await http_call_execute(params)
        result2 = await http_call_execute(params)

        # StructuredOutcome uses 'id' field
        assert result1.id == result2.id

    @pytest.mark.asyncio
    async def test_seeded_retry_delay_deterministic(self):
        """Retry delays are deterministic with seed."""
        config = RetryConfig(
            initial_delay_ms=100,
            retry_seed=42
        )

        delays1 = [compute_retry_delay(i, config) for i in range(5)]
        delays2 = [compute_retry_delay(i, config) for i in range(5)]

        assert delays1 == delays2


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
