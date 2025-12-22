# tests/skills/test_claude_adapter.py
"""
Tests for Claude Adapter (M3)

Tests the ClaudeAdapterStub for deterministic testing.
Real API tests require ANTHROPIC_API_KEY.
"""

import sys
from pathlib import Path

import pytest

# Path setup
_backend = Path(__file__).parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.skills.adapters.claude_adapter import (
    CLAUDE_COST_MODEL,
    DEFAULT_MODEL,
    ClaudeAdapter,
    ClaudeAdapterStub,
)
from app.skills.llm_invoke_v2 import (
    LLMConfig,
    LLMResponse,
    Message,
    get_adapter,
)


class TestClaudeAdapterProperties:
    """Test adapter properties."""

    def test_adapter_id(self):
        """Adapter has correct ID."""
        adapter = ClaudeAdapter()
        assert adapter.adapter_id == "claude"

    def test_default_model(self):
        """Default model is set."""
        adapter = ClaudeAdapter()
        assert adapter.default_model == DEFAULT_MODEL
        assert "claude" in adapter.default_model

    def test_supports_seeding_false(self):
        """Claude doesn't natively support seeding."""
        adapter = ClaudeAdapter()
        assert adapter.supports_seeding() is False


class TestClaudeAdapterStub:
    """Test stub adapter for testing."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear mock responses before each test."""
        stub = ClaudeAdapterStub()
        stub.clear_mocks()
        yield stub

    def test_stub_adapter_id(self, setup):
        """Stub has same adapter ID."""
        assert setup.adapter_id == "claude"

    def test_stub_supports_seeding(self, setup):
        """Stub supports seeding for determinism."""
        assert setup.supports_seeding() is True

    @pytest.mark.asyncio
    async def test_simple_invoke(self, setup):
        """Simple invocation returns response."""
        config = LLMConfig()
        messages = [Message(role="user", content="Hello")]

        response = await setup.invoke(messages, config)

        assert isinstance(response, LLMResponse)
        assert "Claude stub response" in response.content
        assert response.finish_reason == "end_turn"

    @pytest.mark.asyncio
    async def test_deterministic_with_seed(self, setup):
        """Same seed produces same response."""
        config = LLMConfig(seed=42)
        messages = [Message(role="user", content="What is 2+2?")]

        response1 = await setup.invoke(messages, config)
        response2 = await setup.invoke(messages, config)

        assert response1.content == response2.content
        assert response1.seed == 42

    @pytest.mark.asyncio
    async def test_different_seeds_different_responses(self, setup):
        """Different seeds produce different responses."""
        messages = [Message(role="user", content="What is 2+2?")]

        config1 = LLMConfig(seed=42)
        config2 = LLMConfig(seed=123)

        response1 = await setup.invoke(messages, config1)
        response2 = await setup.invoke(messages, config2)

        assert response1.content != response2.content

    @pytest.mark.asyncio
    async def test_mock_error_response(self, setup):
        """Mock error is returned."""
        import hashlib

        prompt = "user: Error test"
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        setup.set_mock_response(prompt_hash, ("rate_limited", "Rate limit hit", True))

        config = LLMConfig()
        messages = [Message(role="user", content="Error test")]

        response = await setup.invoke(messages, config)

        assert isinstance(response, tuple)
        error_type, message, retryable = response
        assert error_type == "rate_limited"
        assert retryable is True

    @pytest.mark.asyncio
    async def test_string_prompt(self, setup):
        """String prompt works."""
        config = LLMConfig()
        prompt = "Hello, world!"

        response = await setup.invoke(prompt, config)

        assert isinstance(response, LLMResponse)
        assert "Hello" in response.content

    @pytest.mark.asyncio
    async def test_with_system_prompt(self, setup):
        """System prompt is handled."""
        config = LLMConfig(system_prompt="You are a helpful assistant.")
        messages = [Message(role="system", content="Be concise."), Message(role="user", content="Hi")]

        response = await setup.invoke(messages, config)

        assert isinstance(response, LLMResponse)


class TestClaudeErrorMapping:
    """Test error mapping."""

    def test_rate_limit_error(self):
        """Rate limit is mapped correctly."""
        adapter = ClaudeAdapter()

        class RateLimitError(Exception):
            pass

        error_type, _, retryable = adapter._map_api_error(RateLimitError("Rate limit exceeded"))
        assert error_type == "rate_limited"
        assert retryable is True

    def test_auth_error(self):
        """Auth error is not retryable."""
        adapter = ClaudeAdapter()

        class AuthError(Exception):
            pass

        error_type, _, retryable = adapter._map_api_error(AuthError("Invalid API key"))
        assert error_type == "auth_failed"
        assert retryable is False

    def test_timeout_error(self):
        """Timeout is retryable."""
        adapter = ClaudeAdapter()

        class TimeoutError(Exception):
            pass

        error_type, _, retryable = adapter._map_api_error(TimeoutError("Request timeout"))
        assert error_type == "timeout"
        assert retryable is True

    def test_content_blocked_error(self):
        """Content blocked is permanent."""
        adapter = ClaudeAdapter()

        error_type, _, retryable = adapter._map_api_error(Exception("Content blocked by policy"))
        assert error_type == "content_blocked"
        assert retryable is False

    def test_unknown_error_is_retryable(self):
        """Unknown errors default to retryable."""
        adapter = ClaudeAdapter()

        error_type, _, retryable = adapter._map_api_error(Exception("Something went wrong"))
        assert retryable is True


class TestCostModel:
    """Test cost model constants."""

    def test_sonnet_cost(self):
        """Sonnet cost is defined."""
        assert "claude-3-5-sonnet-20241022" in CLAUDE_COST_MODEL
        model_cost = CLAUDE_COST_MODEL["claude-3-5-sonnet-20241022"]
        assert model_cost["input"] == 300
        assert model_cost["output"] == 1500

    def test_haiku_cost(self):
        """Haiku is cheaper than Sonnet."""
        haiku_cost = CLAUDE_COST_MODEL["claude-3-haiku-20240307"]
        sonnet_cost = CLAUDE_COST_MODEL["claude-3-5-sonnet-20241022"]

        assert haiku_cost["input"] < sonnet_cost["input"]
        assert haiku_cost["output"] < sonnet_cost["output"]


class TestTokenEstimation:
    """Test token estimation."""

    def test_estimate_tokens(self):
        """Token estimation is reasonable."""
        adapter = ClaudeAdapter()

        # Roughly 3.5 chars per token for Claude
        text = "Hello world, this is a test."  # 28 chars
        tokens = adapter.estimate_tokens(text)

        # Should be around 8-10 tokens
        assert 5 < tokens < 15


class TestRegistration:
    """Test adapter registration."""

    def test_register_claude_adapter(self):
        """Claude adapter can be registered."""
        from app.skills.adapters.claude_adapter import register_claude_adapter

        adapter = register_claude_adapter()
        assert adapter is not None
        assert adapter.adapter_id == "claude"

        # Should now be in registry
        registered = get_adapter("claude")
        assert registered is not None


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
