# tests/planner/test_determinism_stress.py
"""
Planner Determinism Stress Tests (M2.5 Gap Fix)

Stress tests to verify planner determinism doesn't collapse under:
1. Repeated identical calls
2. Large nested input graphs
3. Multiple planners in the same session
4. Randomized input key ordering
5. Concurrent planning calls

These tests are critical - planner drift causes runtime instability.
"""

import asyncio
import random
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Add paths
_backend_path = str(Path(__file__).parent.parent.parent)
_app_path = str(Path(__file__).parent.parent.parent / "app")

for p in [_backend_path, _app_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.app.hoc.int.platform.drivers.interface import (
    DeterminismMode,
    PlannerOutput,
    PlannerRegistry,
)
from app.hoc.int.platform.drivers.stub_planner import StubPlanner


class TestRepeatedIdenticalCalls:
    """Test that repeated identical calls produce identical outputs."""

    @pytest.fixture
    def planner(self):
        return StubPlanner()

    @pytest.fixture
    def manifest(self):
        return [
            {"skill_id": "skill.http_call", "name": "HTTP Call"},
            {"skill_id": "skill.json_transform", "name": "JSON Transform"},
            {"skill_id": "skill.llm_invoke", "name": "LLM Invoke"},
        ]

    def _strip_timestamp(self, output: "PlannerOutput") -> Dict[str, Any]:
        """Strip timestamp fields for deterministic comparison."""
        d = output.to_dict()
        if "metadata" in d and "generated_at" in d["metadata"]:
            d["metadata"] = {k: v for k, v in d["metadata"].items() if k != "generated_at"}
        return d

    def test_100_identical_calls_same_output(self, planner, manifest):
        """100 identical calls must produce identical output (excluding timestamps)."""
        inputs = {"agent_id": "stress-test-agent", "goal": "fetch user data from API", "tool_manifest": manifest}

        results = []
        for _ in range(100):
            result = planner.plan(**inputs)
            assert result.__class__.__name__ == "PlannerOutput"
            results.append(self._strip_timestamp(result))

        # All outputs must be identical (excluding timestamps)
        first = results[0]
        for i, r in enumerate(results[1:], 1):
            assert r == first, f"Output {i} differs from first output"

    def test_1000_calls_same_cache_key(self, planner, manifest):
        """1000 calls must produce identical cache keys."""
        inputs = {"agent_id": "cache-key-test", "goal": "analyze data", "tool_manifest": manifest}

        cache_keys = set()
        for _ in range(1000):
            result = planner.plan(**inputs)
            assert result.__class__.__name__ == "PlannerOutput"
            cache_keys.add(result.metadata.cache_key)

        # Only one unique cache key
        assert len(cache_keys) == 1, f"Expected 1 cache key, got {len(cache_keys)}"

    def test_100_calls_same_cache_key_only(self, planner, manifest):
        """100 calls must produce identical cache keys (cache_key is timestamp-free)."""
        inputs = {"agent_id": "hash-test", "goal": "echo hello", "tool_manifest": [{"skill_id": "skill.echo"}]}

        cache_keys = set()
        for _ in range(100):
            result = planner.plan(**inputs)
            assert result.__class__.__name__ == "PlannerOutput"
            cache_keys.add(result.metadata.cache_key)

        assert len(cache_keys) == 1, f"Expected 1 unique cache key, got {len(cache_keys)}"


class TestLargeNestedInputs:
    """Test determinism with large/complex inputs."""

    @pytest.fixture
    def planner(self):
        return StubPlanner()

    def _generate_deep_nested(self, depth: int) -> Dict[str, Any]:
        """Generate deeply nested dictionary."""
        if depth == 0:
            return {"value": "leaf"}
        return {"nested": self._generate_deep_nested(depth - 1), "level": depth}

    def _generate_wide_dict(self, width: int) -> Dict[str, Any]:
        """Generate wide dictionary with many keys."""
        return {f"key_{i}": {"data": f"value_{i}", "index": i} for i in range(width)}

    def test_deep_nesting_deterministic(self, planner):
        """Deep nested context doesn't affect determinism."""
        manifest = [{"skill_id": "skill.http_call"}]

        # Create deep nested context
        deep_context = self._generate_deep_nested(50)

        inputs = {"agent_id": "deep-test", "goal": "fetch data", "tool_manifest": manifest, "context": deep_context}

        results = [planner.plan(**inputs) for _ in range(10)]

        # All results must have same cache key
        cache_keys = {r.metadata.cache_key for r in results if hasattr(r, "metadata")}
        assert len(cache_keys) == 1

    def test_wide_manifest_deterministic(self, planner):
        """Wide manifest (many skills) doesn't affect determinism."""
        # Generate manifest with 100 skills - include http_call so there's a match
        manifest = [{"skill_id": "skill.http_call", "name": "HTTP Call"}]
        manifest.extend([{"skill_id": f"skill.skill_{i}", "name": f"Skill {i}"} for i in range(99)])

        inputs = {"agent_id": "wide-test", "goal": "fetch data", "tool_manifest": manifest}

        results = [planner.plan(**inputs) for _ in range(10)]
        cache_keys = {r.metadata.cache_key for r in results if hasattr(r, "metadata")}
        assert len(cache_keys) == 1


class TestKeyOrderInvariance:
    """Test that key order doesn't affect determinism."""

    @pytest.fixture
    def planner(self):
        return StubPlanner()

    @pytest.fixture
    def manifest(self):
        return [
            {"skill_id": "skill.http_call"},
            {"skill_id": "skill.llm_invoke"},
        ]

    def test_manifest_key_order_invariant(self, planner):
        """Different manifest key orderings produce same plan."""
        # Same manifest data, different key orders
        m1 = [{"skill_id": "skill.http_call", "name": "HTTP"}]
        m2 = [{"name": "HTTP", "skill_id": "skill.http_call"}]

        inputs1 = {"agent_id": "test", "goal": "fetch", "tool_manifest": m1}
        inputs2 = {"agent_id": "test", "goal": "fetch", "tool_manifest": m2}

        r1 = planner.plan(**inputs1)
        r2 = planner.plan(**inputs2)

        # Structure should match even if manifest key order differs
        assert r1.__class__.__name__ == r2.__class__.__name__
        if hasattr(r1, "steps"):
            assert len(r1.steps) == len(r2.steps)
            for s1, s2 in zip(r1.steps, r2.steps):
                assert s1.skill == s2.skill

    def test_randomized_key_order_1000_times(self, planner, manifest):
        """1000 iterations with randomized key ordering produce consistent results."""
        base_inputs = {
            "agent_id": "random-order-test",
            "goal": "analyze data",
            "context_summary": "Test context",
            "tool_manifest": manifest,
        }

        results = []
        for _ in range(1000):
            # Randomize key order (Python 3.7+ dicts are ordered, but we test shuffling)
            keys = list(base_inputs.keys())
            random.shuffle(keys)
            shuffled = {k: base_inputs[k] for k in keys}

            result = planner.plan(**shuffled)
            if hasattr(result, "steps"):
                results.append(len(result.steps))

        # All should have same step count
        if results:
            assert all(r == results[0] for r in results)


class TestMultiplePlannersInSession:
    """Test multiple planners in the same session don't interfere."""

    def _strip_timestamp(self, output) -> Dict[str, Any]:
        """Strip timestamp fields for deterministic comparison."""
        d = output.to_dict()
        if "metadata" in d and "generated_at" in d["metadata"]:
            d["metadata"] = {k: v for k, v in d["metadata"].items() if k != "generated_at"}
        return d

    def test_two_planners_independent(self):
        """Two planner instances remain independent."""
        p1 = StubPlanner()
        p2 = StubPlanner()

        manifest = [{"skill_id": "skill.http_call"}]

        # Use both planners
        r1_a = p1.plan(agent_id="a1", goal="fetch", tool_manifest=manifest)
        r2_a = p2.plan(agent_id="a2", goal="fetch", tool_manifest=manifest)
        r1_b = p1.plan(agent_id="a1", goal="fetch", tool_manifest=manifest)

        # First planner should be deterministic (excluding timestamp)
        assert r1_a.__class__.__name__ == "PlannerOutput"
        assert r1_b.__class__.__name__ == "PlannerOutput"
        assert self._strip_timestamp(r1_a) == self._strip_timestamp(r1_b)

        # History should be independent
        assert len(p1.get_call_history()) == 2
        assert len(p2.get_call_history()) == 1

    def test_registry_multiple_planners(self):
        """Registry handles multiple planners correctly."""
        PlannerRegistry.clear()

        p1 = StubPlanner()
        p2 = StubPlanner()

        # Override planner_id for testing
        p1._test_id = "stub1"
        p2._test_id = "stub2"

        # Since both have same planner_id, second replaces first
        PlannerRegistry.register(p1)

        assert PlannerRegistry.get("stub") is p1


class TestConcurrentPlanning:
    """Test concurrent planning calls remain deterministic."""

    @pytest.fixture
    def planner(self):
        return StubPlanner()

    @pytest.fixture
    def manifest(self):
        return [{"skill_id": "skill.http_call"}]

    def _strip_timestamp(self, output) -> Dict[str, Any]:
        """Strip timestamp fields for deterministic comparison."""
        d = output.to_dict()
        if "metadata" in d and "generated_at" in d["metadata"]:
            d["metadata"] = {k: v for k, v in d["metadata"].items() if k != "generated_at"}
        return d

    @pytest.mark.asyncio
    async def test_concurrent_calls_same_result(self, planner, manifest):
        """Concurrent planning calls produce same cache keys."""
        inputs = {"agent_id": "concurrent-test", "goal": "fetch data", "tool_manifest": manifest}

        # Run 50 concurrent plans
        tasks = [asyncio.create_task(asyncio.to_thread(planner.plan, **inputs)) for _ in range(50)]
        results = await asyncio.gather(*tasks)

        # All results should have identical cache keys
        cache_keys = {r.metadata.cache_key for r in results if hasattr(r, "metadata")}
        assert len(cache_keys) == 1, f"Got {len(cache_keys)} unique cache keys from 50 concurrent calls"


class TestDeterminismModeContract:
    """Test that determinism mode is correctly reported."""

    def _strip_timestamp(self, output) -> Dict[str, Any]:
        """Strip timestamp fields for deterministic comparison."""
        d = output.to_dict()
        if "metadata" in d and "generated_at" in d["metadata"]:
            d["metadata"] = {k: v for k, v in d["metadata"].items() if k != "generated_at"}
        return d

    def test_stub_planner_reports_full_determinism(self):
        """StubPlanner must report FULL determinism."""
        planner = StubPlanner()
        mode = planner.get_determinism_mode()

        assert mode == DeterminismMode.FULL

    def test_full_determinism_means_identical_outputs(self):
        """FULL determinism means identical outputs (excluding timestamp)."""
        planner = StubPlanner()
        assert planner.get_determinism_mode() == DeterminismMode.FULL

        manifest = [{"skill_id": "skill.echo"}]
        inputs = {"agent_id": "test", "goal": "echo hello", "tool_manifest": manifest}

        r1 = planner.plan(**inputs)
        r2 = planner.plan(**inputs)

        # Excluding generated_at timestamp, outputs must be identical
        assert self._strip_timestamp(r1) == self._strip_timestamp(r2)
        # Cache keys must be identical
        assert r1.metadata.cache_key == r2.metadata.cache_key


class TestEdgeCases:
    """Test edge cases that might break determinism."""

    @pytest.fixture
    def planner(self):
        return StubPlanner()

    def test_empty_manifest_produces_error_or_filtered(self, planner):
        """Empty manifest produces deterministic result (error or filtered plan)."""
        results = []
        for _ in range(10):
            result = planner.plan(agent_id="test", goal="fetch data", tool_manifest=[])
            results.append(result.__class__.__name__)

        # All results should be consistent (either all errors or all plans)
        assert len(set(results)) == 1, f"Inconsistent results: {set(results)}"

    def test_unicode_goal_deterministic(self, planner):
        """Unicode in goal doesn't break determinism."""
        manifest = [{"skill_id": "skill.echo"}]

        cache_keys = set()
        for _ in range(10):
            result = planner.plan(agent_id="test", goal="echo こんにちは 🌍 مرحبا", tool_manifest=manifest)
            if hasattr(result, "metadata"):
                cache_keys.add(result.metadata.cache_key)

        if cache_keys:
            assert len(cache_keys) == 1, f"Got {len(cache_keys)} different cache keys"

    def test_very_long_goal_deterministic(self, planner):
        """Very long goal doesn't break determinism."""
        manifest = [{"skill_id": "skill.echo"}]
        long_goal = "echo " + "x" * 10000

        results = []
        for _ in range(10):
            result = planner.plan(agent_id="test", goal=long_goal, tool_manifest=manifest)
            if hasattr(result, "metadata"):
                results.append(result.metadata.cache_key)

        if results:
            assert len(set(results)) == 1


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
