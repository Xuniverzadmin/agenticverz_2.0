# M4-T4: Lifecycle Kill/Resume Tests
"""
Tests for workflow checkpoint resume behavior.

The WorkflowEngine uses structured outcomes (never throws) so these tests verify:
1. Checkpoint state after step failures
2. Resume from checkpoint continues correctly
3. Step outputs are preserved across resume
4. Version consistency after resume

Note: Engine converts exceptions to StepResult.from_error with failed status.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

os.environ.setdefault("DISABLE_EXTERNAL_CALLS", "1")


class TestCheckpointStore:
    """In-memory checkpoint store for lifecycle testing."""

    def __init__(self):
        self._store: Dict[str, Dict] = {}
        self._save_count = 0
        self._load_count = 0

    async def save(
        self,
        run_id: str,
        next_step_index: int,
        last_result_hash: Optional[str] = None,
        step_outputs: Optional[Dict[str, Any]] = None,
        status: str = "running",
        workflow_id: str = "",
        tenant_id: str = "",
        expected_version: Optional[int] = None,
        **kwargs,
    ) -> str:
        self._save_count += 1

        existing = self._store.get(run_id)
        if existing and expected_version is not None:
            if existing["version"] != expected_version:
                from app.workflow.checkpoint import CheckpointVersionConflictError

                raise CheckpointVersionConflictError(run_id, expected_version, existing["version"])

        version = (existing["version"] + 1) if existing else 1
        now = datetime.now(timezone.utc)

        self._store[run_id] = {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "tenant_id": tenant_id,
            "next_step_index": next_step_index,
            "last_result_hash": last_result_hash,
            "step_outputs": step_outputs or {},
            "status": status,
            "version": version,
            "created_at": existing["created_at"] if existing else now,
            "updated_at": now,
        }

        return hashlib.sha256(f"{run_id}:{next_step_index}:{version}".encode()).hexdigest()[:16]

    async def save_with_retry(self, **kwargs) -> str:
        """Save with automatic retry on version conflict."""
        max_retries = kwargs.pop("max_retries", 3)
        for attempt in range(max_retries):
            try:
                current = await self.load(kwargs["run_id"])
                expected_version = current.version if current else None
                return await self.save(**kwargs, expected_version=expected_version)
            except Exception:
                if attempt == max_retries - 1:
                    raise
        raise RuntimeError("Save failed after retries")

    async def load(self, run_id: str):
        self._load_count += 1
        data = self._store.get(run_id)
        if not data:
            return None

        class CheckpointData:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)

        return CheckpointData(data)

    async def delete(self, run_id: str) -> bool:
        if run_id in self._store:
            del self._store[run_id]
            return True
        return False


class DeterministicSkillRegistry:
    """Registry with deterministic skills for lifecycle testing."""

    def __init__(self):
        self._skills: Dict[str, Any] = {}
        self._call_count = 0
        self._fail_at_call: Optional[int] = None
        self._setup_skills()

    def _setup_skills(self):
        """Setup deterministic skills."""
        for name in ["compute", "transform", "validate"]:
            self._skills[name] = self._make_skill(name)
        self._skills["flaky"] = self._make_flaky_skill()

    def _make_skill(self, name: str):
        async def handler(inputs: Dict, seed: int = 0, meta: Dict = None) -> Dict:
            input_hash = hashlib.sha256(str(sorted(inputs.items())).encode()).hexdigest()[:8]
            return {
                "ok": True,
                "skill": name,
                "input_hash": input_hash,
                "seed": seed,
                "result": f"{name}-{input_hash}-{seed}",
            }

        return MagicMock(invoke=AsyncMock(side_effect=handler))

    def _make_flaky_skill(self):
        """Skill that fails on configured call number."""

        async def handler(inputs: Dict, seed: int = 0, meta: Dict = None) -> Dict:
            self._call_count += 1

            if self._fail_at_call is not None and self._call_count == self._fail_at_call:
                return {
                    "ok": False,
                    "error": {"code": "STEP_FAILED", "message": "Simulated failure"},
                }

            return {
                "ok": True,
                "skill": "flaky",
                "call": self._call_count,
            }

        return MagicMock(invoke=AsyncMock(side_effect=handler))

    def set_fail_at_call(self, call_number: int):
        """Configure flaky skill to fail at specific call."""
        self._fail_at_call = call_number

    def clear_failure(self):
        """Clear failure configuration."""
        self._fail_at_call = None
        self._call_count = 0

    def get(self, skill_id: str) -> Optional[Any]:
        return self._skills.get(skill_id)


class TestCheckpointCreation:
    """Tests for checkpoint creation during workflow execution."""

    @pytest.mark.asyncio
    async def test_checkpoint_created_after_each_step(self):
        """Verify checkpoint is saved after each successful step."""
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec

        registry = DeterministicSkillRegistry()
        store = TestCheckpointStore()

        spec = WorkflowSpec(
            id="test-checkpoint-creation",
            name="Checkpoint Creation Test",
            steps=[
                StepDescriptor(id="step1", skill_id="compute", inputs={"data": "test1"}),
                StepDescriptor(id="step2", skill_id="transform", inputs={"data": "test2"}),
                StepDescriptor(id="step3", skill_id="validate", inputs={"data": "test3"}),
            ],
        )

        engine = WorkflowEngine(registry, store)
        run_id = f"test-{uuid4().hex[:8]}"

        result = await engine.run(spec, run_id, seed=12345)

        assert result.status == "completed"
        assert result.steps_completed == 3

        # Verify checkpoint exists and has correct state
        checkpoint = await store.load(run_id)
        assert checkpoint is not None
        assert checkpoint.next_step_index == 3
        assert checkpoint.status == "completed"
        assert len(checkpoint.step_outputs) == 3

    @pytest.mark.asyncio
    async def test_checkpoint_saved_on_failure(self):
        """Verify checkpoint is saved even when step fails."""
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec

        registry = DeterministicSkillRegistry()
        store = TestCheckpointStore()

        # Fail on second call to flaky skill
        registry.set_fail_at_call(1)

        spec = WorkflowSpec(
            id="test-checkpoint-failure",
            name="Checkpoint Failure Test",
            steps=[
                StepDescriptor(id="step1", skill_id="flaky", inputs={"data": "a"}),
                StepDescriptor(id="step2", skill_id="compute", inputs={"data": "b"}),
            ],
        )

        engine = WorkflowEngine(registry, store)
        run_id = f"fail-{uuid4().hex[:8]}"

        result = await engine.run(spec, run_id, seed=11111)

        assert result.status == "failed"

        # Checkpoint should still exist
        checkpoint = await store.load(run_id)
        assert checkpoint is not None
        assert checkpoint.status == "failed"


class TestCheckpointResume:
    """Tests for resuming from checkpoint."""

    @pytest.mark.asyncio
    async def test_resume_from_checkpoint(self):
        """Test that workflow resumes from checkpoint correctly."""
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec

        registry = DeterministicSkillRegistry()
        store = TestCheckpointStore()

        spec = WorkflowSpec(
            id="test-resume",
            name="Resume Test",
            steps=[
                StepDescriptor(id="step1", skill_id="compute", inputs={"x": 1}),
                StepDescriptor(id="step2", skill_id="transform", inputs={"x": 2}),
                StepDescriptor(id="step3", skill_id="validate", inputs={"x": 3}),
            ],
        )

        run_id = f"resume-{uuid4().hex[:8]}"

        # Pre-create checkpoint at step 2 (step 1 completed)
        await store.save(
            run_id=run_id,
            next_step_index=1,
            step_outputs={"step1": {"ok": True, "result": "step1-done"}},
            status="running",
            workflow_id=spec.id,
        )

        engine = WorkflowEngine(registry, store)
        result = await engine.run(spec, run_id, seed=22222)

        assert result.status == "completed"
        # Steps 2 and 3 should have run
        assert result.steps_completed >= 2

    @pytest.mark.asyncio
    async def test_step_outputs_preserved_across_resume(self):
        """Test that step outputs from before checkpoint are available."""
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec

        registry = DeterministicSkillRegistry()
        store = TestCheckpointStore()

        spec = WorkflowSpec(
            id="test-outputs",
            name="Outputs Test",
            steps=[
                StepDescriptor(id="producer", skill_id="compute", inputs={"val": "data"}),
                StepDescriptor(id="consumer", skill_id="transform", inputs={"ref": "${producer.result}"}),
            ],
        )

        run_id = f"outputs-{uuid4().hex[:8]}"

        # Pre-create checkpoint with producer output
        await store.save(
            run_id=run_id,
            next_step_index=1,
            step_outputs={"producer": {"ok": True, "result": "producer-output"}},
            status="running",
            workflow_id=spec.id,
        )

        engine = WorkflowEngine(registry, store)
        result = await engine.run(spec, run_id, seed=33333)

        assert result.status == "completed"

        # Consumer should have received producer's output
        final_checkpoint = await store.load(run_id)
        assert "producer" in final_checkpoint.step_outputs
        assert "consumer" in final_checkpoint.step_outputs


class TestVersionConsistency:
    """Tests for checkpoint version consistency."""

    @pytest.mark.asyncio
    async def test_version_increments_on_save(self):
        """Test that checkpoint version increments correctly."""
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec

        registry = DeterministicSkillRegistry()
        store = TestCheckpointStore()

        spec = WorkflowSpec(
            id="test-version",
            name="Version Test",
            steps=[
                StepDescriptor(id="s1", skill_id="compute", inputs={"a": 1}),
                StepDescriptor(id="s2", skill_id="compute", inputs={"b": 2}),
                StepDescriptor(id="s3", skill_id="compute", inputs={"c": 3}),
            ],
        )

        run_id = f"version-{uuid4().hex[:8]}"

        engine = WorkflowEngine(registry, store)
        await engine.run(spec, run_id, seed=44444)

        checkpoint = await store.load(run_id)

        # Version should be > 1 after multiple saves
        assert checkpoint.version >= 3  # At least one save per step

    @pytest.mark.asyncio
    async def test_concurrent_checkpoint_updates(self):
        """Test handling of concurrent checkpoint updates."""
        store = TestCheckpointStore()
        run_id = f"concurrent-{uuid4().hex[:8]}"

        # Initial save
        await store.save(
            run_id=run_id,
            next_step_index=0,
            status="running",
        )

        ck1 = await store.load(run_id)
        ck2 = await store.load(run_id)

        # First update succeeds
        await store.save(
            run_id=run_id,
            next_step_index=1,
            status="running",
            expected_version=ck1.version,
        )

        # Second update with stale version fails
        with pytest.raises(Exception):  # CheckpointVersionConflictError
            await store.save(
                run_id=run_id,
                next_step_index=2,
                status="running",
                expected_version=ck2.version,  # Stale version
            )


class TestDeterminism:
    """Tests for deterministic execution across runs."""

    @pytest.mark.asyncio
    async def test_same_seed_same_output(self):
        """Test that same seed produces same outputs."""
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec

        registry = DeterministicSkillRegistry()
        spec = WorkflowSpec(
            id="test-determinism",
            name="Determinism Test",
            steps=[
                StepDescriptor(id="s1", skill_id="compute", inputs={"v": 1}),
                StepDescriptor(id="s2", skill_id="transform", inputs={"v": 2}),
            ],
        )

        seed = 55555
        results = []
        step_outputs_list = []

        # Run twice with same seed
        for i in range(2):
            store = TestCheckpointStore()
            engine = WorkflowEngine(registry, store)
            run_id = f"run-{i}"
            result = await engine.run(spec, run_id, seed=seed)
            results.append(result)
            # Load step outputs from checkpoint
            checkpoint = await store.load(run_id)
            step_outputs_list.append(checkpoint.step_outputs)

        # Both runs should complete successfully
        assert results[0].status == "completed"
        assert results[1].status == "completed"

        # Step outputs should be identical (deterministic)
        assert step_outputs_list[0] == step_outputs_list[1]

    @pytest.mark.asyncio
    async def test_different_seed_different_output(self):
        """Test that different seeds produce different outputs."""
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec

        registry = DeterministicSkillRegistry()
        spec = WorkflowSpec(
            id="test-seeds",
            name="Seeds Test",
            steps=[
                StepDescriptor(id="s1", skill_id="compute", inputs={"v": 1}),
            ],
        )

        seeds = [11111, 22222, 33333]
        step_outputs_list = []

        for seed in seeds:
            store = TestCheckpointStore()
            engine = WorkflowEngine(registry, store)
            run_id = f"seed-{seed}"
            result = await engine.run(spec, run_id, seed=seed)
            checkpoint = await store.load(run_id)
            # Get the output hash from the result to compare determinism
            step_outputs_list.append(str(checkpoint.step_outputs))

        # All outputs should be different due to different seeds
        assert len(set(step_outputs_list)) == len(seeds)


class TestMultipleResumeCycles:
    """Tests for multiple resume cycles."""

    @pytest.mark.asyncio
    async def test_multiple_resume_cycles(self):
        """Test workflow can resume multiple times."""
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec

        registry = DeterministicSkillRegistry()
        store = TestCheckpointStore()

        spec = WorkflowSpec(
            id="test-multi-resume",
            name="Multi Resume Test",
            steps=[StepDescriptor(id=f"step{i}", skill_id="compute", inputs={"i": i}) for i in range(5)],
        )

        run_id = f"multi-{uuid4().hex[:8]}"

        # Simulate multiple partial runs by pre-setting checkpoints
        for start_step in range(5):
            # Pre-create checkpoint at step N
            step_outputs = {f"step{i}": {"ok": True} for i in range(start_step)}

            await store.save(
                run_id=run_id,
                next_step_index=start_step,
                step_outputs=step_outputs,
                status="running",
                workflow_id=spec.id,
            )

            # Verify can resume
            engine = WorkflowEngine(registry, store)
            result = await engine.run(spec, run_id, seed=66666)

            assert result.status == "completed"
            assert result.steps_total == 5
