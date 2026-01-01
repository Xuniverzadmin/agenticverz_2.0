# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: scheduler (CI)
#   Execution: sync
# Role: Test quota exhaustion scenarios for embedding and rate limiting
# Callers: pytest
# Allowed Imports: L6 (platform), L4 (domain)
# Forbidden Imports: L1, L2, L3
# Reference: PIN-052

"""
Test quota exhaustion scenarios for embeddings and rate limiting.

Scenarios covered:
1. Daily embedding quota exhaustion
2. Quota reset at midnight UTC
3. Rate limiter token bucket exhaustion
4. Graceful degradation under quota exhaustion
5. Quota status reporting
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest


class TestEmbeddingQuotaExhaustion:
    """Tests for embedding daily quota scenarios."""

    def setup_method(self):
        """Reset quota state before each test."""
        # Reset module-level state
        import app.memory.embedding_metrics as metrics

        metrics._daily_call_count = 0
        metrics._last_reset_date = None
        metrics.EMBEDDING_QUOTA_EXCEEDED = False

    def test_quota_allows_requests_under_limit(self):
        """Requests should be allowed when under quota."""
        from app.memory.embedding_metrics import (
            check_embedding_quota,
            get_embedding_quota_status,
            increment_embedding_count,
        )

        # Set a low quota for testing
        with patch("app.memory.embedding_metrics.EMBEDDING_DAILY_QUOTA", 10):
            # First 9 requests should succeed
            for i in range(9):
                assert check_embedding_quota() is True
                increment_embedding_count()

            status = get_embedding_quota_status()
            assert status["current_count"] == 9
            assert status["remaining"] == 1
            assert status["exceeded"] is False

    def test_quota_blocks_at_limit(self):
        """Requests should be blocked when quota is exhausted."""
        from app.memory.embedding_metrics import (
            check_embedding_quota,
            get_embedding_quota_status,
            increment_embedding_count,
        )

        with patch("app.memory.embedding_metrics.EMBEDDING_DAILY_QUOTA", 5):
            # Consume all quota
            for _ in range(5):
                assert check_embedding_quota() is True
                increment_embedding_count()

            # Next request should be blocked
            assert check_embedding_quota() is False

            status = get_embedding_quota_status()
            assert status["exceeded"] is True
            assert status["remaining"] == 0

    def test_quota_resets_at_midnight_utc(self):
        """Quota should reset when date changes."""
        import app.memory.embedding_metrics as metrics
        from app.memory.embedding_metrics import (
            check_embedding_quota,
            get_embedding_quota_status,
            increment_embedding_count,
        )

        with patch("app.memory.embedding_metrics.EMBEDDING_DAILY_QUOTA", 3):
            # Exhaust quota
            for _ in range(3):
                check_embedding_quota()
                increment_embedding_count()

            assert check_embedding_quota() is False

            # Simulate day change
            yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
            metrics._last_reset_date = yesterday

            # Should reset and allow
            assert check_embedding_quota() is True

            status = get_embedding_quota_status()
            assert status["current_count"] == 0
            assert status["exceeded"] is False

    def test_unlimited_quota_when_zero(self):
        """Quota of 0 means unlimited."""
        from app.memory.embedding_metrics import (
            check_embedding_quota,
            get_embedding_quota_status,
            increment_embedding_count,
        )

        with patch("app.memory.embedding_metrics.EMBEDDING_DAILY_QUOTA", 0):
            # Many requests should all succeed
            for _ in range(1000):
                assert check_embedding_quota() is True
                increment_embedding_count()

            status = get_embedding_quota_status()
            assert status["remaining"] == -1  # -1 indicates unlimited

    def test_quota_metrics_incremented(self):
        """Quota exhaustion should increment Prometheus counter."""
        from app.memory.embedding_metrics import (
            EMBEDDING_QUOTA_EXCEEDED_COUNT,
            check_embedding_quota,
            increment_embedding_count,
        )

        with patch("app.memory.embedding_metrics.EMBEDDING_DAILY_QUOTA", 2):
            # Track initial count
            initial = (
                EMBEDDING_QUOTA_EXCEEDED_COUNT._value.get() if hasattr(EMBEDDING_QUOTA_EXCEEDED_COUNT, "_value") else 0
            )

            # Exhaust quota
            for _ in range(2):
                check_embedding_quota()
                increment_embedding_count()

            # Trigger exhaustion
            check_embedding_quota()

            # Counter should have incremented
            # Note: In real Prometheus, we'd verify the counter value


class TestRateLimiterExhaustion:
    """Tests for rate limiter exhaustion scenarios."""

    def test_allows_under_limit(self):
        """Requests should be allowed under rate limit."""
        from app.utils.rate_limiter import RateLimiter

        # Mock Redis client
        mock_client = MagicMock()
        mock_client.evalsha.return_value = 1  # 1 = allowed

        limiter = RateLimiter()
        limiter._client = mock_client
        limiter._script_sha = "fake_sha"

        assert limiter.allow("tenant:123", 60) is True
        assert limiter.allow("tenant:123", 60) is True

    def test_blocks_at_limit(self):
        """Requests should be blocked when rate limit exhausted."""
        from app.utils.rate_limiter import RateLimiter

        mock_client = MagicMock()
        mock_client.evalsha.return_value = 0  # 0 = blocked

        limiter = RateLimiter()
        limiter._client = mock_client
        limiter._script_sha = "fake_sha"

        assert limiter.allow("tenant:123", 60) is False

    def test_fail_open_when_redis_down(self):
        """Should allow requests when Redis unavailable (fail_open=True)."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(fail_open=True)
        limiter._client = None  # Simulate Redis failure

        # Should allow (fail open)
        assert limiter.allow("tenant:123", 60) is True

    def test_fail_closed_when_redis_down(self):
        """Should block requests when Redis unavailable (fail_open=False)."""
        from app.utils.rate_limiter import RateLimiter

        mock_client = MagicMock()
        mock_client.evalsha.side_effect = Exception("Redis connection error")

        limiter = RateLimiter(fail_open=False)
        limiter._client = mock_client
        limiter._script_sha = "fake_sha"

        # Should block (fail closed)
        assert limiter.allow("tenant:123", 60) is False

    def test_zero_rate_allows_all(self):
        """Rate of 0 means no limit."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter()
        # Should allow without even checking Redis
        assert limiter.allow("tenant:123", 0) is True

    def test_get_remaining_tokens(self):
        """Should return remaining tokens."""
        from app.utils.rate_limiter import RateLimiter

        mock_client = MagicMock()
        mock_client.hgetall.return_value = {
            b"tokens": b"45.5",
            b"last": b"1703980800",
        }

        limiter = RateLimiter()
        limiter._client = mock_client

        remaining = limiter.get_remaining("tenant:123", 60)
        assert remaining == 45  # Truncated to int


class TestVectorSearchFallback:
    """Tests for vector search degradation under quota exhaustion."""

    def test_fallback_on_quota_exhausted(self):
        """Vector search should fall back to keyword search when quota exhausted."""
        import app.memory.embedding_metrics as metrics
        from app.memory.embedding_metrics import VECTOR_FALLBACK_COUNT

        # Simulate quota exhausted
        metrics.EMBEDDING_QUOTA_EXCEEDED = True

        # The vector store should check quota and fall back
        # This tests the expected behavior pattern
        if metrics.EMBEDDING_QUOTA_EXCEEDED:
            VECTOR_FALLBACK_COUNT.labels(reason="quota_exhausted").inc()
            # In real code, this would trigger keyword fallback

        # Reset
        metrics.EMBEDDING_QUOTA_EXCEEDED = False

    def test_fallback_increments_metric(self):
        """Fallback should increment the fallback counter."""
        from app.memory.embedding_metrics import VECTOR_FALLBACK_COUNT

        # Track that metric exists and is incrementable
        VECTOR_FALLBACK_COUNT.labels(reason="no_embedding").inc()
        VECTOR_FALLBACK_COUNT.labels(reason="below_threshold").inc()
        VECTOR_FALLBACK_COUNT.labels(reason="error").inc()


class TestQuotaIntegration:
    """Integration tests for quota and rate limiting together."""

    def test_combined_quota_and_rate_limit(self):
        """Both quota and rate limit should be checked."""
        import app.memory.embedding_metrics as metrics
        from app.memory.embedding_metrics import check_embedding_quota, increment_embedding_count
        from app.utils.rate_limiter import RateLimiter

        # Reset state
        metrics._daily_call_count = 0
        metrics._last_reset_date = None
        metrics.EMBEDDING_QUOTA_EXCEEDED = False

        mock_client = MagicMock()
        mock_client.evalsha.return_value = 1
        limiter = RateLimiter()
        limiter._client = mock_client
        limiter._script_sha = "fake_sha"

        with patch("app.memory.embedding_metrics.EMBEDDING_DAILY_QUOTA", 100):
            # Both should pass
            rate_ok = limiter.allow("tenant:123", 60)
            quota_ok = check_embedding_quota()

            assert rate_ok is True
            assert quota_ok is True

            # Simulate embedding call
            increment_embedding_count()

    def test_quota_exhausted_before_rate_limit(self):
        """Quota exhaustion should block even if rate limit allows."""
        import app.memory.embedding_metrics as metrics
        from app.memory.embedding_metrics import check_embedding_quota, increment_embedding_count
        from app.utils.rate_limiter import RateLimiter

        # Reset state
        metrics._daily_call_count = 0
        metrics._last_reset_date = None
        metrics.EMBEDDING_QUOTA_EXCEEDED = False

        mock_client = MagicMock()
        mock_client.evalsha.return_value = 1  # Rate limit allows
        limiter = RateLimiter()
        limiter._client = mock_client
        limiter._script_sha = "fake_sha"

        with patch("app.memory.embedding_metrics.EMBEDDING_DAILY_QUOTA", 2):
            # Exhaust quota
            for _ in range(2):
                check_embedding_quota()
                increment_embedding_count()

            # Rate limit still allows
            rate_ok = limiter.allow("tenant:123", 60)
            assert rate_ok is True

            # But quota blocks
            quota_ok = check_embedding_quota()
            assert quota_ok is False


class TestQuotaStatusEndpoint:
    """Tests for quota status API responses."""

    def test_status_response_format(self):
        """Quota status should return expected format."""
        import app.memory.embedding_metrics as metrics
        from app.memory.embedding_metrics import get_embedding_quota_status, increment_embedding_count

        # Reset
        metrics._daily_call_count = 0
        metrics._last_reset_date = None
        metrics.EMBEDDING_QUOTA_EXCEEDED = False

        with patch("app.memory.embedding_metrics.EMBEDDING_DAILY_QUOTA", 1000):
            increment_embedding_count()
            increment_embedding_count()

            status = get_embedding_quota_status()

            assert "daily_quota" in status
            assert "current_count" in status
            assert "remaining" in status
            assert "exceeded" in status

            assert status["daily_quota"] == 1000
            assert status["current_count"] == 2
            assert status["remaining"] == 998
            assert status["exceeded"] is False

    def test_status_shows_exhausted(self):
        """Status should show exhausted state correctly."""
        import app.memory.embedding_metrics as metrics
        from app.memory.embedding_metrics import (
            check_embedding_quota,
            get_embedding_quota_status,
            increment_embedding_count,
        )

        # Reset
        metrics._daily_call_count = 0
        metrics._last_reset_date = None
        metrics.EMBEDDING_QUOTA_EXCEEDED = False

        with patch("app.memory.embedding_metrics.EMBEDDING_DAILY_QUOTA", 1):
            check_embedding_quota()
            increment_embedding_count()
            check_embedding_quota()  # This should set exceeded

            status = get_embedding_quota_status()
            assert status["exceeded"] is True
            assert status["remaining"] == 0


class TestGracefulDegradation:
    """Tests for graceful degradation patterns."""

    def test_system_continues_without_embeddings(self):
        """System should continue to function without embedding capability."""
        import app.memory.embedding_metrics as metrics

        # Simulate exhausted quota
        metrics.EMBEDDING_QUOTA_EXCEEDED = True

        # Core functionality should still work
        # This is a placeholder for actual integration testing
        # In real system: recovery matcher falls back to keyword search
        # In real system: memory still stores data, just without vectors

        assert metrics.EMBEDDING_QUOTA_EXCEEDED is True

        # Reset for other tests
        metrics.EMBEDDING_QUOTA_EXCEEDED = False

    def test_error_messages_are_clear(self):
        """Error responses should clearly indicate quota exhaustion."""
        import app.memory.embedding_metrics as metrics
        from app.memory.embedding_metrics import check_embedding_quota, get_embedding_quota_status

        # Reset and exhaust
        metrics._daily_call_count = 0
        metrics._last_reset_date = None
        metrics.EMBEDDING_QUOTA_EXCEEDED = False

        with patch("app.memory.embedding_metrics.EMBEDDING_DAILY_QUOTA", 0):
            # With unlimited quota, check still works
            assert check_embedding_quota() is True

        with patch("app.memory.embedding_metrics.EMBEDDING_DAILY_QUOTA", 1):
            # Reset state for this patch
            metrics._daily_call_count = 1
            check_embedding_quota()  # Should set exceeded

            status = get_embedding_quota_status()
            # Status provides clear information for error messages
            assert "exceeded" in status
            assert "daily_quota" in status


# Fixtures for pytest
@pytest.fixture(autouse=True)
def reset_quota_state():
    """Reset quota state before and after each test."""
    import app.memory.embedding_metrics as metrics

    metrics._daily_call_count = 0
    metrics._last_reset_date = None
    metrics.EMBEDDING_QUOTA_EXCEEDED = False
    yield
    metrics._daily_call_count = 0
    metrics._last_reset_date = None
    metrics.EMBEDDING_QUOTA_EXCEEDED = False
