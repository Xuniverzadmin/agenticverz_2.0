# tests/skills/test_stubs.py
"""
Skill Stubs Tests (M2)

Tests for deterministic stub implementations:
- http_call_stub
- llm_invoke_stub
- json_transform_stub
"""

import sys
from pathlib import Path

import pytest

# Direct path to stubs to avoid pydantic-dependent imports through skills/__init__.py
_stubs_path = str(Path(__file__).parent.parent.parent / "app" / "skills" / "stubs")
if _stubs_path not in sys.path:
    sys.path.insert(0, _stubs_path)

from http_call_stub import (
    HTTP_CALL_STUB_DESCRIPTOR,
    HttpCallStub,
    MockResponse,
    configure_http_call_stub,
    http_call_stub_handler,
)
from json_transform_stub import JSON_TRANSFORM_STUB_DESCRIPTOR, JsonTransformStub, json_transform_stub_handler
from llm_invoke_stub import LLM_INVOKE_STUB_DESCRIPTOR, LlmInvokeStub, MockLlmResponse, llm_invoke_stub_handler

# ============================================================================
# Test: HTTP Call Stub
# ============================================================================


class TestHttpCallStub:
    """Tests for http_call stub."""

    @pytest.fixture
    def stub(self):
        """Create a fresh stub instance."""
        return HttpCallStub()

    @pytest.mark.asyncio
    async def test_default_response(self, stub):
        """Default response is returned for unknown URLs."""
        result = await stub.execute({"url": "https://unknown.example.com"})

        assert result["status_code"] == 200
        assert result["body"]["stub"] is True
        assert "x-stub" in result["headers"]

    @pytest.mark.asyncio
    async def test_custom_response(self, stub):
        """Custom response is returned for configured URL."""
        stub.add_response(
            "https://api.example.com/data", MockResponse(status_code=200, body={"key": "value"}, latency_ms=100)
        )

        result = await stub.execute({"url": "https://api.example.com/data"})

        assert result["status_code"] == 200
        assert result["body"]["key"] == "value"
        assert result["latency_ms"] == 100

    @pytest.mark.asyncio
    async def test_prefix_matching(self, stub):
        """URL prefix matching works."""
        stub.add_response("https://api.example.com", MockResponse(status_code=201, body={"matched": "prefix"}))

        result = await stub.execute({"url": "https://api.example.com/any/path"})

        assert result["status_code"] == 201
        assert result["body"]["matched"] == "prefix"

    @pytest.mark.asyncio
    async def test_deterministic_body_hash(self, stub):
        """Body hash is deterministic."""
        stub.add_response("https://test.com", MockResponse(body={"data": [1, 2, 3]}))

        r1 = await stub.execute({"url": "https://test.com"})
        r2 = await stub.execute({"url": "https://test.com"})

        assert r1["body_hash"] == r2["body_hash"]

    @pytest.mark.asyncio
    async def test_call_history(self, stub):
        """Calls are recorded in history."""
        await stub.execute({"url": "https://a.com", "method": "GET"})
        await stub.execute({"url": "https://b.com", "method": "POST"})

        assert len(stub.call_history) == 2
        assert stub.call_history[0]["url"] == "https://a.com"
        assert stub.call_history[1]["method"] == "POST"

    def test_descriptor_has_failure_modes(self):
        """Descriptor includes failure modes."""
        assert len(HTTP_CALL_STUB_DESCRIPTOR.failure_modes) > 0
        codes = [fm["code"] for fm in HTTP_CALL_STUB_DESCRIPTOR.failure_modes]
        assert "ERR_TIMEOUT" in codes
        assert "ERR_DNS_FAILURE" in codes


# ============================================================================
# Test: LLM Invoke Stub
# ============================================================================


class TestLlmInvokeStub:
    """Tests for llm_invoke stub."""

    @pytest.fixture
    def stub(self):
        """Create a fresh stub instance."""
        return LlmInvokeStub()

    @pytest.mark.asyncio
    async def test_deterministic_response(self, stub):
        """Same prompt produces same response."""
        r1 = await stub.execute({"prompt": "What is 2+2?"})
        r2 = await stub.execute({"prompt": "What is 2+2?"})

        assert r1["content"] == r2["content"]
        assert r1["prompt_hash"] == r2["prompt_hash"]
        assert r1["response_hash"] == r2["response_hash"]

    @pytest.mark.asyncio
    async def test_different_prompts_different_responses(self, stub):
        """Different prompts produce different responses."""
        r1 = await stub.execute({"prompt": "Question A"})
        r2 = await stub.execute({"prompt": "Question B"})

        assert r1["prompt_hash"] != r2["prompt_hash"]

    @pytest.mark.asyncio
    async def test_custom_response(self, stub):
        """Custom response for prompt pattern."""
        stub.add_response("analyze", MockLlmResponse(content="Analysis: Everything looks good.", output_tokens=6))

        result = await stub.execute({"prompt": "Please analyze this data"})

        assert "Analysis" in result["content"]
        assert result["usage"]["output_tokens"] == 6

    @pytest.mark.asyncio
    async def test_token_counting(self, stub):
        """Tokens are counted correctly."""
        result = await stub.execute({"prompt": "one two three four five"})

        assert result["usage"]["input_tokens"] == 5
        assert result["usage"]["total_tokens"] > 0

    @pytest.mark.asyncio
    async def test_cost_estimation(self, stub):
        """Cost is estimated based on tokens."""
        result = await stub.execute({"prompt": "test prompt"})

        assert "cost_cents" in result
        assert result["cost_cents"] >= 1

    def test_descriptor_has_cost_model(self):
        """Descriptor includes cost model."""
        assert LLM_INVOKE_STUB_DESCRIPTOR.cost_model["base_cents"] == 1
        assert "per_token_cents" in LLM_INVOKE_STUB_DESCRIPTOR.cost_model


# ============================================================================
# Test: JSON Transform Stub
# ============================================================================


class TestJsonTransformStub:
    """Tests for json_transform stub."""

    @pytest.fixture
    def stub(self):
        """Create a fresh stub instance."""
        return JsonTransformStub()

    @pytest.mark.asyncio
    async def test_extract_simple(self, stub):
        """Extract simple value."""
        result = await stub.execute({"data": {"name": "Alice", "age": 30}, "operation": "extract", "path": "$.name"})

        assert result["output"] == "Alice"

    @pytest.mark.asyncio
    async def test_extract_nested(self, stub):
        """Extract nested value."""
        result = await stub.execute(
            {
                "data": {"user": {"profile": {"email": "test@example.com"}}},
                "operation": "extract",
                "path": "$.user.profile.email",
            }
        )

        assert result["output"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_extract_array_index(self, stub):
        """Extract array item by index."""
        result = await stub.execute({"data": {"items": ["a", "b", "c"]}, "operation": "extract", "path": "$.items[1]"})

        assert result["output"] == "b"

    @pytest.mark.asyncio
    async def test_pick_keys(self, stub):
        """Pick specific keys from object."""
        result = await stub.execute({"data": {"a": 1, "b": 2, "c": 3}, "operation": "pick", "keys": ["a", "c"]})

        assert result["output"] == {"a": 1, "c": 3}

    @pytest.mark.asyncio
    async def test_omit_keys(self, stub):
        """Omit specific keys from object."""
        result = await stub.execute({"data": {"a": 1, "b": 2, "c": 3}, "operation": "omit", "keys": ["b"]})

        assert result["output"] == {"a": 1, "c": 3}

    @pytest.mark.asyncio
    async def test_filter_array(self, stub):
        """Filter array items."""
        result = await stub.execute(
            {
                "data": [{"type": "A", "value": 1}, {"type": "B", "value": 2}, {"type": "A", "value": 3}],
                "operation": "filter",
                "condition": {"type": "A"},
            }
        )

        assert len(result["output"]) == 2
        assert all(item["type"] == "A" for item in result["output"])

    @pytest.mark.asyncio
    async def test_merge_objects(self, stub):
        """Merge two objects."""
        result = await stub.execute({"data": {"a": 1, "b": 2}, "operation": "merge", "with": {"c": 3, "d": 4}})

        assert result["output"] == {"a": 1, "b": 2, "c": 3, "d": 4}

    @pytest.mark.asyncio
    async def test_deterministic_hash(self, stub):
        """Output hash is deterministic."""
        r1 = await stub.execute({"data": {"key": "value"}, "operation": "extract", "path": "$"})
        r2 = await stub.execute({"data": {"key": "value"}, "operation": "extract", "path": "$"})

        assert r1["output_hash"] == r2["output_hash"]

    def test_descriptor_has_constraints(self):
        """Descriptor includes constraints."""
        assert "max_input_size_bytes" in JSON_TRANSFORM_STUB_DESCRIPTOR.constraints
        assert "max_depth" in JSON_TRANSFORM_STUB_DESCRIPTOR.constraints


# ============================================================================
# Test: Global Stubs
# ============================================================================


class TestGlobalStubs:
    """Tests for global stub instances."""

    @pytest.mark.asyncio
    async def test_http_call_stub_handler(self):
        """Global http_call handler works."""
        # Configure global stub
        stub = HttpCallStub()
        stub.add_response("https://global.test", MockResponse(status_code=202, body={"global": True}))
        configure_http_call_stub(stub)

        result = await http_call_stub_handler({"url": "https://global.test"})
        assert result["status_code"] == 202

    @pytest.mark.asyncio
    async def test_llm_invoke_stub_handler(self):
        """Global llm_invoke handler works."""
        result = await llm_invoke_stub_handler({"prompt": "test"})
        assert "content" in result
        assert "prompt_hash" in result

    @pytest.mark.asyncio
    async def test_json_transform_stub_handler(self):
        """Global json_transform handler works."""
        result = await json_transform_stub_handler({"data": {"x": 1}, "operation": "extract", "path": "$.x"})
        assert result["output"] == 1
