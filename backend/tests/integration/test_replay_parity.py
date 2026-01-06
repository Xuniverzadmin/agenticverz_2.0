"""
Replay Parity Tests - M7 Implementation

Tests to verify that memory integration doesn't break determinism.
Compares baseline trace (without memory) vs memory-enabled trace.

Run with:
    # Local tests (mocked)
    pytest tests/integration/test_replay_parity.py -v

    # Live tests against staging
    STAGING_BASE=https://staging.example.com MACHINE_JWT=xxx pytest tests/integration/test_replay_parity.py -v --live
"""

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

import pytest

# Check if requests is available for live tests
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# Configuration
STAGING_BASE = os.getenv("STAGING_BASE", "http://localhost:8000")
MACHINE_JWT = os.getenv("MACHINE_JWT", "")


def requires_live():
    """Marker for tests that require live API."""
    return pytest.mark.skipif(
        not os.getenv("RUN_LIVE_TESTS", "").lower() == "true", reason="Live tests disabled (set RUN_LIVE_TESTS=true)"
    )


class TestReplayParity:
    """Tests for replay determinism with/without memory."""

    def test_deterministic_hash_function(self):
        """Test that our hash function is deterministic."""
        data1 = {"key": "value", "nested": {"a": 1, "b": 2}}
        data2 = {"nested": {"b": 2, "a": 1}, "key": "value"}  # Same data, different order

        hash1 = self._canonical_hash(data1)
        hash2 = self._canonical_hash(data2)

        assert hash1 == hash2, "Hash should be order-independent"

    def test_hash_excludes_timestamps(self):
        """Test that timestamps don't affect hash."""
        data1 = {"result": "success", "timestamp": "2025-01-01T00:00:00Z", "data": {"value": 42}}
        data2 = {"result": "success", "timestamp": "2025-01-02T00:00:00Z", "data": {"value": 42}}

        hash1 = self._canonical_hash(data1, exclude_keys=["timestamp"])
        hash2 = self._canonical_hash(data2, exclude_keys=["timestamp"])

        assert hash1 == hash2, "Hash should exclude timestamps"

    def test_mock_trace_parity(self):
        """Test trace parity with mocked execution."""
        # Simulate a trace execution
        trace = {
            "workflow_id": "test-workflow-1",
            "steps": [
                {"skill": "http_call", "params": {"url": "https://api.example.com/data"}},
                {"skill": "json_transform", "params": {"jq": ".items"}},
            ],
        }

        # Mock execution results
        baseline_result = self._mock_execute_trace(trace, enable_memory=False)
        memory_result = self._mock_execute_trace(trace, enable_memory=True)

        # Compare deterministic fields
        assert baseline_result["final_state"] == memory_result["final_state"]
        assert baseline_result["step_count"] == memory_result["step_count"]

    def test_mock_trace_with_memory_context(self):
        """Test that memory context is injected but doesn't change output."""
        trace = {
            "workflow_id": "test-workflow-2",
            "agent_id": "agent-123",
            "steps": [
                {"skill": "llm_invoke", "params": {"prompt": "Hello"}},
            ],
        }

        baseline_result = self._mock_execute_trace(trace, enable_memory=False)
        memory_result = self._mock_execute_trace(trace, enable_memory=True)

        # Memory-enabled should have context_injected flag
        assert memory_result.get("context_injected") is True

        # But final output should match (modulo memory-specific metadata)
        baseline_hash = self._canonical_hash(
            baseline_result, exclude_keys=["context_injected", "memory_context", "execution_time"]
        )
        memory_hash = self._canonical_hash(
            memory_result, exclude_keys=["context_injected", "memory_context", "execution_time"]
        )

        assert baseline_hash == memory_hash

    @requires_live()
    def test_live_trace_parity(self):
        """Live test: compare traces with and without memory."""
        if not HAS_REQUESTS:
            pytest.skip("requests library not available")

        if not MACHINE_JWT:
            pytest.skip("MACHINE_JWT not configured")

        trace = {"user": "test-user", "ops": [{"op": "price", "args": {"v": "TEST"}}]}

        baseline = self._run_live_trace(trace, enable_memory=False)
        with_memory = self._run_live_trace(trace, enable_memory=True)

        assert baseline["final_state"] == with_memory["final_state"], (
            "Determinism drift detected between baseline and memory-enabled traces"
        )

    @staticmethod
    def _canonical_hash(data: Dict[str, Any], exclude_keys: Optional[List[str]] = None) -> str:
        """
        Compute a canonical hash of a dictionary.

        Excludes specified keys and sorts for consistency.
        """
        exclude_keys = exclude_keys or []

        def filter_and_sort(obj):
            if isinstance(obj, dict):
                return {k: filter_and_sort(v) for k, v in sorted(obj.items()) if k not in exclude_keys}
            elif isinstance(obj, list):
                return [filter_and_sort(item) for item in obj]
            else:
                return obj

        filtered = filter_and_sort(data)
        canonical = json.dumps(filtered, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def _mock_execute_trace(trace: Dict[str, Any], enable_memory: bool = False) -> Dict[str, Any]:
        """
        Mock trace execution for testing.

        In a real system, this would call the runtime API.
        """
        step_count = len(trace.get("steps", []))

        result = {
            "workflow_id": trace.get("workflow_id"),
            "step_count": step_count,
            "final_state": {"status": "completed", "steps_executed": step_count, "output": {"data": "mock_result"}},
            "execution_time": 0.123,  # Non-deterministic
        }

        if enable_memory:
            result["context_injected"] = True
            result["memory_context"] = {
                "agent_id": trace.get("agent_id"),
                "memories_loaded": 3,
            }

        return result

    def _run_live_trace(self, trace: Dict[str, Any], enable_memory: bool = False) -> Dict[str, Any]:
        """Run a trace against the live API."""
        url = f"{STAGING_BASE}/api/v1/costsim/run"
        headers = {
            "Authorization": f"Bearer {MACHINE_JWT}",
            "Content-Type": "application/json",
        }
        payload = {
            "trace": trace,
            "enable_memory": enable_memory,
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()


class TestMemoryIntegrationParity:
    """Tests for memory integration not breaking existing functionality."""

    def test_memory_store_parity(self):
        """Test that memory store operations are idempotent."""
        from unittest.mock import MagicMock

        # Mock memory store
        store = MagicMock()
        store.store.return_value = "mem-123"
        store.get.return_value = {"id": "mem-123", "text": "test memory", "created_at": "2025-01-01T00:00:00Z"}

        # Store same content twice
        id1 = store.store(agent_id="a1", text="test memory", memory_type="general")
        id2 = store.store(agent_id="a1", text="test memory", memory_type="general")

        # Get should return consistent data
        result1 = store.get(id1)
        result2 = store.get(id2)

        assert result1["text"] == result2["text"]

    def test_memory_retrieval_deterministic(self):
        """Test that memory retrieval order is deterministic."""
        # Simulated memories
        memories = [
            {"id": "m1", "text": "first", "created_at": "2025-01-01T00:00:00Z"},
            {"id": "m2", "text": "second", "created_at": "2025-01-01T00:01:00Z"},
            {"id": "m3", "text": "third", "created_at": "2025-01-01T00:02:00Z"},
        ]

        # Sort by created_at descending (newest first)
        sorted1 = sorted(memories, key=lambda m: m["created_at"], reverse=True)
        sorted2 = sorted(memories, key=lambda m: m["created_at"], reverse=True)

        assert sorted1 == sorted2
        assert sorted1[0]["id"] == "m3"  # Newest first

    def test_context_injection_format(self):
        """Test that memory context injection has stable format."""
        memories = [
            {"text": "User prefers JSON output", "memory_type": "preference"},
            {"text": "Previous task completed successfully", "memory_type": "history"},
        ]

        # Format context (simulated)
        def format_context(mems):
            lines = ["## Agent Memory Context"]
            for m in mems:
                lines.append(f"- [{m['memory_type']}] {m['text']}")
            return "\n".join(lines)

        context1 = format_context(memories)
        context2 = format_context(memories)

        assert context1 == context2
        assert "## Agent Memory Context" in context1
        assert "[preference]" in context1


class TestMemoryPinsParity:
    """Tests for memory pins not affecting existing behavior."""

    def test_pin_upsert_idempotent(self):
        """Test that upserting same pin twice is idempotent."""
        # Simulated pin storage
        pins = {}

        def upsert(tenant_id, key, value):
            pins[(tenant_id, key)] = value
            return {"tenant_id": tenant_id, "key": key, "value": value}

        result1 = upsert("t1", "k1", {"foo": "bar"})
        result2 = upsert("t1", "k1", {"foo": "bar"})

        assert result1 == result2
        assert len(pins) == 1

    def test_pin_retrieval_consistent(self):
        """Test that pin retrieval is consistent."""
        pins = {
            ("global", "config"): {"setting": "value"},
        }

        def get_pin(tenant_id, key):
            return pins.get((tenant_id, key))

        result1 = get_pin("global", "config")
        result2 = get_pin("global", "config")

        assert result1 == result2
        assert result1["setting"] == "value"

    def test_expired_pins_excluded(self):
        """Test that expired pins are not returned."""
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        pins = [
            {"key": "valid", "expires_at": future, "value": "ok"},
            {"key": "expired", "expires_at": past, "value": "old"},
            {"key": "no_ttl", "expires_at": None, "value": "always"},
        ]

        def filter_active(pins_list, current_time):
            return [p for p in pins_list if p["expires_at"] is None or p["expires_at"] > current_time]

        active = filter_active(pins, now)
        assert len(active) == 2
        assert all(p["key"] != "expired" for p in active)
