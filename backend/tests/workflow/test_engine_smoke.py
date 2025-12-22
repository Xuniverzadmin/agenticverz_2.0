# Workflow Engine Smoke Tests (M4)
"""
Unit and integration tests for the workflow engine.

Tests:
1. Basic workflow execution
2. Checkpoint save/load/resume
3. Step dependency resolution
4. Error handling and retry
5. Golden file recording
"""

from typing import Any, Dict, Optional

import pytest

from app.workflow.checkpoint import InMemoryCheckpointStore
from app.workflow.engine import (
    StepDescriptor,
    WorkflowEngine,
    WorkflowSpec,
    _derive_seed,
)
from app.workflow.golden import InMemoryGoldenRecorder
from app.workflow.planner_sandbox import PlannerSandbox
from app.workflow.policies import PolicyEnforcer

# ============== Test Fixtures ==============


class DummySkill:
    """Deterministic dummy skill for testing."""

    def __init__(self, skill_id: str, fail_on_attempt: Optional[int] = None):
        self.skill_id = skill_id
        self.fail_on_attempt = fail_on_attempt
        self.call_count = 0

    async def invoke(
        self,
        inputs: Dict[str, Any],
        seed: int = 0,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self.call_count += 1

        # Simulate failure on specific attempt
        if self.fail_on_attempt and self.call_count <= self.fail_on_attempt:
            return {
                "ok": False,
                "success": False,
                # Use TIMEOUT which is a retryable error code
                "error": {"code": "TIMEOUT", "message": "Simulated transient failure"},
            }

        # Deterministic output based on seed + inputs
        return {
            "ok": True,
            "success": True,
            "skill": self.skill_id,
            "seed": seed,
            "inputs": inputs,
            "call_count": self.call_count,
        }


class DummyRegistry:
    """Simple skill registry for testing."""

    def __init__(self):
        self._skills: Dict[str, Any] = {}

    def register(self, skill_id: str, skill: Any) -> None:
        self._skills[skill_id] = skill

    def get(self, skill_id: str) -> Optional[Any]:
        return self._skills.get(skill_id)


@pytest.fixture
def registry():
    """Create registry with test skills."""
    reg = DummyRegistry()
    reg.register("noop", DummySkill("noop"))
    reg.register("echo", DummySkill("echo"))
    reg.register("transform", DummySkill("transform"))
    reg.register("failing", DummySkill("failing", fail_on_attempt=1))
    return reg


@pytest.fixture
def checkpoint_store():
    """Create in-memory checkpoint store."""
    return InMemoryCheckpointStore()


@pytest.fixture
def golden_recorder():
    """Create in-memory golden recorder."""
    return InMemoryGoldenRecorder()


@pytest.fixture
def engine(registry, checkpoint_store, golden_recorder):
    """Create workflow engine with test dependencies."""
    return WorkflowEngine(
        registry=registry,
        checkpoint_store=checkpoint_store,
        golden=golden_recorder,
    )


# ============== Seed Derivation Tests ==============


class TestSeedDerivation:
    """Tests for deterministic seed derivation."""

    def test_derive_seed_is_deterministic(self):
        """Same inputs produce same seed."""
        seed1 = _derive_seed(12345, 0)
        seed2 = _derive_seed(12345, 0)
        assert seed1 == seed2

    def test_derive_seed_differs_by_step(self):
        """Different steps produce different seeds."""
        seed0 = _derive_seed(12345, 0)
        seed1 = _derive_seed(12345, 1)
        seed2 = _derive_seed(12345, 2)

        assert seed0 != seed1
        assert seed1 != seed2
        assert seed0 != seed2

    def test_derive_seed_differs_by_base(self):
        """Different base seeds produce different step seeds."""
        seed_a = _derive_seed(111, 0)
        seed_b = _derive_seed(222, 0)
        assert seed_a != seed_b


# ============== Workflow Spec Tests ==============


class TestWorkflowSpec:
    """Tests for WorkflowSpec parsing and serialization."""

    def test_from_dict_minimal(self):
        """Parse minimal workflow spec."""
        data = {
            "id": "test-workflow",
            "steps": [
                {"id": "step1", "skill_id": "noop"},
            ],
        }
        spec = WorkflowSpec.from_dict(data)

        assert spec.id == "test-workflow"
        assert spec.name == "test-workflow"  # defaults to id
        assert len(spec.steps) == 1
        assert spec.steps[0].id == "step1"
        assert spec.steps[0].skill_id == "noop"

    def test_from_dict_full(self):
        """Parse full workflow spec with all fields."""
        data = {
            "id": "full-workflow",
            "name": "Full Workflow",
            "version": "2.0.0",
            "budget_ceiling_cents": 500,
            "timeout_seconds": 60.0,
            "steps": [
                {
                    "id": "step1",
                    "skill_id": "http_call",
                    "inputs": {"url": "http://example.com"},
                    "estimated_cost_cents": 10,
                    "max_cost_cents": 50,
                    "retry": True,
                    "max_retries": 2,
                },
            ],
        }
        spec = WorkflowSpec.from_dict(data)

        assert spec.name == "Full Workflow"
        assert spec.version == "2.0.0"
        assert spec.budget_ceiling_cents == 500
        assert spec.steps[0].retry is True
        assert spec.steps[0].max_retries == 2

    def test_to_dict_roundtrip(self):
        """Spec survives roundtrip through dict."""
        original = WorkflowSpec(
            id="roundtrip",
            name="Roundtrip Test",
            steps=[
                StepDescriptor(id="s1", skill_id="noop", inputs={"x": 1}),
            ],
        )
        data = original.to_dict()
        restored = WorkflowSpec.from_dict(data)

        assert restored.id == original.id
        assert restored.name == original.name
        assert len(restored.steps) == len(original.steps)


# ============== Engine Execution Tests ==============


class TestWorkflowEngine:
    """Tests for WorkflowEngine execution."""

    @pytest.mark.asyncio
    async def test_run_simple_workflow(self, engine, checkpoint_store):
        """Run a simple two-step workflow."""
        spec = WorkflowSpec(
            id="simple",
            name="Simple Workflow",
            steps=[
                StepDescriptor(id="step1", skill_id="noop", inputs={"a": 1}),
                StepDescriptor(id="step2", skill_id="echo", inputs={"b": 2}),
            ],
        )

        result = await engine.run(spec, run_id="run-1", seed=12345)

        assert result.status == "completed"
        assert result.steps_completed == 2
        assert result.steps_total == 2
        assert len(result.step_results) == 2
        assert all(r.success for r in result.step_results)

    @pytest.mark.asyncio
    async def test_deterministic_execution(self, engine):
        """Same seed produces same results."""
        spec = WorkflowSpec(
            id="deterministic",
            name="Deterministic Test",
            steps=[
                StepDescriptor(id="s1", skill_id="noop", inputs={"x": 1}),
            ],
        )

        result1 = await engine.run(spec, run_id="run-a", seed=99999)
        result2 = await engine.run(spec, run_id="run-b", seed=99999)

        # Same seed should produce same step results (excluding timing)
        assert result1.step_results[0].output["seed"] == result2.step_results[0].output["seed"]

    @pytest.mark.asyncio
    async def test_skill_not_found(self, engine):
        """Gracefully handle missing skill."""
        spec = WorkflowSpec(
            id="missing-skill",
            name="Missing Skill Test",
            steps=[
                StepDescriptor(id="s1", skill_id="nonexistent"),
            ],
        )

        result = await engine.run(spec, run_id="run-missing", seed=1)

        assert result.status == "failed"
        assert result.step_results[0].success is False
        assert "SKILL_NOT_FOUND" in result.step_results[0].error["code"]

    @pytest.mark.asyncio
    async def test_checkpoint_saves_progress(self, engine, checkpoint_store):
        """Checkpoint is saved after each step."""
        spec = WorkflowSpec(
            id="checkpoint-test",
            name="Checkpoint Test",
            steps=[
                StepDescriptor(id="s1", skill_id="noop"),
                StepDescriptor(id="s2", skill_id="echo"),
            ],
        )

        await engine.run(spec, run_id="ck-run", seed=1)

        ck = await checkpoint_store.load("ck-run")
        assert ck is not None
        assert ck.status == "completed"
        assert ck.next_step_index == 2
        assert "s1" in ck.step_outputs
        assert "s2" in ck.step_outputs

    @pytest.mark.asyncio
    async def test_golden_records_events(self, engine, golden_recorder):
        """Golden recorder captures all events."""
        spec = WorkflowSpec(
            id="golden-test",
            name="Golden Test",
            steps=[
                StepDescriptor(id="s1", skill_id="noop"),
            ],
        )

        await engine.run(spec, run_id="golden-run", seed=1)

        events = golden_recorder.get_events("golden-run")
        assert len(events) == 3  # run_start, step, run_end

        assert events[0].event_type == "run_start"
        assert events[1].event_type == "step"
        assert events[2].event_type == "run_end"


# ============== Resume Tests ==============


class TestWorkflowResume:
    """Tests for checkpoint resume functionality."""

    @pytest.mark.asyncio
    async def test_resume_from_checkpoint(self, registry, checkpoint_store, golden_recorder):
        """Workflow resumes from checkpoint after simulated restart."""
        # First run: execute first step
        engine1 = WorkflowEngine(
            registry=registry,
            checkpoint_store=checkpoint_store,
            golden=golden_recorder,
        )

        spec = WorkflowSpec(
            id="resume-test",
            name="Resume Test",
            steps=[
                StepDescriptor(id="step1", skill_id="noop"),
                StepDescriptor(id="step2", skill_id="echo"),
            ],
        )

        # Manually save checkpoint at step 1
        await checkpoint_store.save(
            run_id="resume-run",
            next_step_index=1,
            last_result_hash="abc123",
            step_outputs={"step1": {"value": "from_step1"}},
            status="running",
        )

        # "Restart" with new engine instance
        engine2 = WorkflowEngine(
            registry=registry,
            checkpoint_store=checkpoint_store,
            golden=golden_recorder,
        )

        result = await engine2.run(spec, run_id="resume-run", seed=12345)

        # Should complete from step2
        assert result.status == "completed"
        assert result.steps_completed == 1  # Only step2 was executed


# ============== Dependency Resolution Tests ==============


class TestDependencyResolution:
    """Tests for step input dependency resolution."""

    @pytest.mark.asyncio
    async def test_resolve_step_reference(self, engine):
        """Resolve ${step_id} references in inputs."""
        spec = WorkflowSpec(
            id="deps-test",
            name="Dependencies Test",
            steps=[
                StepDescriptor(id="producer", skill_id="noop", inputs={"value": 42}),
                StepDescriptor(
                    id="consumer",
                    skill_id="echo",
                    inputs={"previous": "${producer}"},
                    depends_on=["producer"],
                ),
            ],
        )

        result = await engine.run(spec, run_id="deps-run", seed=1)

        assert result.status == "completed"
        # Consumer should have received producer's output
        consumer_inputs = result.step_results[1].output["inputs"]
        assert "previous" in consumer_inputs
        # The resolved input should be the producer's output dict
        assert isinstance(consumer_inputs["previous"], dict)


# ============== Error Handling Tests ==============


class TestErrorHandling:
    """Tests for error handling and retry logic."""

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, registry, checkpoint_store, golden_recorder):
        """Step retries on transient failure."""
        # Register a skill that fails first, succeeds second
        failing_skill = DummySkill("retry_test", fail_on_attempt=1)
        registry.register("retry_test", failing_skill)

        engine = WorkflowEngine(
            registry=registry,
            checkpoint_store=checkpoint_store,
            golden=golden_recorder,
        )

        spec = WorkflowSpec(
            id="retry-test",
            name="Retry Test",
            steps=[
                StepDescriptor(
                    id="s1",
                    skill_id="retry_test",
                    retry=True,
                    max_retries=2,
                ),
            ],
        )

        result = await engine.run(spec, run_id="retry-run", seed=1)

        # Should eventually succeed after retry
        assert result.status == "completed"
        assert result.step_results[0].retries >= 1

    @pytest.mark.asyncio
    async def test_abort_on_error(self, engine):
        """Workflow aborts on step failure with on_error=abort."""
        spec = WorkflowSpec(
            id="abort-test",
            name="Abort Test",
            steps=[
                StepDescriptor(id="s1", skill_id="failing", on_error="abort"),
                StepDescriptor(id="s2", skill_id="noop"),  # Should not run
            ],
        )

        result = await engine.run(spec, run_id="abort-run", seed=1)

        assert result.status == "failed"
        assert result.steps_completed == 0
        assert len(result.step_results) == 1


# ============== Policy Integration Tests ==============


class TestPolicyIntegration:
    """Tests for policy enforcement."""

    @pytest.mark.asyncio
    async def test_budget_exceeded_stops_workflow(self, registry, checkpoint_store):
        """Workflow stops when budget is exceeded."""
        policy = PolicyEnforcer(
            step_ceiling_cents=10,
            workflow_ceiling_cents=50,
        )

        engine = WorkflowEngine(
            registry=registry,
            checkpoint_store=checkpoint_store,
            policy=policy,
        )

        spec = WorkflowSpec(
            id="budget-test",
            name="Budget Test",
            steps=[
                StepDescriptor(id="s1", skill_id="noop", estimated_cost_cents=100),  # Exceeds ceiling
            ],
        )

        result = await engine.run(spec, run_id="budget-run", seed=1)

        # Budget exceeded - should have specific error code
        assert result.status == "budget_exceeded"
        # Error code should be specific: STEP_CEILING_EXCEEDED, WORKFLOW_CEILING_EXCEEDED,
        # AGENT_BUDGET_EXCEEDED, or BUDGET_EXCEEDED
        error_code = result.step_results[0].error_code
        assert error_code in (
            "STEP_CEILING_EXCEEDED",
            "WORKFLOW_CEILING_EXCEEDED",
            "AGENT_BUDGET_EXCEEDED",
            "BUDGET_EXCEEDED",
        )


# ============== Sandbox Integration Tests ==============


class TestSandboxIntegration:
    """Tests for planner sandbox validation."""

    @pytest.mark.asyncio
    async def test_sandbox_rejects_forbidden_skill(self, registry, checkpoint_store):
        """Sandbox rejects plans with forbidden skills."""
        sandbox = PlannerSandbox()

        engine = WorkflowEngine(
            registry=registry,
            checkpoint_store=checkpoint_store,
            sandbox=sandbox,
        )

        spec = WorkflowSpec(
            id="sandbox-test",
            name="Sandbox Test",
            steps=[
                StepDescriptor(
                    id="s1",
                    skill_id="noop",
                    planner_output={
                        "steps": [
                            {"id": "s1", "skill_id": "shell_exec"}  # Forbidden
                        ]
                    },
                ),
            ],
        )

        result = await engine.run(spec, run_id="sandbox-run", seed=1)

        assert result.status == "sandbox_rejected"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
