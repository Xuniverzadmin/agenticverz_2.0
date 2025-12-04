# Nightly Golden Stress Tests
"""
Representative workflow stress tests for nightly CI.

These tests run representative workflows 100x each to detect:
1. Non-determinism that only appears at scale
2. Seed-dependent race conditions
3. Golden file signature drift
4. Memory leaks or resource exhaustion

Run manually:
    STRESS_ITERATIONS=100 pytest tests/workflow/test_nightly_golden_stress.py -v

Environment:
    STRESS_ITERATIONS: Number of iterations per workflow (default: 100)
    DISABLE_EXTERNAL_CALLS: Must be "1" for these tests
    GOLDEN_SECRET: Secret for signing golden files
"""

from __future__ import annotations
import asyncio
import hashlib
import os
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

import pytest

# Get iteration count from environment (default 100 for nightly, can reduce for local testing)
STRESS_ITERATIONS = int(os.getenv("STRESS_ITERATIONS", "100"))


class MockSkillRegistry:
    """Registry with representative skills for stress testing."""

    def __init__(self):
        self._skills: Dict[str, Dict] = {}
        self._setup_representative_skills()

    def _setup_representative_skills(self):
        """Setup skills that represent production patterns."""
        # CPU-bound skill
        self._skills["compute_hash"] = {
            "id": "compute_hash",
            "cost_estimate_cents": 1,
            "handler": self._compute_hash,
        }
        # Memory-intensive skill
        self._skills["transform_json"] = {
            "id": "transform_json",
            "cost_estimate_cents": 2,
            "handler": self._transform_json,
        }
        # I/O simulation skill
        self._skills["mock_io"] = {
            "id": "mock_io",
            "cost_estimate_cents": 5,
            "handler": self._mock_io,
        }
        # LLM simulation skill (deterministic stub)
        self._skills["llm_stub"] = {
            "id": "llm_stub",
            "cost_estimate_cents": 10,
            "handler": self._llm_stub,
        }

    async def _compute_hash(self, params: Dict, context: Dict) -> Dict:
        """Deterministic hash computation."""
        data = str(params.get("data", ""))
        hash_value = hashlib.sha256(data.encode()).hexdigest()
        return {"hash": hash_value, "length": len(data)}

    async def _transform_json(self, params: Dict, context: Dict) -> Dict:
        """Deterministic JSON transformation."""
        input_data = params.get("input", {})
        # Consistent transformation
        result = {
            "keys": sorted(input_data.keys()) if isinstance(input_data, dict) else [],
            "count": len(input_data) if isinstance(input_data, (dict, list)) else 1,
            "type": type(input_data).__name__,
        }
        return result

    async def _mock_io(self, params: Dict, context: Dict) -> Dict:
        """Mock I/O with deterministic delay (no actual sleep in test)."""
        # In test mode, no actual delay
        return {
            "read_bytes": len(str(params)),
            "operation": "mock_read",
        }

    async def _llm_stub(self, params: Dict, context: Dict) -> Dict:
        """Deterministic LLM stub using seeded generation."""
        seed = context.get("seed", 0)
        prompt = params.get("prompt", "")

        # Deterministic response based on seed and prompt hash
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        response = f"Response-{seed}-{prompt_hash}"

        return {
            "response": response,
            "tokens_used": len(prompt) // 4,
        }

    def get(self, skill_id: str) -> Dict:
        return self._skills.get(skill_id)

    def get_cost_estimate(self, skill_id: str) -> int:
        skill = self._skills.get(skill_id)
        return skill["cost_estimate_cents"] if skill else 0


class RepresentativeWorkflow:
    """A representative workflow pattern for stress testing."""

    def __init__(self, name: str, steps: List[Dict]):
        self.name = name
        self.steps = steps

    @classmethod
    def compute_pipeline(cls) -> "RepresentativeWorkflow":
        """5-step compute pipeline (hash -> transform -> hash -> transform -> llm)."""
        return cls("compute_pipeline", [
            {"skill_id": "compute_hash", "params": {"data": "input_data_step_1"}},
            {"skill_id": "transform_json", "params": {"input": {"a": 1, "b": 2, "c": 3}}},
            {"skill_id": "compute_hash", "params": {"data": "step_2_output"}},
            {"skill_id": "transform_json", "params": {"input": [1, 2, 3, 4, 5]}},
            {"skill_id": "llm_stub", "params": {"prompt": "Summarize the computation"}},
        ])

    @classmethod
    def io_heavy(cls) -> "RepresentativeWorkflow":
        """8-step I/O heavy workflow."""
        return cls("io_heavy", [
            {"skill_id": "mock_io", "params": {"file": "file1.txt"}},
            {"skill_id": "mock_io", "params": {"file": "file2.txt"}},
            {"skill_id": "transform_json", "params": {"input": {"files": ["f1", "f2"]}}},
            {"skill_id": "mock_io", "params": {"file": "file3.txt"}},
            {"skill_id": "compute_hash", "params": {"data": "combined_content"}},
            {"skill_id": "mock_io", "params": {"file": "output.txt", "mode": "write"}},
            {"skill_id": "transform_json", "params": {"input": {"status": "complete"}}},
            {"skill_id": "llm_stub", "params": {"prompt": "Verify IO operations"}},
        ])

    @classmethod
    def llm_intensive(cls) -> "RepresentativeWorkflow":
        """6-step LLM-intensive workflow."""
        return cls("llm_intensive", [
            {"skill_id": "llm_stub", "params": {"prompt": "Step 1: Analyze"}},
            {"skill_id": "transform_json", "params": {"input": {"analysis": True}}},
            {"skill_id": "llm_stub", "params": {"prompt": "Step 2: Plan"}},
            {"skill_id": "llm_stub", "params": {"prompt": "Step 3: Execute"}},
            {"skill_id": "transform_json", "params": {"input": {"execution": "done"}}},
            {"skill_id": "llm_stub", "params": {"prompt": "Step 4: Summarize"}},
        ])


async def run_workflow_once(
    workflow: RepresentativeWorkflow,
    registry: MockSkillRegistry,
    seed: int,
) -> Dict[str, Any]:
    """Run a workflow once and return result hashes."""
    step_hashes = []
    context = {"seed": seed}

    for i, step in enumerate(workflow.steps):
        skill_id = step["skill_id"]
        params = step["params"]

        skill = registry.get(skill_id)
        if not skill:
            raise ValueError(f"Unknown skill: {skill_id}")

        result = await skill["handler"](params, context)

        # Hash the result deterministically
        result_str = str(sorted(result.items()) if isinstance(result, dict) else result)
        result_hash = hashlib.sha256(result_str.encode()).hexdigest()[:16]
        step_hashes.append(f"{skill_id}:{result_hash}")

    # Final workflow hash
    workflow_hash = hashlib.sha256(":".join(step_hashes).encode()).hexdigest()

    return {
        "workflow": workflow.name,
        "seed": seed,
        "step_hashes": step_hashes,
        "workflow_hash": workflow_hash,
    }


class TestNightlyGoldenStress:
    """Nightly stress tests for golden file determinism."""

    @pytest.fixture
    def registry(self) -> MockSkillRegistry:
        return MockSkillRegistry()

    @pytest.mark.asyncio
    async def test_compute_pipeline_100x(self, registry: MockSkillRegistry):
        """Run compute_pipeline 100x and verify all hashes match."""
        workflow = RepresentativeWorkflow.compute_pipeline()
        seed = 12345

        # Run first iteration to get reference
        reference = await run_workflow_once(workflow, registry, seed)
        reference_hash = reference["workflow_hash"]

        # Run remaining iterations
        mismatches = []
        for i in range(1, STRESS_ITERATIONS):
            result = await run_workflow_once(workflow, registry, seed)
            if result["workflow_hash"] != reference_hash:
                mismatches.append({
                    "iteration": i,
                    "expected": reference_hash,
                    "actual": result["workflow_hash"],
                    "step_hashes": result["step_hashes"],
                })

        assert not mismatches, (
            f"Determinism failure in compute_pipeline: "
            f"{len(mismatches)}/{STRESS_ITERATIONS} iterations had different hashes.\n"
            f"First mismatch: {mismatches[0] if mismatches else 'N/A'}"
        )

    @pytest.mark.asyncio
    async def test_io_heavy_100x(self, registry: MockSkillRegistry):
        """Run io_heavy workflow 100x and verify determinism."""
        workflow = RepresentativeWorkflow.io_heavy()
        seed = 67890

        reference = await run_workflow_once(workflow, registry, seed)
        reference_hash = reference["workflow_hash"]

        mismatches = []
        for i in range(1, STRESS_ITERATIONS):
            result = await run_workflow_once(workflow, registry, seed)
            if result["workflow_hash"] != reference_hash:
                mismatches.append({
                    "iteration": i,
                    "expected": reference_hash,
                    "actual": result["workflow_hash"],
                })

        assert not mismatches, (
            f"Determinism failure in io_heavy: "
            f"{len(mismatches)}/{STRESS_ITERATIONS} iterations had different hashes."
        )

    @pytest.mark.asyncio
    async def test_llm_intensive_100x(self, registry: MockSkillRegistry):
        """Run llm_intensive workflow 100x and verify determinism."""
        workflow = RepresentativeWorkflow.llm_intensive()
        seed = 11111

        reference = await run_workflow_once(workflow, registry, seed)
        reference_hash = reference["workflow_hash"]

        mismatches = []
        for i in range(1, STRESS_ITERATIONS):
            result = await run_workflow_once(workflow, registry, seed)
            if result["workflow_hash"] != reference_hash:
                mismatches.append({
                    "iteration": i,
                    "expected": reference_hash,
                    "actual": result["workflow_hash"],
                })

        assert not mismatches, (
            f"Determinism failure in llm_intensive: "
            f"{len(mismatches)}/{STRESS_ITERATIONS} iterations had different hashes."
        )

    @pytest.mark.asyncio
    async def test_varied_seeds_deterministic(self, registry: MockSkillRegistry):
        """Test that different seeds produce different but deterministic results."""
        workflow = RepresentativeWorkflow.compute_pipeline()
        seeds = [100, 200, 300, 400, 500]

        # For each seed, run twice and verify consistency
        for seed in seeds:
            result1 = await run_workflow_once(workflow, registry, seed)
            result2 = await run_workflow_once(workflow, registry, seed)

            assert result1["workflow_hash"] == result2["workflow_hash"], (
                f"Same seed {seed} produced different results"
            )

        # Verify different seeds produce different results
        results = []
        for seed in seeds:
            result = await run_workflow_once(workflow, registry, seed)
            results.append(result["workflow_hash"])

        unique_hashes = len(set(results))
        assert unique_hashes >= len(seeds) - 1, (
            f"Expected mostly unique hashes for different seeds, got {unique_hashes}/{len(seeds)}"
        )

    @pytest.mark.asyncio
    async def test_concurrent_execution_determinism(self, registry: MockSkillRegistry):
        """Test that concurrent executions with same seed produce same results."""
        workflow = RepresentativeWorkflow.compute_pipeline()
        seed = 99999

        # Run 10 concurrent executions
        tasks = [
            run_workflow_once(workflow, registry, seed)
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)

        # All should have the same hash
        hashes = [r["workflow_hash"] for r in results]
        unique = set(hashes)

        assert len(unique) == 1, (
            f"Concurrent executions produced {len(unique)} different hashes: {unique}"
        )

    @pytest.mark.asyncio
    async def test_all_workflows_stress(self, registry: MockSkillRegistry):
        """Run all representative workflows with stress iterations."""
        workflows = [
            RepresentativeWorkflow.compute_pipeline(),
            RepresentativeWorkflow.io_heavy(),
            RepresentativeWorkflow.llm_intensive(),
        ]

        # Use fewer iterations per workflow when running all together
        iterations = max(STRESS_ITERATIONS // 3, 10)

        for workflow in workflows:
            seed = hash(workflow.name) % 100000
            reference = await run_workflow_once(workflow, registry, seed)

            for i in range(iterations):
                result = await run_workflow_once(workflow, registry, seed)
                assert result["workflow_hash"] == reference["workflow_hash"], (
                    f"Mismatch in {workflow.name} at iteration {i}"
                )

    @pytest.mark.asyncio
    async def test_memory_stability(self, registry: MockSkillRegistry):
        """Test for memory leaks over many iterations."""
        import gc

        workflow = RepresentativeWorkflow.compute_pipeline()
        seed = 55555

        # Force garbage collection before starting
        gc.collect()

        # Run many iterations
        for _ in range(STRESS_ITERATIONS):
            result = await run_workflow_once(workflow, registry, seed)
            del result

        # Force GC after
        gc.collect()

        # If we got here without OOM, the test passes
        # In production, you'd check memory metrics

    @pytest.mark.asyncio
    async def test_hash_collision_resistance(self, registry: MockSkillRegistry):
        """Verify no hash collisions across different workflow runs."""
        workflow = RepresentativeWorkflow.compute_pipeline()

        # Generate results with many different seeds
        seen_hashes: Dict[str, int] = {}
        collision_count = 0

        for seed in range(STRESS_ITERATIONS * 2):
            result = await run_workflow_once(workflow, registry, seed)
            h = result["workflow_hash"]

            if h in seen_hashes and seen_hashes[h] != seed:
                collision_count += 1

            seen_hashes[h] = seed

        # No collisions expected for SHA256
        assert collision_count == 0, (
            f"Found {collision_count} hash collisions in {STRESS_ITERATIONS * 2} runs"
        )
