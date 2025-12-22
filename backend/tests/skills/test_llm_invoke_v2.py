# tests/skills/test_llm_invoke_v2.py
"""
Tests for LLM Invoke Skill v2 (M3)

Tests adapter pattern, deterministic seeding, error handling,
and cost tracking.
"""

import sys
from pathlib import Path

import pytest

# Path setup
_backend = Path(__file__).parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.skills.llm_invoke_v2 import (
    LLM_ERROR_MAP,
    LLM_INVOKE_DESCRIPTOR,
    ErrorCategory,
    LLMConfig,
    LLMResponse,
    Message,
    StubAdapter,
    _canonical_json,
    _content_hash,
    _generate_call_id,
    estimate_cost,
    get_adapter,
    list_adapters,
    llm_invoke_execute,
)


class TestCanonicalJson:
    """Test canonical JSON utilities."""

    def test_canonical_json_sorted_keys(self):
        """Keys must be sorted alphabetically."""
        data = {"z": 1, "a": 2, "m": 3}
        canonical = _canonical_json(data)
        assert canonical == '{"a":2,"m":3,"z":1}'

    def test_content_hash_deterministic(self):
        """Same input produces same hash."""
        text = "Hello, world!"
        hash1 = _content_hash(text)
        hash2 = _content_hash(text)
        assert hash1 == hash2
        assert len(hash1) == 16

    def test_generate_call_id_deterministic(self):
        """Call ID is deterministic from params."""
        params = {"prompt": "Hello", "adapter": "stub"}
        id1 = _generate_call_id(params)
        id2 = _generate_call_id(params)
        assert id1 == id2
        assert id1.startswith("llm_")


class TestErrorMappings:
    """Test error mapping constants."""

    def test_rate_limited(self):
        """Rate limited error is mapped correctly."""
        mapping = LLM_ERROR_MAP["rate_limited"]
        assert mapping.code == "ERR_LLM_RATE_LIMITED"
        assert mapping.category == ErrorCategory.RATE_LIMIT
        assert mapping.retryable is True

    def test_auth_failed(self):
        """Auth failed error is not retryable."""
        mapping = LLM_ERROR_MAP["auth_failed"]
        assert mapping.code == "ERR_LLM_AUTH_FAILED"
        assert mapping.category == ErrorCategory.AUTH_FAIL
        assert mapping.retryable is False

    def test_content_blocked(self):
        """Content blocked is permanent."""
        mapping = LLM_ERROR_MAP["content_blocked"]
        assert mapping.code == "ERR_LLM_CONTENT_BLOCKED"
        assert mapping.category == ErrorCategory.PERMANENT
        assert mapping.retryable is False

    def test_timeout(self):
        """Timeout is retryable."""
        mapping = LLM_ERROR_MAP["timeout"]
        assert mapping.code == "ERR_LLM_TIMEOUT"
        assert mapping.category == ErrorCategory.TIMEOUT
        assert mapping.retryable is True


class TestCostEstimation:
    """Test cost estimation."""

    def test_stub_is_free(self):
        """Stub model costs nothing."""
        cost = estimate_cost("stub", 1000, 500)
        assert cost == 0

    def test_claude_sonnet_cost(self):
        """Claude Sonnet cost calculation."""
        # 1M input tokens = 300 cents, 1M output = 1500 cents
        cost = estimate_cost("claude-3-5-sonnet-20241022", 1_000_000, 1_000_000)
        assert cost == 300 + 1500

    def test_unknown_model_default(self):
        """Unknown model uses default cost."""
        cost = estimate_cost("unknown-model", 1_000_000, 1_000_000)
        # Default: 100 input + 500 output per 1M tokens
        assert cost == 100 + 500


class TestStubAdapter:
    """Test stub adapter."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear mock responses before each test."""
        StubAdapter.clear_responses()
        yield
        StubAdapter.clear_responses()

    def test_adapter_id(self):
        """Adapter has correct ID."""
        adapter = StubAdapter()
        assert adapter.adapter_id == "stub"

    def test_supports_seeding(self):
        """Stub adapter supports seeding."""
        adapter = StubAdapter()
        assert adapter.supports_seeding() is True

    def test_default_model(self):
        """Default model is stub."""
        adapter = StubAdapter()
        assert adapter.default_model == "stub"

    @pytest.mark.asyncio
    async def test_simple_invoke(self):
        """Simple invocation returns response."""
        adapter = StubAdapter()
        config = LLMConfig()
        messages = [Message(role="user", content="Hello")]

        response = await adapter.invoke(messages, config)

        assert isinstance(response, LLMResponse)
        assert response.model == "stub"
        assert response.finish_reason == "end_turn"
        assert response.input_tokens > 0

    @pytest.mark.asyncio
    async def test_deterministic_with_seed(self):
        """Same seed produces same response."""
        adapter = StubAdapter()
        config = LLMConfig(seed=42)
        messages = [Message(role="user", content="What is 2+2?")]

        response1 = await adapter.invoke(messages, config)
        response2 = await adapter.invoke(messages, config)

        assert response1.content == response2.content
        assert response1.seed == 42

    @pytest.mark.asyncio
    async def test_different_seeds_different_responses(self):
        """Different seeds produce different responses."""
        adapter = StubAdapter()
        messages = [Message(role="user", content="What is 2+2?")]

        config1 = LLMConfig(seed=42)
        config2 = LLMConfig(seed=123)

        response1 = await adapter.invoke(messages, config1)
        response2 = await adapter.invoke(messages, config2)

        assert response1.content != response2.content

    @pytest.mark.asyncio
    async def test_mock_error(self):
        """Mock error response."""
        adapter = StubAdapter()
        # Prompt hash is computed from "role: content" format
        prompt_text = "user: Error test"
        prompt_hash = _content_hash(prompt_text)
        StubAdapter.set_error(prompt_hash, "rate_limited", "Rate limit exceeded")

        config = LLMConfig()
        messages = [Message(role="user", content="Error test")]

        response = await adapter.invoke(messages, config)

        assert isinstance(response, tuple)
        error_type, message, retryable = response
        assert error_type == "rate_limited"
        assert retryable is True


class TestAdapterRegistry:
    """Test adapter registry."""

    def test_stub_registered_by_default(self):
        """Stub adapter is registered by default."""
        assert "stub" in list_adapters()
        adapter = get_adapter("stub")
        assert adapter is not None
        assert isinstance(adapter, StubAdapter)

    def test_get_unknown_adapter(self):
        """Unknown adapter returns None."""
        adapter = get_adapter("unknown")
        assert adapter is None


class TestLLMInvokeExecute:
    """Test main execute function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear mock responses before each test."""
        StubAdapter.clear_responses()
        yield
        StubAdapter.clear_responses()

    @pytest.mark.asyncio
    async def test_simple_prompt(self):
        """Simple string prompt succeeds."""
        result = await llm_invoke_execute({"prompt": "Hello, world!", "adapter": "stub"})

        assert result.ok is True
        assert "content" in result.result
        assert "content_hash" in result.result
        assert "input_tokens" in result.result
        assert "output_tokens" in result.result
        assert result.result["model"] == "stub"

    @pytest.mark.asyncio
    async def test_messages_format(self):
        """Messages array format works."""
        result = await llm_invoke_execute(
            {
                "prompt": [{"role": "system", "content": "You are helpful."}, {"role": "user", "content": "Hi"}],
                "adapter": "stub",
            }
        )

        assert result.ok is True

    @pytest.mark.asyncio
    async def test_with_seed(self):
        """Seed is passed through and response is deterministic."""
        params = {"prompt": "What is the meaning of life?", "adapter": "stub", "seed": 42, "temperature": 0.0}

        result1 = await llm_invoke_execute(params)
        result2 = await llm_invoke_execute(params)

        assert result1.ok is True
        assert result2.ok is True
        assert result1.result["content"] == result2.result["content"]
        assert result1.result["content_hash"] == result2.result["content_hash"]
        assert result1.result["seed"] == 42

    @pytest.mark.asyncio
    async def test_missing_prompt(self):
        """Missing prompt returns error."""
        result = await llm_invoke_execute({"adapter": "stub"})

        assert result.ok is False
        assert result.error["code"] == "ERR_LLM_INVALID_PROMPT"
        assert result.error["category"] == "VALIDATION"
        assert result.error["retryable"] is False

    @pytest.mark.asyncio
    async def test_unknown_adapter(self):
        """Unknown adapter returns error."""
        result = await llm_invoke_execute({"prompt": "Hello", "adapter": "nonexistent"})

        assert result.ok is False
        assert result.error["code"] == "ERR_LLM_ADAPTER_NOT_FOUND"
        assert "available" in result.error["details"]

    @pytest.mark.asyncio
    async def test_rate_limited_error(self):
        """Rate limited error is handled correctly."""
        # Set up mock error - hash is computed from "user: content" format
        prompt_hash = _content_hash("user: Rate limit test")
        StubAdapter.set_error(prompt_hash, "rate_limited", "Too many requests")

        result = await llm_invoke_execute({"prompt": "Rate limit test", "adapter": "stub"})

        assert result.ok is False
        assert result.error["code"] == "ERR_LLM_RATE_LIMITED"
        assert result.error["category"] == "RATE_LIMIT"
        assert result.error["retryable"] is True

    @pytest.mark.asyncio
    async def test_content_blocked_error(self):
        """Content blocked error is permanent."""
        # Hash is computed from "user: content" format
        prompt_hash = _content_hash("user: Blocked content")
        StubAdapter.set_error(prompt_hash, "content_blocked", "Content policy violation")

        result = await llm_invoke_execute({"prompt": "Blocked content", "adapter": "stub"})

        assert result.ok is False
        assert result.error["code"] == "ERR_LLM_CONTENT_BLOCKED"
        assert result.error["category"] == "PERMANENT"
        assert result.error["retryable"] is False

    @pytest.mark.asyncio
    async def test_cost_tracking(self):
        """Cost is tracked in result."""
        result = await llm_invoke_execute({"prompt": "Hello", "adapter": "stub"})

        assert result.ok is True
        assert "cost_cents" in result.result
        assert result.result["cost_cents"] == 0  # Stub is free

    @pytest.mark.asyncio
    async def test_deterministic_metadata(self):
        """Meta includes deterministic flag when seeded."""
        result = await llm_invoke_execute({"prompt": "Test", "adapter": "stub", "seed": 123})

        assert result.ok is True
        assert result.meta.get("deterministic") is True

    @pytest.mark.asyncio
    async def test_non_deterministic_metadata(self):
        """Meta shows non-deterministic when not seeded."""
        result = await llm_invoke_execute({"prompt": "Test", "adapter": "stub"})

        assert result.ok is True
        assert result.meta.get("deterministic") is False


class TestDescriptor:
    """Test skill descriptor."""

    def test_descriptor_fields(self):
        """Descriptor has required fields."""
        d = LLM_INVOKE_DESCRIPTOR
        assert d.skill_id == "skill.llm_invoke"
        assert d.version == "2.0.0"
        assert "content_hash" in d.stable_fields
        assert "input_tokens" in d.stable_fields
        assert "output_tokens" in d.stable_fields

    def test_failure_modes_defined(self):
        """Failure modes match error contract."""
        d = LLM_INVOKE_DESCRIPTOR
        assert "ERR_LLM_RATE_LIMITED" in d.failure_modes
        assert "ERR_LLM_TIMEOUT" in d.failure_modes
        assert "ERR_LLM_AUTH_FAILED" in d.failure_modes
        assert "ERR_LLM_CONTENT_BLOCKED" in d.failure_modes

    def test_constraints_defined(self):
        """Constraints are defined."""
        d = LLM_INVOKE_DESCRIPTOR
        assert d.constraints["max_prompt_tokens"] == 100000
        assert d.constraints["max_output_tokens"] == 100000


class TestDeterminism:
    """Test deterministic behavior."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear mock responses before each test."""
        StubAdapter.clear_responses()
        yield
        StubAdapter.clear_responses()

    @pytest.mark.asyncio
    async def test_same_params_same_id(self):
        """Same params produce same call ID."""
        params = {"prompt": "Test", "adapter": "stub"}

        result1 = await llm_invoke_execute(params)
        result2 = await llm_invoke_execute(params)

        assert result1.id == result2.id

    @pytest.mark.asyncio
    async def test_content_hash_stable(self):
        """Content hash is stable for same content."""
        params = {"prompt": "Stable content", "adapter": "stub", "seed": 42}

        result1 = await llm_invoke_execute(params)
        result2 = await llm_invoke_execute(params)

        assert result1.result["content_hash"] == result2.result["content_hash"]

    @pytest.mark.asyncio
    async def test_different_prompts_different_hashes(self):
        """Different prompts produce different content hashes."""
        result1 = await llm_invoke_execute({"prompt": "First prompt", "adapter": "stub", "seed": 42})

        result2 = await llm_invoke_execute({"prompt": "Second prompt", "adapter": "stub", "seed": 42})

        assert result1.result["content_hash"] != result2.result["content_hash"]


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
