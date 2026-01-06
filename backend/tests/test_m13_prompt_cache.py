"""
Tests for M13 Prompt Caching Implementation

Tests the prompt cache in llm_invoke.py to ensure:
1. Cache hits return cached responses
2. Cache misses call the LLM
3. TTL expiration works correctly
4. LRU eviction works when at capacity
5. Cache can be disabled per-request
6. Metrics are recorded correctly
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.skills.llm_invoke import (
    LLMInvokeSkill,
    PromptCache,
    configure_prompt_cache,
    get_prompt_cache,
)

# =============================================================================
# CACHE KEY GENERATION TESTS
# =============================================================================


class TestCacheKeyGeneration:
    """Test cache key generation logic."""

    def test_same_params_produce_same_key(self):
        """Same parameters should produce identical cache keys."""
        cache = PromptCache()

        messages = [{"role": "user", "content": "Hello"}]

        key1 = cache._generate_cache_key(
            provider="anthropic",
            model="claude-3-5-sonnet",
            messages=messages,
            system_prompt="Be helpful",
            temperature=0.7,
        )

        key2 = cache._generate_cache_key(
            provider="anthropic",
            model="claude-3-5-sonnet",
            messages=messages,
            system_prompt="Be helpful",
            temperature=0.7,
        )

        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex digest

    def test_different_messages_produce_different_keys(self):
        """Different messages should produce different cache keys."""
        cache = PromptCache()

        key1 = cache._generate_cache_key(
            provider="anthropic",
            model="claude-3-5-sonnet",
            messages=[{"role": "user", "content": "Hello"}],
            system_prompt=None,
            temperature=0.7,
        )

        key2 = cache._generate_cache_key(
            provider="anthropic",
            model="claude-3-5-sonnet",
            messages=[{"role": "user", "content": "Goodbye"}],
            system_prompt=None,
            temperature=0.7,
        )

        assert key1 != key2

    def test_different_temperature_produces_different_key(self):
        """Different temperature should produce different cache keys."""
        cache = PromptCache()
        messages = [{"role": "user", "content": "Hello"}]

        key1 = cache._generate_cache_key(
            provider="anthropic",
            model="claude-3-5-sonnet",
            messages=messages,
            system_prompt=None,
            temperature=0.5,
        )

        key2 = cache._generate_cache_key(
            provider="anthropic",
            model="claude-3-5-sonnet",
            messages=messages,
            system_prompt=None,
            temperature=0.9,
        )

        assert key1 != key2

    def test_different_provider_produces_different_key(self):
        """Different provider should produce different cache keys."""
        cache = PromptCache()
        messages = [{"role": "user", "content": "Hello"}]

        key1 = cache._generate_cache_key(
            provider="anthropic",
            model="claude-3-5-sonnet",
            messages=messages,
            system_prompt=None,
            temperature=0.7,
        )

        key2 = cache._generate_cache_key(
            provider="openai",
            model="claude-3-5-sonnet",
            messages=messages,
            system_prompt=None,
            temperature=0.7,
        )

        assert key1 != key2


# =============================================================================
# CACHE GET/SET TESTS
# =============================================================================


class TestCacheGetSet:
    """Test cache get and set operations."""

    def test_set_and_get_returns_cached_response(self):
        """Setting a value should allow getting it back."""
        cache = PromptCache(ttl_seconds=3600, max_size=100)

        messages = [{"role": "user", "content": "What is 2+2?"}]
        response = {
            "response_text": "4",
            "model_used": "claude-3-5-sonnet",
            "input_tokens": 10,
            "output_tokens": 5,
            "finish_reason": "end_turn",
        }

        # Set
        cache.set(
            provider="anthropic",
            model="claude-3-5-sonnet",
            messages=messages,
            system_prompt=None,
            temperature=0.7,
            response=response,
            estimated_cost_cents=0.5,
        )

        # Get
        cached = cache.get(
            provider="anthropic",
            model="claude-3-5-sonnet",
            messages=messages,
            system_prompt=None,
            temperature=0.7,
        )

        assert cached is not None
        assert cached["response_text"] == "4"
        assert cached["input_tokens"] == 10

    def test_get_returns_none_for_uncached(self):
        """Getting uncached value should return None."""
        cache = PromptCache()

        result = cache.get(
            provider="anthropic",
            model="claude-3-5-sonnet",
            messages=[{"role": "user", "content": "Never asked before"}],
            system_prompt=None,
            temperature=0.7,
        )

        assert result is None

    def test_cache_disabled_returns_none(self):
        """Disabled cache should always return None."""
        cache = PromptCache(enabled=False)

        messages = [{"role": "user", "content": "Hello"}]
        response = {
            "response_text": "Hi",
            "model_used": "test",
            "input_tokens": 1,
            "output_tokens": 1,
            "finish_reason": "stop",
        }

        # Set (should be no-op)
        cache.set(
            provider="anthropic",
            model="test",
            messages=messages,
            system_prompt=None,
            temperature=0.7,
            response=response,
        )

        # Get (should return None even if set was attempted)
        result = cache.get(
            provider="anthropic",
            model="test",
            messages=messages,
            system_prompt=None,
            temperature=0.7,
        )

        assert result is None


# =============================================================================
# TTL EXPIRATION TESTS
# =============================================================================


class TestCacheTTL:
    """Test cache TTL expiration."""

    def test_expired_entry_returns_none(self):
        """Expired entry should return None and be evicted."""
        cache = PromptCache(ttl_seconds=1, max_size=100)  # 1 second TTL

        messages = [{"role": "user", "content": "Short lived"}]
        response = {
            "response_text": "Hi",
            "model_used": "test",
            "input_tokens": 1,
            "output_tokens": 1,
            "finish_reason": "stop",
        }

        cache.set(
            provider="anthropic",
            model="test",
            messages=messages,
            system_prompt=None,
            temperature=0.7,
            response=response,
        )

        # Immediately should work
        assert (
            cache.get(
                provider="anthropic",
                model="test",
                messages=messages,
                system_prompt=None,
                temperature=0.7,
            )
            is not None
        )

        # Wait for expiration
        import time

        time.sleep(1.5)

        # Should be expired
        result = cache.get(
            provider="anthropic",
            model="test",
            messages=messages,
            system_prompt=None,
            temperature=0.7,
        )
        assert result is None


# =============================================================================
# LRU EVICTION TESTS
# =============================================================================


class TestCacheLRUEviction:
    """Test LRU eviction when cache is at capacity."""

    def test_evicts_oldest_when_at_capacity(self):
        """Should evict oldest entry when at capacity."""
        cache = PromptCache(ttl_seconds=3600, max_size=3)

        response = {
            "response_text": "Hi",
            "model_used": "test",
            "input_tokens": 1,
            "output_tokens": 1,
            "finish_reason": "stop",
        }

        # Fill cache
        for i in range(3):
            cache.set(
                provider="anthropic",
                model="test",
                messages=[{"role": "user", "content": f"Message {i}"}],
                system_prompt=None,
                temperature=0.7,
                response=response,
            )

        assert len(cache._cache) == 3

        # Add one more (should evict oldest)
        cache.set(
            provider="anthropic",
            model="test",
            messages=[{"role": "user", "content": "Message 3"}],
            system_prompt=None,
            temperature=0.7,
            response=response,
        )

        # Should still be at capacity
        assert len(cache._cache) == 3

        # First message should be evicted
        result = cache.get(
            provider="anthropic",
            model="test",
            messages=[{"role": "user", "content": "Message 0"}],
            system_prompt=None,
            temperature=0.7,
        )
        assert result is None

        # Latest message should still be there
        result = cache.get(
            provider="anthropic",
            model="test",
            messages=[{"role": "user", "content": "Message 3"}],
            system_prompt=None,
            temperature=0.7,
        )
        assert result is not None


# =============================================================================
# CACHE STATS TESTS
# =============================================================================


class TestCacheStats:
    """Test cache statistics."""

    def test_stats_returns_correct_values(self):
        """Stats should return accurate cache information."""
        cache = PromptCache(ttl_seconds=3600, max_size=100)

        response = {
            "response_text": "Hi",
            "model_used": "test",
            "input_tokens": 10,
            "output_tokens": 5,
            "finish_reason": "stop",
        }

        # Add some entries
        for i in range(5):
            cache.set(
                provider="anthropic",
                model="test",
                messages=[{"role": "user", "content": f"Message {i}"}],
                system_prompt=None,
                temperature=0.7,
                response=response,
                estimated_cost_cents=0.5,
            )

        # Hit some entries multiple times
        for _ in range(3):
            cache.get(
                provider="anthropic",
                model="test",
                messages=[{"role": "user", "content": "Message 0"}],
                system_prompt=None,
                temperature=0.7,
            )

        stats = cache.stats()

        assert stats["size"] == 5
        assert stats["max_size"] == 100
        assert stats["ttl_seconds"] == 3600
        assert stats["enabled"] is True
        assert stats["total_hits"] == 3

    def test_clear_removes_all_entries(self):
        """Clear should remove all cache entries."""
        cache = PromptCache(ttl_seconds=3600, max_size=100)

        response = {
            "response_text": "Hi",
            "model_used": "test",
            "input_tokens": 1,
            "output_tokens": 1,
            "finish_reason": "stop",
        }

        # Add entries
        for i in range(10):
            cache.set(
                provider="anthropic",
                model="test",
                messages=[{"role": "user", "content": f"Message {i}"}],
                system_prompt=None,
                temperature=0.7,
                response=response,
            )

        assert len(cache._cache) == 10

        count = cache.clear()

        assert count == 10
        assert len(cache._cache) == 0


# =============================================================================
# INTEGRATION TESTS (with mocked LLM)
# =============================================================================


class TestLLMInvokeCacheIntegration:
    """Integration tests for cache in LLMInvokeSkill."""

    @pytest.fixture
    def mock_metrics(self):
        """Mock Prometheus metrics to avoid label errors in tests."""
        with (
            patch("app.skills.llm_invoke.nova_llm_invocations_total") as m1,
            patch("app.skills.llm_invoke.nova_llm_duration_seconds") as m2,
            patch("app.skills.llm_invoke.nova_llm_tokens_total") as m3,
            patch("app.skills.llm_invoke.nova_llm_cost_cents_total") as m4,
            patch("app.skills.llm_invoke.llm_cache_hits_total") as m5,
            patch("app.skills.llm_invoke.llm_cache_misses_total") as m6,
            patch("app.skills.llm_invoke.llm_cache_savings_cents") as m7,
        ):
            # Setup mock labels
            for m in [m1, m2, m3, m4, m5, m6, m7]:
                m.labels.return_value.inc = MagicMock()
                m.labels.return_value.observe = MagicMock()
            yield

    @pytest.fixture
    def skill(self, mock_metrics):
        """Create LLMInvokeSkill with mocked clients."""
        skill = LLMInvokeSkill(
            {
                "anthropic_api_key": "test-key",
                "track_costs": True,
            }
        )
        return skill

    @pytest.mark.asyncio
    async def test_first_call_misses_cache(self, skill):
        """First call should be a cache miss."""
        # Configure fresh cache
        configure_prompt_cache(ttl_seconds=3600, max_size=100, enabled=True)

        with patch.object(skill, "_invoke_anthropic", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "response_text": "Hello!",
                "model_used": "claude-sonnet-4-20250514",
                "input_tokens": 10,
                "output_tokens": 5,
                "finish_reason": "end_turn",
            }

            result = await skill.execute(
                {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-20250514",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "enable_cache": True,
                }
            )

            # Should have called the LLM
            mock_invoke.assert_called_once()

            # Should not be a cache hit
            assert result["result"]["cache_hit"] is False

    @pytest.mark.asyncio
    async def test_second_call_hits_cache(self, skill):
        """Second identical call should hit cache."""
        # Configure fresh cache
        configure_prompt_cache(ttl_seconds=3600, max_size=100, enabled=True)

        with patch.object(skill, "_invoke_anthropic", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "response_text": "Hello!",
                "model_used": "claude-sonnet-4-20250514",
                "input_tokens": 10,
                "output_tokens": 5,
                "finish_reason": "end_turn",
            }

            params = {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "messages": [{"role": "user", "content": "Hello world"}],
                "temperature": 0.7,
                "enable_cache": True,
            }

            # First call - cache miss
            result1 = await skill.execute(params)
            assert result1["result"]["cache_hit"] is False
            assert mock_invoke.call_count == 1

            # Second call - cache hit
            result2 = await skill.execute(params)
            assert result2["result"]["cache_hit"] is True
            assert result2["result"]["cost_cents"] == 0.0  # No cost for cache hit
            assert mock_invoke.call_count == 1  # Still only 1 call

    @pytest.mark.asyncio
    async def test_cache_disabled_per_request(self, skill):
        """enable_cache=False should bypass cache."""
        # Configure fresh cache
        configure_prompt_cache(ttl_seconds=3600, max_size=100, enabled=True)

        with patch.object(skill, "_invoke_anthropic", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "response_text": "Hello!",
                "model_used": "claude-sonnet-4-20250514",
                "input_tokens": 10,
                "output_tokens": 5,
                "finish_reason": "end_turn",
            }

            params = {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "messages": [{"role": "user", "content": "No cache please"}],
                "enable_cache": False,  # Disable cache
            }

            # First call
            result1 = await skill.execute(params)
            assert result1["result"]["cache_hit"] is False

            # Second call - should still call LLM (cache disabled)
            result2 = await skill.execute(params)
            assert result2["result"]["cache_hit"] is False

            # LLM should have been called twice
            assert mock_invoke.call_count == 2

    @pytest.mark.asyncio
    async def test_different_params_dont_hit_cache(self, skill):
        """Different parameters should not share cache."""
        # Configure fresh cache
        configure_prompt_cache(ttl_seconds=3600, max_size=100, enabled=True)

        with patch.object(skill, "_invoke_anthropic", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "response_text": "Hello!",
                "model_used": "claude-sonnet-4-20250514",
                "input_tokens": 10,
                "output_tokens": 5,
                "finish_reason": "end_turn",
            }

            # First call
            result1 = await skill.execute(
                {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-20250514",
                    "messages": [{"role": "user", "content": "Question A"}],
                    "enable_cache": True,
                }
            )

            # Different message - should miss cache
            result2 = await skill.execute(
                {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-20250514",
                    "messages": [{"role": "user", "content": "Question B"}],
                    "enable_cache": True,
                }
            )

            assert result1["result"]["cache_hit"] is False
            assert result2["result"]["cache_hit"] is False
            assert mock_invoke.call_count == 2


# =============================================================================
# GLOBAL CACHE CONFIGURATION TESTS
# =============================================================================


class TestGlobalCacheConfiguration:
    """Test global cache configuration."""

    def test_configure_prompt_cache_creates_new_cache(self):
        """configure_prompt_cache should create new cache with settings."""
        cache = configure_prompt_cache(
            ttl_seconds=7200,
            max_size=500,
            enabled=True,
        )

        assert cache.ttl_seconds == 7200
        assert cache.max_size == 500
        assert cache.enabled is True

    def test_get_prompt_cache_returns_singleton(self):
        """get_prompt_cache should return the same instance."""
        configure_prompt_cache(ttl_seconds=3600, max_size=100, enabled=True)

        cache1 = get_prompt_cache()
        cache2 = get_prompt_cache()

        assert cache1 is cache2


# =============================================================================
# M13 ACCEPTANCE CRITERIA TESTS
# =============================================================================


class TestM13AcceptanceCriteria:
    """Tests verifying M13 prompt caching acceptance criteria."""

    def test_ac1_cache_stores_llm_responses(self):
        """AC1: Cache should store LLM responses for reuse."""
        cache = PromptCache(ttl_seconds=3600, max_size=100)

        response = {
            "response_text": "The answer is 42",
            "model_used": "claude-3-5-sonnet",
            "input_tokens": 15,
            "output_tokens": 10,
            "finish_reason": "end_turn",
        }

        cache.set(
            provider="anthropic",
            model="claude-3-5-sonnet",
            messages=[{"role": "user", "content": "What is the answer?"}],
            system_prompt="Be helpful",
            temperature=0.7,
            response=response,
            estimated_cost_cents=0.5,
        )

        cached = cache.get(
            provider="anthropic",
            model="claude-3-5-sonnet",
            messages=[{"role": "user", "content": "What is the answer?"}],
            system_prompt="Be helpful",
            temperature=0.7,
        )

        assert cached is not None
        assert cached["response_text"] == "The answer is 42"

    def test_ac2_cache_key_includes_all_relevant_params(self):
        """AC2: Cache key should differentiate by all relevant parameters."""
        cache = PromptCache()
        messages = [{"role": "user", "content": "Test"}]

        # Different providers
        key_anthropic = cache._generate_cache_key("anthropic", "model", messages, None, 0.7)
        key_openai = cache._generate_cache_key("openai", "model", messages, None, 0.7)
        assert key_anthropic != key_openai

        # Different models
        key_model1 = cache._generate_cache_key("anthropic", "model1", messages, None, 0.7)
        key_model2 = cache._generate_cache_key("anthropic", "model2", messages, None, 0.7)
        assert key_model1 != key_model2

        # Different system prompts
        key_sys1 = cache._generate_cache_key("anthropic", "model", messages, "prompt1", 0.7)
        key_sys2 = cache._generate_cache_key("anthropic", "model", messages, "prompt2", 0.7)
        assert key_sys1 != key_sys2

        # Different temperatures
        key_temp1 = cache._generate_cache_key("anthropic", "model", messages, None, 0.5)
        key_temp2 = cache._generate_cache_key("anthropic", "model", messages, None, 0.9)
        assert key_temp1 != key_temp2

    def test_ac3_ttl_expiration_works(self):
        """AC3: Cache entries should expire after TTL."""
        cache = PromptCache(ttl_seconds=1)  # 1 second

        response = {
            "response_text": "Hi",
            "model_used": "test",
            "input_tokens": 1,
            "output_tokens": 1,
            "finish_reason": "stop",
        }

        cache.set(
            provider="anthropic",
            model="test",
            messages=[{"role": "user", "content": "test"}],
            system_prompt=None,
            temperature=0.7,
            response=response,
        )

        # Should exist immediately
        assert cache.get("anthropic", "test", [{"role": "user", "content": "test"}], None, 0.7) is not None

        # Wait for expiration
        import time

        time.sleep(1.5)

        # Should be expired
        assert cache.get("anthropic", "test", [{"role": "user", "content": "test"}], None, 0.7) is None

    def test_ac4_lru_eviction_at_capacity(self):
        """AC4: LRU eviction should work when cache is at capacity."""
        cache = PromptCache(ttl_seconds=3600, max_size=2)

        response = {
            "response_text": "Hi",
            "model_used": "test",
            "input_tokens": 1,
            "output_tokens": 1,
            "finish_reason": "stop",
        }

        # Add 3 entries to cache with size 2
        for i in range(3):
            cache.set(
                provider="anthropic",
                model="test",
                messages=[{"role": "user", "content": f"msg{i}"}],
                system_prompt=None,
                temperature=0.7,
                response=response,
            )

        # First entry should be evicted
        assert cache.get("anthropic", "test", [{"role": "user", "content": "msg0"}], None, 0.7) is None
        # Latest should still exist
        assert cache.get("anthropic", "test", [{"role": "user", "content": "msg2"}], None, 0.7) is not None

    def test_ac5_cache_hit_reports_zero_cost(self):
        """AC5: Cache hits should report zero cost."""
        # This is verified in test_second_call_hits_cache
        # Cache hit returns cost_cents=0.0
        pass

    def test_ac6_cache_can_be_disabled(self):
        """AC6: Cache should be disableable globally and per-request."""
        # Global disable
        cache = PromptCache(enabled=False)
        response = {
            "response_text": "Hi",
            "model_used": "test",
            "input_tokens": 1,
            "output_tokens": 1,
            "finish_reason": "stop",
        }

        cache.set("anthropic", "test", [{"role": "user", "content": "test"}], None, 0.7, response)
        assert cache.get("anthropic", "test", [{"role": "user", "content": "test"}], None, 0.7) is None

        # Per-request disable is tested in test_cache_disabled_per_request


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
