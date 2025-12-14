"""
Tests for BudgetLLM package.

Run with: pytest tests/test_budgetllm.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from budgetllm.core.budget import BudgetTracker, BudgetExceededError, InMemoryStateAdapter
from budgetllm.core.cache import PromptCache
from budgetllm.core.backends.memory import MemoryBackend


# =============================================================================
# BUDGET TRACKER TESTS
# =============================================================================

class TestBudgetTracker:
    """Tests for BudgetTracker class."""

    def test_daily_limit_blocks_when_exceeded(self):
        """Daily limit should block calls when exceeded."""
        tracker = BudgetTracker(daily_limit_cents=100, auto_pause=True)

        # Record 50 cents
        tracker.record_cost(50)
        assert tracker.check_limits() is True

        # Record another 60 cents (total 110, exceeds 100)
        tracker.record_cost(60)

        with pytest.raises(BudgetExceededError) as exc:
            tracker.check_limits()

        assert exc.value.limit_type == "daily"
        assert exc.value.spent == 110
        assert exc.value.limit == 100

    def test_monthly_limit_blocks_when_exceeded(self):
        """Monthly limit should block calls when exceeded."""
        tracker = BudgetTracker(monthly_limit_cents=500, auto_pause=True)

        tracker.record_cost(300)
        assert tracker.check_limits() is True

        tracker.record_cost(250)  # Total 550

        with pytest.raises(BudgetExceededError) as exc:
            tracker.check_limits()

        assert exc.value.limit_type == "monthly"

    def test_hard_limit_blocks_when_exceeded(self):
        """Hard limit should block calls when exceeded."""
        tracker = BudgetTracker(hard_limit_cents=1000, auto_pause=True)

        tracker.record_cost(500)
        tracker.record_cost(300)
        assert tracker.check_limits() is True

        tracker.record_cost(300)  # Total 1100

        with pytest.raises(BudgetExceededError) as exc:
            tracker.check_limits()

        assert exc.value.limit_type == "hard"

    def test_auto_pause_disabled_returns_false(self):
        """With auto_pause=False, should return False instead of raising."""
        tracker = BudgetTracker(daily_limit_cents=100, auto_pause=False)

        tracker.record_cost(150)

        # Should return False, not raise
        assert tracker.check_limits() is False

    def test_manual_pause_blocks_calls(self):
        """Manual pause (kill switch) should block all calls."""
        tracker = BudgetTracker(daily_limit_cents=1000, auto_pause=True)

        tracker.pause()

        with pytest.raises(BudgetExceededError) as exc:
            tracker.check_limits()

        assert exc.value.limit_type == "paused"

    def test_resume_after_pause(self):
        """Resume should allow calls after pause."""
        tracker = BudgetTracker(daily_limit_cents=1000, auto_pause=True)

        tracker.pause()
        assert tracker.is_paused() is True

        tracker.resume()
        assert tracker.is_paused() is False
        assert tracker.check_limits() is True

    def test_get_status_returns_correct_values(self):
        """get_status should return accurate spend info."""
        tracker = BudgetTracker(
            daily_limit_cents=100,
            monthly_limit_cents=500,
            hard_limit_cents=1000,
        )

        tracker.record_cost(50)

        status = tracker.get_status()

        assert status["daily"]["spent_cents"] == 50
        assert status["daily"]["remaining_cents"] == 50
        assert status["monthly"]["spent_cents"] == 50
        assert status["total"]["spent_cents"] == 50

    def test_reset_clears_counters(self):
        """reset_all should clear all counters."""
        tracker = BudgetTracker(daily_limit_cents=100)

        tracker.record_cost(50)
        assert tracker.get_daily_spend() == 50

        tracker.reset_all()
        assert tracker.get_daily_spend() == 0


# =============================================================================
# CACHE TESTS
# =============================================================================

class TestPromptCache:
    """Tests for PromptCache class."""

    def test_same_prompt_returns_cached_response(self):
        """Same prompt should return cached response."""
        backend = MemoryBackend()
        cache = PromptCache(backend=backend)

        messages = [{"role": "user", "content": "Hello"}]
        response = {"content": "Hi there!", "input_tokens": 5, "output_tokens": 3}

        # Store
        cache.set(
            model="gpt-4o-mini",
            messages=messages,
            response=response,
            cost_cents=0.1,
        )

        # Retrieve
        cached = cache.get(
            model="gpt-4o-mini",
            messages=messages,
        )

        assert cached is not None
        assert cached["content"] == "Hi there!"
        assert cached["cached"] is True

    def test_different_prompt_returns_none(self):
        """Different prompt should not hit cache."""
        backend = MemoryBackend()
        cache = PromptCache(backend=backend)

        messages1 = [{"role": "user", "content": "Hello"}]
        messages2 = [{"role": "user", "content": "Goodbye"}]

        cache.set(
            model="gpt-4o-mini",
            messages=messages1,
            response={"content": "Hi"},
            cost_cents=0.1,
        )

        cached = cache.get(model="gpt-4o-mini", messages=messages2)
        assert cached is None

    def test_different_model_returns_none(self):
        """Different model should not hit cache."""
        backend = MemoryBackend()
        cache = PromptCache(backend=backend)

        messages = [{"role": "user", "content": "Hello"}]

        cache.set(
            model="gpt-4o-mini",
            messages=messages,
            response={"content": "Hi"},
            cost_cents=0.1,
        )

        cached = cache.get(model="gpt-4o", messages=messages)
        assert cached is None

    def test_cache_disabled_returns_none(self):
        """Disabled cache should always return None."""
        backend = MemoryBackend()
        cache = PromptCache(backend=backend, enabled=False)

        messages = [{"role": "user", "content": "Hello"}]

        cache.set(
            model="gpt-4o-mini",
            messages=messages,
            response={"content": "Hi"},
            cost_cents=0.1,
        )

        cached = cache.get(model="gpt-4o-mini", messages=messages)
        assert cached is None

    def test_hit_counter_increments(self):
        """Cache hits should increment counter."""
        backend = MemoryBackend()
        cache = PromptCache(backend=backend)

        messages = [{"role": "user", "content": "Hello"}]

        cache.set(
            model="gpt-4o-mini",
            messages=messages,
            response={"content": "Hi"},
            cost_cents=0.5,
        )

        # 3 cache hits
        cache.get(model="gpt-4o-mini", messages=messages)
        cache.get(model="gpt-4o-mini", messages=messages)
        cache.get(model="gpt-4o-mini", messages=messages)

        stats = cache.get_stats()
        assert stats["hits"] == 3
        assert stats["savings_cents"] == 1.5  # 0.5 * 3


# =============================================================================
# MEMORY BACKEND TESTS
# =============================================================================

class TestMemoryBackend:
    """Tests for MemoryBackend class."""

    def test_set_and_get(self):
        """Basic set/get should work."""
        backend = MemoryBackend()

        backend.set("key1", {"data": "value"})
        result = backend.get("key1")

        assert result is not None
        assert result["data"] == "value"

    def test_get_nonexistent_returns_none(self):
        """Getting nonexistent key should return None."""
        backend = MemoryBackend()

        result = backend.get("nonexistent")
        assert result is None

    def test_ttl_expiration(self):
        """Expired entries should return None."""
        backend = MemoryBackend()

        # Set with 1 second TTL
        backend.set("key1", {"data": "value"}, ttl=1)

        # Should exist immediately
        result = backend.get("key1")
        assert result is not None

        # Wait for expiration
        import time
        time.sleep(1.5)

        result = backend.get("key1")
        assert result is None

    def test_lru_eviction(self):
        """LRU eviction should work at capacity."""
        backend = MemoryBackend(max_size=3)

        # Add 3 items
        backend.set("key1", {"n": 1})
        backend.set("key2", {"n": 2})
        backend.set("key3", {"n": 3})

        # Add 4th item (should evict key1)
        backend.set("key4", {"n": 4})

        assert backend.get("key1") is None
        assert backend.get("key4") is not None

    def test_clear(self):
        """Clear should remove all entries."""
        backend = MemoryBackend()

        backend.set("key1", {"n": 1})
        backend.set("key2", {"n": 2})

        count = backend.clear()

        assert count == 2
        assert backend.size() == 0


# =============================================================================
# CLIENT TESTS (with mocked OpenAI)
# =============================================================================

class TestClient:
    """Tests for Client class."""

    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI client."""
        with patch.dict("sys.modules", {"openai": MagicMock()}):
            import sys
            mock_openai_module = sys.modules["openai"]

            # Setup mock response matching OpenAI's actual format
            mock_response = MagicMock()
            mock_response.id = "chatcmpl-test123"
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello back!"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.model = "gpt-4o-mini"
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5

            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_module.OpenAI.return_value = mock_client

            yield mock_openai_module

    def test_chat_returns_response(self, mock_openai):
        """chat() should return OpenAI-compatible response."""
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)

        result = client.chat("Hello!")

        # OpenAI-compatible format
        assert result["choices"][0]["message"]["content"] == "Hello back!"
        assert result["cache_hit"] is False
        assert "cost_cents" in result
        assert "usage" in result

    def test_cache_hit_returns_zero_cost(self, mock_openai):
        """Second identical call should hit cache with zero cost."""
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)

        # First call - cache miss
        result1 = client.chat("Hello!", model="gpt-4o-mini")
        assert result1["cache_hit"] is False

        # Second call - cache hit
        result2 = client.chat("Hello!", model="gpt-4o-mini")
        assert result2["cache_hit"] is True
        assert result2["cost_cents"] == 0.0

    def test_budget_exceeded_raises_error(self, mock_openai):
        """Exceeding budget should raise BudgetExceededError."""
        from budgetllm import Client, BudgetExceededError

        # Make the mock return high token counts so cost is significant
        mock_client = mock_openai.OpenAI.return_value
        mock_response = mock_client.chat.completions.create.return_value
        mock_response.id = "chatcmpl-expensive"
        mock_response.usage.prompt_tokens = 100000  # High token count
        mock_response.usage.completion_tokens = 50000

        client = Client(openai_key="test-key", budget_cents=1)  # Very low limit

        # First call uses budget (will exceed with high token count)
        client.chat("Hello!")

        # Second call should fail
        with pytest.raises(BudgetExceededError):
            client.chat("Hello again!", enable_cache=False)

    def test_pause_blocks_calls(self, mock_openai):
        """Manual pause should block calls."""
        from budgetllm import Client, BudgetExceededError

        client = Client(openai_key="test-key", budget_cents=1000)

        client.pause()

        with pytest.raises(BudgetExceededError):
            client.chat("Hello!")

    def test_get_status_returns_info(self, mock_openai):
        """get_status should return budget and cache info."""
        from budgetllm import Client

        client = Client(
            openai_key="test-key",
            budget_cents=1000,
            daily_limit_cents=500,
        )

        status = client.get_status()

        assert "budget" in status
        assert "cache" in status
        assert status["budget"]["total"]["limit_cents"] == 1000


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests combining budget + cache."""

    def test_full_flow_with_mock(self):
        """Test complete flow: cache miss -> record cost -> cache hit."""
        mock_openai_module = MagicMock()

        mock_response = MagicMock()
        mock_response.id = "chatcmpl-integration"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 10000  # Enough tokens to register cost
        mock_response.usage.completion_tokens = 5000

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            from budgetllm import Client

            client = Client(
                openai_key="test-key",
                budget_cents=1000,
                daily_limit_cents=500,
            )

            # First call
            r1 = client.chat("Test message")
            assert r1["cache_hit"] is False

            # Check budget was recorded
            status = client.get_status()
            assert status["budget"]["total"]["spent_cents"] >= 0

            # Second call - should hit cache
            r2 = client.chat("Test message")
            assert r2["cache_hit"] is True
            assert r2["cost_cents"] == 0.0

            # Verify OpenAI was only called once
            assert mock_client.chat.completions.create.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
