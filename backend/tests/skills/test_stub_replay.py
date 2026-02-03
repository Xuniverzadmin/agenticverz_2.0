# tests/skills/test_stub_replay.py
"""
Stub Replay Tests

Tests that stubs produce deterministic outputs suitable for replay testing.
Uses golden files to verify output consistency across runs.

Key properties tested:
1. Same input → Same output (determinism)
2. Output structure matches golden file
3. Deterministic fields match exactly
4. Hashes are stable
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Add paths
_backend_path = str(Path(__file__).parent.parent.parent)
_runtime_path = str(Path(__file__).parent.parent.parent / "app" / "worker" / "runtime")


for p in [_backend_path, _runtime_path, _skills_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

from stubs.http_call_stub import (
    HttpCallStub,
)
from stubs.json_transform_stub import (
    JsonTransformStub,
)
from stubs.llm_invoke_stub import (
    LlmInvokeStub,
)

GOLDEN_DIR = Path(__file__).parent.parent / "golden"


def load_golden(name: str) -> Dict[str, Any]:
    """Load a golden file."""
    path = GOLDEN_DIR / f"{name}.json"
    with open(path) as f:
        return json.load(f)


class TestHttpCallStubReplay:
    """Replay tests for http_call stub."""

    @pytest.fixture
    def stub(self):
        """Create fresh stub instance."""
        stub = HttpCallStub()
        stub.add_response(
            "api.example.com",
            {"status_code": 200, "body": '{"result": "ok"}', "headers": {"content-type": "application/json"}},
        )
        return stub

    @pytest.mark.asyncio
    async def test_deterministic_output(self, stub):
        """Same input produces same output."""
        inputs = {"url": "https://api.example.com/test", "method": "GET"}

        result1 = await stub.execute(inputs)
        result2 = await stub.execute(inputs)

        # Core fields must match
        assert result1["status_code"] == result2["status_code"]
        assert result1["body_hash"] == result2["body_hash"]

    @pytest.mark.asyncio
    async def test_different_urls_different_hashes(self, stub):
        """Different URLs produce different body hashes."""
        stub.add_response("other.api.com", {"status_code": 200, "body": "different"})

        result1 = await stub.execute({"url": "https://api.example.com/test"})
        result2 = await stub.execute({"url": "https://other.api.com/test"})

        # Hashes should differ
        assert result1["body_hash"] != result2["body_hash"]

    @pytest.mark.asyncio
    async def test_call_history_recorded(self, stub):
        """Call history is recorded for verification."""
        inputs = {"url": "https://api.example.com/test", "method": "GET"}

        await stub.execute(inputs)
        await stub.execute(inputs)

        assert len(stub.call_history) == 2
        assert all(h["url"] == inputs["url"] for h in stub.call_history)


class TestLlmInvokeStubReplay:
    """Replay tests for llm_invoke stub."""

    @pytest.fixture
    def stub(self):
        """Create fresh stub instance."""
        return LlmInvokeStub()

    @pytest.mark.asyncio
    async def test_deterministic_response(self, stub):
        """Same prompt produces same response."""
        inputs = {"prompt": "Analyze this data", "model": "stub-model"}

        result1 = await stub.execute(inputs)
        result2 = await stub.execute(inputs)

        # Response must be identical
        assert result1["content"] == result2["content"]
        assert result1["prompt_hash"] == result2["prompt_hash"]
        assert result1["response_hash"] == result2["response_hash"]

    @pytest.mark.asyncio
    async def test_prompt_hash_deterministic(self, stub):
        """Prompt hash is deterministic."""
        prompt = "What is the meaning of life?"

        result1 = await stub.execute({"prompt": prompt})
        result2 = await stub.execute({"prompt": prompt})

        assert result1["prompt_hash"] == result2["prompt_hash"]

    @pytest.mark.asyncio
    async def test_different_prompts_different_hashes(self, stub):
        """Different prompts produce different hashes."""
        result1 = await stub.execute({"prompt": "Hello world"})
        result2 = await stub.execute({"prompt": "Goodbye world"})

        assert result1["prompt_hash"] != result2["prompt_hash"]

    @pytest.mark.asyncio
    async def test_custom_response_override(self, stub):
        """Custom responses can be configured."""
        from stubs.llm_invoke_stub import MockLlmResponse

        stub.add_response("analyze", MockLlmResponse(content="Custom analysis result", output_tokens=5))

        result = await stub.execute({"prompt": "Please analyze the data"})

        assert result["content"] == "Custom analysis result"

    @pytest.mark.asyncio
    async def test_token_counting(self, stub):
        """Token counts are included."""
        result = await stub.execute({"prompt": "Short prompt"})

        assert "usage" in result
        assert "input_tokens" in result["usage"]
        assert "output_tokens" in result["usage"]
        assert "total_tokens" in result["usage"]


class TestJsonTransformStubReplay:
    """Replay tests for json_transform stub."""

    @pytest.fixture
    def stub(self):
        """Create fresh stub instance."""
        return JsonTransformStub()

    @pytest.mark.asyncio
    async def test_extract_deterministic(self, stub):
        """Extract operation is deterministic."""
        inputs = {
            "data": {"user": {"name": "Alice", "email": "alice@example.com"}},
            "operation": "extract",
            "path": "$.user.email",
        }

        result1 = await stub.execute(inputs)
        result2 = await stub.execute(inputs)

        assert result1["output"] == result2["output"]
        assert result1["output_hash"] == result2["output_hash"]

    @pytest.mark.asyncio
    async def test_pick_deterministic(self, stub):
        """Pick operation is deterministic."""
        inputs = {"data": {"a": 1, "b": 2, "c": 3}, "operation": "pick", "keys": ["a", "c"]}

        result1 = await stub.execute(inputs)
        result2 = await stub.execute(inputs)

        assert result1["output"] == result2["output"]
        assert result1["output"] == {"a": 1, "c": 3}

    @pytest.mark.asyncio
    async def test_omit_deterministic(self, stub):
        """Omit operation is deterministic."""
        inputs = {"data": {"a": 1, "b": 2, "c": 3}, "operation": "omit", "keys": ["b"]}

        result1 = await stub.execute(inputs)
        result2 = await stub.execute(inputs)

        assert result1["output"] == result2["output"]
        assert result1["output"] == {"a": 1, "c": 3}

    @pytest.mark.asyncio
    async def test_filter_deterministic(self, stub):
        """Filter operation is deterministic."""
        inputs = {
            "data": [
                {"name": "Alice", "active": True},
                {"name": "Bob", "active": False},
                {"name": "Charlie", "active": True},
            ],
            "operation": "filter",
            "condition": {"active": True},
        }

        result1 = await stub.execute(inputs)
        result2 = await stub.execute(inputs)

        assert result1["output"] == result2["output"]
        assert len(result1["output"]) == 2

    @pytest.mark.asyncio
    async def test_merge_deterministic(self, stub):
        """Merge operation is deterministic."""
        inputs = {"data": {"a": 1, "b": 2}, "operation": "merge", "with": {"c": 3, "d": 4}}

        result1 = await stub.execute(inputs)
        result2 = await stub.execute(inputs)

        assert result1["output"] == result2["output"]
        assert result1["output"] == {"a": 1, "b": 2, "c": 3, "d": 4}


class TestStubGoldenFileComparison:
    """Tests comparing stub outputs against golden files."""

    @pytest.mark.asyncio
    async def test_http_stub_matches_golden_structure(self):
        """HTTP stub output structure matches golden file."""
        golden = load_golden("stub_http_call")

        stub = HttpCallStub()
        stub.add_response(
            "api.example.com",
            {"status_code": 200, "body": "test response", "headers": {"content-type": "application/json"}},
        )

        result = await stub.execute(golden["input"])

        # Check structure matches
        assert "status_code" in result
        assert "body_hash" in result
        assert result["status_code"] == golden["expected_output"]["status_code"]

    @pytest.mark.asyncio
    async def test_llm_stub_matches_golden_structure(self):
        """LLM stub output structure matches golden file."""
        golden = load_golden("stub_llm_invoke")

        stub = LlmInvokeStub()
        result = await stub.execute(golden["input"])

        # Check structure matches
        assert "content" in result
        assert "model" in result
        assert "prompt_hash" in result
        assert "response_hash" in result
        assert result["model"] == golden["expected_output"]["model"]

    @pytest.mark.asyncio
    async def test_json_transform_stub_matches_golden_structure(self):
        """JSON transform stub output structure matches golden file."""
        golden = load_golden("stub_json_transform")

        stub = JsonTransformStub()
        result = await stub.execute(golden["input"])

        # Check structure matches
        assert "output" in result
        assert "output_hash" in result
        assert "transform_type" in result
        assert result["transform_type"] == golden["expected_output"]["transform_type"]

        # Check actual output value
        assert result["output"] == golden["expected_output"]["output"]


class TestStubReset:
    """Tests for stub reset functionality."""

    @pytest.mark.asyncio
    async def test_http_stub_reset_clears_history(self):
        """HTTP stub reset clears call history."""
        stub = HttpCallStub()
        await stub.execute({"url": "https://test.com"})

        assert len(stub.call_history) == 1
        stub.reset()
        assert len(stub.call_history) == 0

    @pytest.mark.asyncio
    async def test_llm_stub_reset_clears_history(self):
        """LLM stub reset clears call history."""
        stub = LlmInvokeStub()
        await stub.execute({"prompt": "test"})

        assert len(stub.call_history) == 1
        stub.reset()
        assert len(stub.call_history) == 0

    @pytest.mark.asyncio
    async def test_json_transform_stub_reset_clears_history(self):
        """JSON transform stub reset clears call history."""
        stub = JsonTransformStub()
        await stub.execute({"data": {"a": 1}, "operation": "extract", "path": "$.a"})

        assert len(stub.call_history) == 1
        stub.reset()
        assert len(stub.call_history) == 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
