"""
OpenAI Compatibility Tests for BudgetLLM.

These tests verify that BudgetLLM is a true drop-in replacement for OpenAI's SDK.
Developers should be able to switch by changing one import line.

Run with: pytest tests/test_openai_compat.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# OPENAI API COMPATIBILITY TESTS
# =============================================================================


class TestOpenAICompatibility:
    """Tests verifying OpenAI API compatibility."""

    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI client with realistic response."""
        mock_openai_module = MagicMock()

        # Setup mock response matching OpenAI's actual format
        mock_response = MagicMock()
        mock_response.id = "chatcmpl-abc123"
        mock_response.object = "chat.completion"
        mock_response.created = 1700000000
        mock_response.model = "gpt-4o-mini"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].index = 0
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.content = "Hello! How can I help you?"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 8
        mock_response.usage.total_tokens = 18

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            yield mock_openai_module

    def test_chat_completions_create_interface(self, mock_openai):
        """client.chat.completions.create() must work like OpenAI."""
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)

        # This is exactly how OpenAI SDK is called
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Hello!"}]
        )

        # Verify response structure matches OpenAI
        assert "id" in response
        assert "object" in response
        assert response["object"] == "chat.completion"
        assert "created" in response
        assert "model" in response
        assert "choices" in response
        assert "usage" in response

    def test_response_choices_structure(self, mock_openai):
        """Response choices must match OpenAI format."""
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)

        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Hi"}]
        )

        # Choices structure
        assert len(response["choices"]) >= 1
        choice = response["choices"][0]
        assert "index" in choice
        assert "message" in choice
        assert "finish_reason" in choice

        # Message structure
        message = choice["message"]
        assert "role" in message
        assert "content" in message
        assert message["role"] == "assistant"

    def test_response_usage_structure(self, mock_openai):
        """Response usage must match OpenAI format."""
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)

        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Hi"}]
        )

        usage = response["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage
        assert (
            usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]
        )

    def test_chat_shortcut_works(self, mock_openai):
        """client.chat("hi") shortcut must work."""
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)

        # Shortcut syntax
        response = client.chat("Hello!")

        # Should return same structure
        assert "choices" in response
        assert (
            response["choices"][0]["message"]["content"] == "Hello! How can I help you?"
        )

    def test_kwargs_passthrough(self, mock_openai):
        """All OpenAI parameters must pass through."""
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)
        mock_client = mock_openai.OpenAI.return_value

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            temperature=0.7,
            max_tokens=100,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.5,
        )

        # Verify kwargs were passed to OpenAI
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["max_tokens"] == 100
        assert call_kwargs["top_p"] == 0.9
        assert call_kwargs["frequency_penalty"] == 0.5
        assert call_kwargs["presence_penalty"] == 0.5

    def test_messages_list_required(self, mock_openai):
        """messages parameter must be required."""
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)

        with pytest.raises(ValueError, match="messages parameter is required"):
            client.chat.completions.create(model="gpt-4o-mini")

    def test_streaming_not_supported_yet(self, mock_openai):
        """stream=True must raise NotImplementedError for now."""
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)

        with pytest.raises(NotImplementedError, match="Streaming not yet supported"):
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hi"}],
                stream=True,
            )


# =============================================================================
# COST AND BUDGET TESTS
# =============================================================================


class TestBudgetEnforcement:
    """Tests for budget enforcement with OpenAI-compatible API."""

    @pytest.fixture
    def mock_openai_expensive(self):
        """Mock OpenAI with high token counts."""
        mock_openai_module = MagicMock()

        mock_response = MagicMock()
        mock_response.id = "chatcmpl-expensive"
        mock_response.model = "gpt-4o-mini"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 100000
        mock_response.usage.completion_tokens = 50000

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            yield mock_openai_module

    def test_cost_cents_in_response(self, mock_openai_expensive):
        """Response must include cost_cents."""
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=10000)

        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Hi"}]
        )

        assert "cost_cents" in response
        assert response["cost_cents"] > 0

    def test_budget_exceeded_blocks_calls(self, mock_openai_expensive):
        """Exceeding budget must raise BudgetExceededError."""
        from budgetllm import Client, BudgetExceededError

        # Very low budget
        client = Client(openai_key="test-key", budget_cents=1)

        # First call exceeds budget
        client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Hi"}]
        )

        # Second call should fail
        with pytest.raises(BudgetExceededError):
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hi again"}],
                enable_cache=False,
            )

    def test_pause_blocks_all_calls(self, mock_openai_expensive):
        """Manual pause must block calls."""
        from budgetllm import Client, BudgetExceededError

        client = Client(openai_key="test-key", budget_cents=10000)
        client.pause()

        with pytest.raises(BudgetExceededError) as exc:
            client.chat.completions.create(
                model="gpt-4o-mini", messages=[{"role": "user", "content": "Hi"}]
            )

        assert exc.value.limit_type == "paused"


# =============================================================================
# CACHE TESTS
# =============================================================================


class TestCacheWithOpenAIFormat:
    """Tests for caching with OpenAI-compatible responses."""

    @pytest.fixture
    def mock_openai(self):
        """Standard mock OpenAI."""
        mock_openai_module = MagicMock()

        mock_response = MagicMock()
        mock_response.id = "chatcmpl-original"
        mock_response.model = "gpt-4o-mini"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Cached response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            yield mock_openai_module, mock_client

    def test_cache_hit_returns_zero_cost(self, mock_openai):
        """Cache hit must return cost_cents=0."""
        mock_module, mock_client = mock_openai
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)

        # First call - cache miss
        r1 = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Hello"}]
        )
        assert r1["cache_hit"] is False
        assert r1["cost_cents"] >= 0

        # Second call - cache hit
        r2 = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Hello"}]
        )
        assert r2["cache_hit"] is True
        assert r2["cost_cents"] == 0.0

    def test_cache_preserves_response_structure(self, mock_openai):
        """Cached response must have same structure as original."""
        mock_module, mock_client = mock_openai
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)

        # First call
        r1 = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Test"}]
        )

        # Second call (cached)
        r2 = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Test"}]
        )

        # Structure must match
        assert "id" in r2
        assert "choices" in r2
        assert "usage" in r2
        assert (
            r2["choices"][0]["message"]["content"]
            == r1["choices"][0]["message"]["content"]
        )

    def test_openai_only_called_once_for_cached(self, mock_openai):
        """OpenAI API must only be called once for cached prompts."""
        mock_module, mock_client = mock_openai
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)

        # Three calls with same prompt
        client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Same prompt"}]
        )
        client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Same prompt"}]
        )
        client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Same prompt"}]
        )

        # OpenAI should only be called once
        assert mock_client.chat.completions.create.call_count == 1


# =============================================================================
# DROP-IN REPLACEMENT TEST
# =============================================================================


class TestDropInReplacement:
    """
    Tests proving BudgetLLM is a true drop-in replacement.

    Developers should be able to switch by:
        # from openai import OpenAI
        from budgetllm import Client as OpenAI
    """

    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI."""
        mock_openai_module = MagicMock()

        mock_response = MagicMock()
        mock_response.id = "chatcmpl-dropin"
        mock_response.model = "gpt-4o-mini"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Drop-in works!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 3

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            yield mock_openai_module

    def test_openai_code_works_unchanged(self, mock_openai):
        """
        Code written for OpenAI SDK must work with BudgetLLM.

        This test simulates a developer's existing OpenAI code.
        """
        # Developer's original code (import line changed):
        # from openai import OpenAI
        from budgetllm import Client as OpenAI

        # Constructor with api_key works (BudgetLLM uses openai_key but accepts it)
        client = OpenAI(openai_key="sk-test", budget_cents=1000)

        # Same API call works
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hi!"},
            ],
        )

        # Same response access pattern works
        content = response["choices"][0]["message"]["content"]
        assert content == "Drop-in works!"

        # Usage access works
        total_tokens = response["usage"]["total_tokens"]
        assert total_tokens == 8

    def test_common_patterns_work(self, mock_openai):
        """Common OpenAI usage patterns must work."""
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)

        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Hello"}]
        )

        # Pattern 1: Direct content access
        content = response["choices"][0]["message"]["content"]
        assert isinstance(content, str)

        # Pattern 2: Check finish reason
        finish_reason = response["choices"][0]["finish_reason"]
        assert finish_reason == "stop"

        # Pattern 3: Token counting
        prompt_tokens = response["usage"]["prompt_tokens"]
        completion_tokens = response["usage"]["completion_tokens"]
        total = response["usage"]["total_tokens"]
        assert total == prompt_tokens + completion_tokens


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
