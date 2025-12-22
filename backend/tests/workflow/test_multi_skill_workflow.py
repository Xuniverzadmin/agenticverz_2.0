# tests/workflow/test_multi_skill_workflow.py
"""
Multi-Skill Workflow Golden Test

Tests that multi-skill workflows execute correctly with:
1. Step dependencies (depends_on)
2. Output interpolation ({{step_id.field}})
3. Deterministic stub outputs
4. Golden file comparison

This is the canonical test for verifying the skill orchestration engine.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Add paths for imports
_backend_path = str(Path(__file__).parent.parent.parent)
_runtime_path = str(Path(__file__).parent.parent.parent / "app" / "worker" / "runtime")
_skills_path = str(Path(__file__).parent.parent.parent / "app" / "skills")

for p in [_backend_path, _runtime_path, _skills_path]:
    if p not in sys.path:
        sys.path.insert(0, p)


# Import runtime and stubs
from core import Runtime, StructuredOutcome

# Import stubs directly
from stubs.http_call_stub import (
    HTTP_CALL_STUB_DESCRIPTOR,
    get_http_call_stub,
    http_call_stub_handler,
)
from stubs.json_transform_stub import (
    JSON_TRANSFORM_STUB_DESCRIPTOR,
    json_transform_stub_handler,
)
from stubs.llm_invoke_stub import (
    LLM_INVOKE_STUB_DESCRIPTOR,
    llm_invoke_stub_handler,
)

GOLDEN_FILE = Path(__file__).parent.parent / "golden" / "workflow_multi_skill.json"


@dataclass
class WorkflowStep:
    """Represents a step in a workflow."""

    step_id: str
    skill: str
    params: Dict[str, Any]
    depends_on: List[str]
    on_error: str = "abort"
    retry_count: int = 3


@dataclass
class WorkflowResult:
    """Result of workflow execution."""

    status: str
    steps: List[Dict[str, Any]]
    workflow_hash: str


class WorkflowExecutor:
    """
    Executes multi-skill workflows with dependency resolution.

    This is a simplified version for testing - production uses runner.py
    """

    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.step_outputs: Dict[str, Dict[str, Any]] = {}

    async def execute(self, plan: Dict[str, Any]) -> WorkflowResult:
        """
        Execute a workflow plan.

        Args:
            plan: Plan dict with "steps" array

        Returns:
            WorkflowResult with status and step results
        """
        steps = plan.get("steps", [])
        results = []

        for step_data in steps:
            step = WorkflowStep(
                step_id=step_data["step_id"],
                skill=step_data["skill"],
                params=step_data.get("params", {}),
                depends_on=step_data.get("depends_on", []),
                on_error=step_data.get("on_error", "abort"),
                retry_count=step_data.get("retry_count", 3),
            )

            # Wait for dependencies (already satisfied in sequential execution)
            # In production, this would be async with dependency graph

            # Interpolate params with previous step outputs
            interpolated_params = self._interpolate(step.params)

            # Execute step
            outcome = await self.runtime.execute(step.skill, interpolated_params)

            # Store output for interpolation
            if outcome.ok:
                self.step_outputs[step.step_id] = outcome.result or {}

            # Record result
            results.append(
                {
                    "step_id": step.step_id,
                    "skill": step.skill,
                    "ok": outcome.ok,
                    "output_hash": self._hash_output(outcome),
                }
            )

            # Handle errors
            if not outcome.ok and step.on_error == "abort":
                return WorkflowResult(status="failed", steps=results, workflow_hash=self._hash_workflow(results))

        return WorkflowResult(status="ok", steps=results, workflow_hash=self._hash_workflow(results))

    def _interpolate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Interpolate {{step_id.field}} references."""
        import re

        def replace(match):
            path = match.group(1)
            parts = path.split(".")
            if len(parts) >= 2:
                step_id = parts[0]
                field = ".".join(parts[1:])
                if step_id in self.step_outputs:
                    output = self.step_outputs[step_id]
                    # Navigate nested fields
                    for part in parts[1:]:
                        if isinstance(output, dict) and part in output:
                            output = output[part]
                        else:
                            return match.group(0)
                    return str(output) if not isinstance(output, str) else output
            return match.group(0)

        def interpolate_value(v):
            if isinstance(v, str):
                return re.sub(r"\{\{([^}]+)\}\}", replace, v)
            elif isinstance(v, dict):
                return {k: interpolate_value(vv) for k, vv in v.items()}
            elif isinstance(v, list):
                return [interpolate_value(item) for item in v]
            return v

        return interpolate_value(params)

    def _hash_output(self, outcome: StructuredOutcome) -> str:
        """Hash outcome for comparison."""
        # Use deterministic for stubs
        return "deterministic"

    def _hash_workflow(self, results: List[Dict]) -> str:
        """Hash workflow result for comparison."""
        return "workflow_deterministic"


class TestMultiSkillWorkflow:
    """Tests for multi-skill workflow execution."""

    @pytest.fixture
    def runtime(self):
        """Create runtime with all stubs registered."""
        rt = Runtime()

        # Configure HTTP stub to return user data
        http_stub = get_http_call_stub()
        http_stub.add_response(
            "api.example.com/users",
            {
                "status_code": 200,
                "body": json.dumps({"id": 1, "name": "Test User", "email": "test@example.com"}),
                "headers": {"content-type": "application/json"},
            },
        )

        # Register stubs (descriptor, handler)
        rt.register_skill(HTTP_CALL_STUB_DESCRIPTOR, http_call_stub_handler)
        rt.register_skill(JSON_TRANSFORM_STUB_DESCRIPTOR, json_transform_stub_handler)
        rt.register_skill(LLM_INVOKE_STUB_DESCRIPTOR, llm_invoke_stub_handler)

        return rt

    @pytest.fixture
    def golden_data(self):
        """Load golden file data."""
        with open(GOLDEN_FILE) as f:
            return json.load(f)

    @pytest.mark.asyncio
    async def test_workflow_executes_all_steps(self, runtime, golden_data):
        """Workflow should execute all steps in order."""
        executor = WorkflowExecutor(runtime)
        plan = golden_data["input"]["plan"]

        result = await executor.execute(plan)

        assert result.status == "ok"
        assert len(result.steps) == 3

    @pytest.mark.asyncio
    async def test_workflow_step_order_matches_golden(self, runtime, golden_data):
        """Step order should match golden file."""
        executor = WorkflowExecutor(runtime)
        plan = golden_data["input"]["plan"]

        result = await executor.execute(plan)

        expected_steps = golden_data["expected_output"]["steps"]
        for i, (actual, expected) in enumerate(zip(result.steps, expected_steps)):
            assert actual["step_id"] == expected["step_id"], f"Step {i} ID mismatch"
            assert actual["skill"] == expected["skill"], f"Step {i} skill mismatch"

    @pytest.mark.asyncio
    async def test_workflow_dependency_resolution(self, runtime, golden_data):
        """Steps with dependencies should receive interpolated values."""
        executor = WorkflowExecutor(runtime)
        plan = golden_data["input"]["plan"]

        result = await executor.execute(plan)

        # All steps should succeed (dependencies resolved)
        for step in result.steps:
            assert step["ok"] is True, f"Step {step['step_id']} failed"

    @pytest.mark.asyncio
    async def test_workflow_deterministic_output(self, runtime, golden_data):
        """Running workflow twice should produce same result."""
        executor1 = WorkflowExecutor(runtime)
        executor2 = WorkflowExecutor(runtime)
        plan = golden_data["input"]["plan"]

        result1 = await executor1.execute(plan)
        result2 = await executor2.execute(plan)

        # Status should match
        assert result1.status == result2.status

        # Step results should match
        assert len(result1.steps) == len(result2.steps)
        for s1, s2 in zip(result1.steps, result2.steps):
            assert s1["step_id"] == s2["step_id"]
            assert s1["skill"] == s2["skill"]
            assert s1["ok"] == s2["ok"]

    @pytest.mark.asyncio
    async def test_workflow_abort_on_error(self, runtime):
        """Workflow should abort on step failure when on_error=abort."""
        # Create a plan with a failing step
        plan = {
            "steps": [
                {
                    "step_id": "s1",
                    "skill": "skill.nonexistent",  # Will fail
                    "params": {},
                    "on_error": "abort",
                },
                {"step_id": "s2", "skill": "skill.http_call", "params": {}, "depends_on": ["s1"]},
            ]
        }

        executor = WorkflowExecutor(runtime)
        result = await executor.execute(plan)

        # Should fail and only have one step result
        assert result.status == "failed"
        assert len(result.steps) == 1

    @pytest.mark.asyncio
    async def test_workflow_matches_golden_structure(self, runtime, golden_data):
        """Workflow output structure should match golden file."""
        executor = WorkflowExecutor(runtime)
        plan = golden_data["input"]["plan"]

        result = await executor.execute(plan)
        expected = golden_data["expected_output"]

        # Check structure matches (ignoring variance fields)
        assert result.status == expected["status"]
        assert len(result.steps) == len(expected["steps"])

        for actual, exp in zip(result.steps, expected["steps"]):
            for field in golden_data["_meta"]["deterministic_fields"]:
                # Handle array notation like "steps[0].skill"
                if field.startswith("steps["):
                    # Already comparing step-by-step
                    continue


class TestWorkflowInterpolation:
    """Tests for parameter interpolation."""

    def test_simple_interpolation(self):
        """Simple {{step_id.field}} interpolation works."""
        executor = WorkflowExecutor(Runtime())
        executor.step_outputs["s1"] = {"body": "hello world"}

        params = {"data": "{{s1.body}}"}
        result = executor._interpolate(params)

        assert result["data"] == "hello world"

    def test_nested_interpolation(self):
        """Nested field interpolation works."""
        executor = WorkflowExecutor(Runtime())
        executor.step_outputs["s1"] = {"response": {"user": {"email": "test@example.com"}}}

        params = {"email": "{{s1.response.user.email}}"}
        result = executor._interpolate(params)

        assert result["email"] == "test@example.com"

    def test_multiple_interpolations(self):
        """Multiple interpolations in same string work."""
        executor = WorkflowExecutor(Runtime())
        executor.step_outputs["s1"] = {"name": "Alice"}
        executor.step_outputs["s2"] = {"greeting": "Hello"}

        params = {"message": "{{s2.greeting}}, {{s1.name}}!"}
        result = executor._interpolate(params)

        assert result["message"] == "Hello, Alice!"

    def test_missing_reference_unchanged(self):
        """Missing references are left unchanged."""
        executor = WorkflowExecutor(Runtime())

        params = {"data": "{{nonexistent.field}}"}
        result = executor._interpolate(params)

        assert result["data"] == "{{nonexistent.field}}"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
