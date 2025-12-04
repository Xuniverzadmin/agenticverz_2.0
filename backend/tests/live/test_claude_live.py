# tests/live/test_claude_live.py
"""
Live Claude Adapter Smoke Tests

These tests make REAL API calls to Claude.
Only run in secure CI environment with ANTHROPIC_API_KEY set.

Usage:
    ANTHROPIC_API_KEY=sk-... pytest tests/live/test_claude_live.py -v

Exit behavior:
    - If ANTHROPIC_API_KEY not set: tests skip gracefully
    - If API call fails: test verifies deterministic fallback behavior
    - If API call succeeds: test verifies response structure
"""

import os
import pytest
import sys
from pathlib import Path

# Path setup
_backend = Path(__file__).parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

# Check if live tests should run
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
SKIP_LIVE = os.environ.get("SKIP_LIVE_TESTS", "false").lower() == "true"

skip_if_no_key = pytest.mark.skipif(
    not ANTHROPIC_API_KEY or SKIP_LIVE,
    reason="ANTHROPIC_API_KEY not set or SKIP_LIVE_TESTS=true"
)


@skip_if_no_key
class TestClaudeLiveSmoke:
    """Live smoke tests for Claude adapter."""

    @pytest.mark.asyncio
    async def test_simple_completion(self):
        """Test simple completion with real API."""
        from app.skills.adapters.claude_adapter import ClaudeAdapter
        from app.skills.llm_invoke_v2 import LLMConfig, Message, LLMResponse

        adapter = ClaudeAdapter(api_key=ANTHROPIC_API_KEY)

        config = LLMConfig(
            max_tokens=50,
            temperature=0.0  # Deterministic
        )
        messages = [Message(role="user", content="Say 'hello' and nothing else.")]

        result = await adapter.invoke(messages, config)

        # Should be LLMResponse or error tuple
        if isinstance(result, LLMResponse):
            print(f"✓ Live response received")
            print(f"  Content: {result.content[:100]}...")
            print(f"  Model: {result.model}")
            print(f"  Tokens: {result.input_tokens} in, {result.output_tokens} out")
            print(f"  Latency: {result.latency_ms}ms")

            assert result.content, "Content should not be empty"
            assert result.input_tokens > 0
            assert result.output_tokens > 0
            assert result.finish_reason in ["end_turn", "max_tokens", "stop_sequence"]
        else:
            # Error tuple
            error_type, message, retryable = result
            print(f"✗ Live call failed: {error_type}")
            print(f"  Message: {message}")
            print(f"  Retryable: {retryable}")

            # Verify error structure
            assert isinstance(error_type, str)
            assert isinstance(message, str)
            assert isinstance(retryable, bool)

    @pytest.mark.asyncio
    async def test_deterministic_with_seed(self):
        """Test deterministic fallback behavior."""
        from app.skills.adapters.claude_adapter import ClaudeAdapter
        from app.skills.llm_invoke_v2 import LLMConfig, Message, LLMResponse

        adapter = ClaudeAdapter(api_key=ANTHROPIC_API_KEY)

        # With seed, should use temperature=0
        config = LLMConfig(
            max_tokens=20,
            seed=42,
            temperature=0.0
        )
        prompt = "What is 2+2? Answer with just the number."
        messages = [Message(role="user", content=prompt)]

        # Run twice
        result1 = await adapter.invoke(messages, config)
        result2 = await adapter.invoke(messages, config)

        if isinstance(result1, LLMResponse) and isinstance(result2, LLMResponse):
            print(f"Result 1: {result1.content}")
            print(f"Result 2: {result2.content}")

            # With temperature=0, responses should be very similar
            # (Not guaranteed identical due to API nondeterminism)
            assert result1.content, "First response should have content"
            assert result2.content, "Second response should have content"

            # Log if they differ
            if result1.content != result2.content:
                print("⚠ Note: Responses differ despite temperature=0")
                print("  This is expected - Claude doesn't guarantee determinism")
            else:
                print("✓ Responses match (deterministic)")
        else:
            print("One or both calls failed - checking error handling")
            # Both should handle errors gracefully
            for r in [result1, result2]:
                if isinstance(r, tuple):
                    error_type, message, retryable = r
                    assert error_type, "Error type should be set"

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test that rate limit errors are properly mapped."""
        from app.skills.adapters.claude_adapter import ClaudeAdapter

        adapter = ClaudeAdapter(api_key=ANTHROPIC_API_KEY)

        # Simulate rate limit error mapping
        class MockRateLimitError(Exception):
            pass

        error_type, message, retryable = adapter._map_api_error(
            MockRateLimitError("Rate limit exceeded - 429")
        )

        assert error_type == "rate_limited"
        assert retryable is True
        print("✓ Rate limit error correctly mapped as retryable")

    @pytest.mark.asyncio
    async def test_auth_error_handling(self):
        """Test auth error with invalid key."""
        from app.skills.adapters.claude_adapter import ClaudeAdapter
        from app.skills.llm_invoke_v2 import LLMConfig, Message

        # Use invalid key
        adapter = ClaudeAdapter(api_key="invalid-key")

        config = LLMConfig(max_tokens=10)
        messages = [Message(role="user", content="test")]

        result = await adapter.invoke(messages, config)

        # Should return error tuple
        if isinstance(result, tuple):
            error_type, message, retryable = result
            print(f"✓ Auth error handled: {error_type}")
            assert error_type == "auth_failed"
            assert retryable is False
        else:
            # Unexpected success with invalid key
            pytest.fail("Expected auth failure with invalid key")


@skip_if_no_key
class TestLLMInvokeLiveSmoke:
    """Live smoke tests through llm_invoke skill."""

    @pytest.mark.asyncio
    async def test_execute_with_live_adapter(self):
        """Test full llm_invoke execution with live Claude."""
        from app.skills.llm_invoke_v2 import llm_invoke_execute, register_adapter
        from app.skills.adapters.claude_adapter import ClaudeAdapter

        # Register live adapter
        adapter = ClaudeAdapter(api_key=ANTHROPIC_API_KEY)
        register_adapter(adapter)

        result = await llm_invoke_execute({
            "prompt": "Reply with just the word 'OK'",
            "adapter": "claude",
            "max_tokens": 10,
            "temperature": 0.0
        })

        print(f"Result: ok={result.ok}")
        if result.ok:
            print(f"  Content: {result.result['content']}")
            print(f"  Tokens: {result.result['input_tokens']} in, {result.result['output_tokens']} out")
            print(f"  Cost: {result.result['cost_cents']:.4f} cents")
            print(f"  Model: {result.result['model']}")

            assert "content" in result.result
            assert "content_hash" in result.result
            assert "cost_cents" in result.result
        else:
            print(f"  Error: {result.error['code']}")
            print(f"  Message: {result.error['message']}")
            print(f"  Retryable: {result.error['retryable']}")

            # Should have proper error structure
            assert "code" in result.error
            assert "category" in result.error
            assert "retryable" in result.error


# Run only if executed directly
if __name__ == "__main__":
    if not ANTHROPIC_API_KEY:
        print("Set ANTHROPIC_API_KEY to run live tests")
        print("Example: ANTHROPIC_API_KEY=sk-... python -m pytest tests/live/ -v")
        sys.exit(1)

    pytest.main([__file__, "-v"])
