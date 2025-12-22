# tests/chaos/test_llm_invoke_chaos.py
"""
Chaos Tests for LLM Invoke Skill

Tests retry behavior under various failure conditions:
- Rate limiting
- Overloaded API
- Timeouts
- Auth failures
- Deterministic fallback behavior

These tests validate error_contract.md compliance for LLM adapters.
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
    ErrorCategory,
    StubAdapter,
    _content_hash,
    llm_invoke_execute,
)


class TestLLMRateLimitHandling:
    """Test rate limit handling for LLM calls."""

    @pytest.fixture(autouse=True)
    def setup(self):
        StubAdapter.clear_responses()
        yield
        StubAdapter.clear_responses()

    @pytest.mark.asyncio
    async def test_rate_limit_error_structure(self):
        """Rate limit error has correct structure."""
        # Set up mock error
        prompt_hash = _content_hash("user: Rate limit test")
        StubAdapter.set_error(prompt_hash, "rate_limited", "Rate limit exceeded")

        result = await llm_invoke_execute({"prompt": "Rate limit test", "adapter": "stub"})

        assert result.ok is False
        assert result.error["code"] == "ERR_LLM_RATE_LIMITED"
        assert result.error["category"] == "RATE_LIMIT"
        assert result.error["retryable"] is True

    @pytest.mark.asyncio
    async def test_overloaded_error_is_transient(self):
        """Overloaded API error is transient and retryable."""
        prompt_hash = _content_hash("user: Overload test")
        StubAdapter.set_error(prompt_hash, "overloaded", "API overloaded")

        result = await llm_invoke_execute({"prompt": "Overload test", "adapter": "stub"})

        assert result.ok is False
        assert result.error["code"] == "ERR_LLM_OVERLOADED"
        assert result.error["category"] == "TRANSIENT"
        assert result.error["retryable"] is True


class TestLLMTimeoutHandling:
    """Test timeout handling for LLM calls."""

    @pytest.fixture(autouse=True)
    def setup(self):
        StubAdapter.clear_responses()
        yield
        StubAdapter.clear_responses()

    @pytest.mark.asyncio
    async def test_timeout_error_structure(self):
        """Timeout error has correct structure."""
        prompt_hash = _content_hash("user: Timeout test")
        StubAdapter.set_error(prompt_hash, "timeout", "Request timed out")

        result = await llm_invoke_execute({"prompt": "Timeout test", "adapter": "stub"})

        assert result.ok is False
        assert result.error["code"] == "ERR_LLM_TIMEOUT"
        assert result.error["category"] == "TIMEOUT"
        assert result.error["retryable"] is True


class TestLLMAuthFailure:
    """Test auth failure handling."""

    @pytest.fixture(autouse=True)
    def setup(self):
        StubAdapter.clear_responses()
        yield
        StubAdapter.clear_responses()

    @pytest.mark.asyncio
    async def test_auth_failed_not_retryable(self):
        """Auth failures are not retryable."""
        prompt_hash = _content_hash("user: Auth test")
        StubAdapter.set_error(prompt_hash, "auth_failed", "Invalid API key")

        result = await llm_invoke_execute({"prompt": "Auth test", "adapter": "stub"})

        assert result.ok is False
        assert result.error["code"] == "ERR_LLM_AUTH_FAILED"
        assert result.error["category"] == "AUTH_FAIL"
        assert result.error["retryable"] is False


class TestLLMContentBlocking:
    """Test content blocking handling."""

    @pytest.fixture(autouse=True)
    def setup(self):
        StubAdapter.clear_responses()
        yield
        StubAdapter.clear_responses()

    @pytest.mark.asyncio
    async def test_content_blocked_is_permanent(self):
        """Content blocked is permanent and not retryable."""
        prompt_hash = _content_hash("user: Blocked content")
        StubAdapter.set_error(prompt_hash, "content_blocked", "Content policy violation")

        result = await llm_invoke_execute({"prompt": "Blocked content", "adapter": "stub"})

        assert result.ok is False
        assert result.error["code"] == "ERR_LLM_CONTENT_BLOCKED"
        assert result.error["category"] == "PERMANENT"
        assert result.error["retryable"] is False


class TestLLMDeterministicFallback:
    """Test deterministic fallback behavior."""

    @pytest.fixture(autouse=True)
    def setup(self):
        StubAdapter.clear_responses()
        yield
        StubAdapter.clear_responses()

    @pytest.mark.asyncio
    async def test_seeded_response_is_deterministic(self):
        """Seeded responses are deterministic."""
        params = {"prompt": "What is the meaning of life?", "adapter": "stub", "seed": 42, "temperature": 0.0}

        result1 = await llm_invoke_execute(params)
        result2 = await llm_invoke_execute(params)

        assert result1.ok is True
        assert result2.ok is True
        assert result1.result["content"] == result2.result["content"]
        assert result1.result["content_hash"] == result2.result["content_hash"]

    @pytest.mark.asyncio
    async def test_different_seeds_different_responses(self):
        """Different seeds produce different responses."""
        result1 = await llm_invoke_execute({"prompt": "Test prompt", "adapter": "stub", "seed": 42})

        result2 = await llm_invoke_execute({"prompt": "Test prompt", "adapter": "stub", "seed": 123})

        assert result1.ok is True
        assert result2.ok is True
        assert result1.result["content"] != result2.result["content"]

    @pytest.mark.asyncio
    async def test_meta_indicates_deterministic_mode(self):
        """Meta indicates when response is deterministic."""
        result_seeded = await llm_invoke_execute({"prompt": "Test", "adapter": "stub", "seed": 42})

        result_unseeded = await llm_invoke_execute({"prompt": "Test", "adapter": "stub"})

        assert result_seeded.meta.get("deterministic") is True
        assert result_unseeded.meta.get("deterministic") is False


class TestLLMErrorContractCompliance:
    """Verify error_contract.md compliance."""

    def test_all_error_types_have_mappings(self):
        """All error types have mappings."""
        required_errors = [
            "rate_limited",
            "overloaded",
            "timeout",
            "invalid_prompt",
            "content_blocked",
            "auth_failed",
            "context_too_long",
            "invalid_model",
        ]

        for error_type in required_errors:
            assert error_type in LLM_ERROR_MAP, f"Missing mapping for {error_type}"

    def test_retryable_errors(self):
        """Retryable errors are correctly marked."""
        retryable = ["rate_limited", "overloaded", "timeout"]
        for error_type in retryable:
            assert LLM_ERROR_MAP[error_type].retryable is True

    def test_non_retryable_errors(self):
        """Non-retryable errors are correctly marked."""
        non_retryable = ["invalid_prompt", "content_blocked", "auth_failed", "context_too_long", "invalid_model"]
        for error_type in non_retryable:
            assert LLM_ERROR_MAP[error_type].retryable is False

    def test_error_categories(self):
        """Error categories are correct."""
        assert LLM_ERROR_MAP["rate_limited"].category == ErrorCategory.RATE_LIMIT
        assert LLM_ERROR_MAP["overloaded"].category == ErrorCategory.TRANSIENT
        assert LLM_ERROR_MAP["timeout"].category == ErrorCategory.TIMEOUT
        assert LLM_ERROR_MAP["auth_failed"].category == ErrorCategory.AUTH_FAIL
        assert LLM_ERROR_MAP["content_blocked"].category == ErrorCategory.PERMANENT
        assert LLM_ERROR_MAP["invalid_prompt"].category == ErrorCategory.VALIDATION


class TestLLMCostTracking:
    """Test cost tracking in chaos scenarios."""

    @pytest.fixture(autouse=True)
    def setup(self):
        StubAdapter.clear_responses()
        yield
        StubAdapter.clear_responses()

    @pytest.mark.asyncio
    async def test_cost_tracked_on_success(self):
        """Cost is tracked on successful calls."""
        result = await llm_invoke_execute({"prompt": "Cost tracking test", "adapter": "stub"})

        assert result.ok is True
        assert "cost_cents" in result.result
        assert isinstance(result.result["cost_cents"], (int, float))

    @pytest.mark.asyncio
    async def test_tokens_tracked_on_success(self):
        """Tokens are tracked on successful calls."""
        result = await llm_invoke_execute({"prompt": "Token tracking test", "adapter": "stub"})

        assert result.ok is True
        assert "input_tokens" in result.result
        assert "output_tokens" in result.result
        assert result.result["input_tokens"] > 0
        assert result.result["output_tokens"] > 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
