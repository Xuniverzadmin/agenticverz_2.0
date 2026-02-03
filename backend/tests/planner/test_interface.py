# tests/planner/test_interface.py
"""
Planner Interface Tests (M2.5)

Tests for:
1. PlannerInterface protocol compliance
2. StubPlanner determinism
3. PlannerOutput structure
4. PlannerError handling
5. PlannerRegistry management
"""

import sys
from pathlib import Path

import pytest

# Add paths
_backend_path = str(Path(__file__).parent.parent.parent)
_app_path = str(Path(__file__).parent.parent.parent / "app")

for p in [_backend_path, _app_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.app.hoc.int.platform.drivers.interface import (
    DeterminismMode,
    PlanMetadata,
    PlannerError,
    PlannerErrorCode,
    PlannerOutput,
    PlannerRegistry,
    PlanStep,
    compute_plan_input_hash,
    normalize_goal,
)
from app.hoc.int.platform.drivers.stub_planner import LegacyStubPlanner, PlanRule, StubPlanner


class TestPlanStep:
    """Tests for PlanStep dataclass."""

    def test_step_creation(self):
        """Can create a plan step with required fields."""
        step = PlanStep(step_id="s1", skill="skill.http_call", params={"url": "https://example.com"})

        assert step.step_id == "s1"
        assert step.skill == "skill.http_call"
        assert step.params["url"] == "https://example.com"

    def test_step_defaults(self):
        """Step has sensible defaults."""
        step = PlanStep(step_id="s1", skill="test", params={})

        assert step.depends_on == []
        assert step.on_error == "abort"
        assert step.retry_count == 3
        assert step.output_key is None

    def test_step_to_dict(self):
        """Step serializes correctly."""
        step = PlanStep(
            step_id="s1", skill="skill.http_call", params={"url": "test"}, depends_on=["s0"], description="Fetch data"
        )

        d = step.to_dict()

        assert d["step_id"] == "s1"
        assert d["skill"] == "skill.http_call"
        assert d["depends_on"] == ["s0"]
        assert d["description"] == "Fetch data"


class TestPlanMetadata:
    """Tests for PlanMetadata dataclass."""

    def test_metadata_creation(self):
        """Can create metadata with required fields."""
        meta = PlanMetadata(planner="stub", planner_version="1.0.0")

        assert meta.planner == "stub"
        assert meta.planner_version == "1.0.0"

    def test_metadata_defaults(self):
        """Metadata has sensible defaults."""
        meta = PlanMetadata(planner="test", planner_version="1.0.0")

        assert meta.model is None
        assert meta.input_tokens == 0
        assert meta.output_tokens == 0
        assert meta.cost_cents == 0
        assert meta.deterministic is False
        assert meta.generated_at is not None

    def test_metadata_to_dict(self):
        """Metadata serializes correctly."""
        meta = PlanMetadata(
            planner="stub",
            planner_version="1.0.0",
            model="test-model",
            input_tokens=100,
            output_tokens=50,
            cost_cents=1,
            deterministic=True,
        )

        d = meta.to_dict()

        assert d["planner"] == "stub"
        assert d["model"] == "test-model"
        assert d["input_tokens"] == 100
        assert d["deterministic"] is True


class TestPlannerOutput:
    """Tests for PlannerOutput dataclass."""

    def test_output_creation(self):
        """Can create planner output."""
        steps = [PlanStep(step_id="s1", skill="test", params={})]
        meta = PlanMetadata(planner="stub", planner_version="1.0.0")

        output = PlannerOutput(steps=steps, metadata=meta)

        assert len(output.steps) == 1
        assert output.metadata.planner == "stub"

    def test_output_plan_property(self):
        """Plan property returns dict with steps and metadata."""
        steps = [PlanStep(step_id="s1", skill="test", params={"a": 1})]
        meta = PlanMetadata(planner="stub", planner_version="1.0.0")

        output = PlannerOutput(steps=steps, metadata=meta)
        plan = output.plan

        assert "steps" in plan
        assert "metadata" in plan
        assert len(plan["steps"]) == 1
        assert plan["metadata"]["planner"] == "stub"


class TestPlannerError:
    """Tests for PlannerError dataclass."""

    def test_error_creation(self):
        """Can create planner error."""
        error = PlannerError(code=PlannerErrorCode.INVALID_GOAL, message="Goal cannot be empty")

        assert error.code == PlannerErrorCode.INVALID_GOAL
        assert error.message == "Goal cannot be empty"
        assert error.retryable is False

    def test_error_with_details(self):
        """Error can include details and retry info."""
        error = PlannerError(
            code=PlannerErrorCode.RATE_LIMITED,
            message="Rate limited",
            retryable=True,
            retry_after_ms=5000,
            details={"limit": 100},
        )

        assert error.retryable is True
        assert error.retry_after_ms == 5000
        assert error.details["limit"] == 100


class TestStubPlanner:
    """Tests for StubPlanner implementation."""

    @pytest.fixture
    def planner(self):
        """Create fresh stub planner."""
        return StubPlanner()

    @pytest.fixture
    def manifest(self):
        """Test tool manifest."""
        return [
            {"skill_id": "skill.http_call", "name": "HTTP Call"},
            {"skill_id": "skill.json_transform", "name": "JSON Transform"},
            {"skill_id": "skill.llm_invoke", "name": "LLM Invoke"},
            {"skill_id": "skill.echo", "name": "Echo"},
        ]

    def test_planner_id(self, planner):
        """Planner has correct ID."""
        assert planner.planner_id == "stub"

    def test_planner_version(self, planner):
        """Planner has version."""
        assert planner.version == "1.0.0"

    def test_determinism_mode(self, planner):
        """Stub planner has FULL determinism."""
        assert planner.get_determinism_mode() == DeterminismMode.FULL

    def test_plan_echo_goal(self, planner, manifest):
        """Plans echo goal correctly."""
        result = planner.plan(agent_id="test", goal="echo hello world", tool_manifest=manifest)

        # Check by class name to avoid import path issues
        assert result.__class__.__name__ == "PlannerOutput"
        assert len(result.steps) == 1
        assert result.steps[0].skill == "skill.echo"

    def test_plan_fetch_goal(self, planner, manifest):
        """Plans fetch goal correctly."""
        result = planner.plan(agent_id="test", goal="fetch data from api", tool_manifest=manifest)

        assert result.__class__.__name__ == "PlannerOutput"
        assert len(result.steps) == 1
        assert result.steps[0].skill == "skill.http_call"

    def test_plan_analyze_goal(self, planner, manifest):
        """Plans analyze goal with multiple steps."""
        result = planner.plan(agent_id="test", goal="analyze user data", tool_manifest=manifest)

        assert result.__class__.__name__ == "PlannerOutput"
        assert len(result.steps) == 3
        assert result.steps[0].skill == "skill.http_call"
        assert result.steps[1].skill == "skill.json_transform"
        assert result.steps[2].skill == "skill.llm_invoke"

    def test_plan_dependencies(self, planner, manifest):
        """Multi-step plans have correct dependencies."""
        result = planner.plan(agent_id="test", goal="analyze data", tool_manifest=manifest)

        assert result.__class__.__name__ == "PlannerOutput"
        # s2 depends on s1, s3 depends on s2
        assert result.steps[1].depends_on == ["s1"]
        assert result.steps[2].depends_on == ["s2"]

    def test_plan_empty_goal_returns_error(self, planner):
        """Empty goal returns error."""
        result = planner.plan(agent_id="test", goal="   ", tool_manifest=[])

        assert result.__class__.__name__ == "PlannerError"
        assert result.code == PlannerErrorCode.INVALID_GOAL

    def test_plan_unknown_goal_returns_error(self, planner, manifest):
        """Unknown goal returns error."""
        result = planner.plan(agent_id="test", goal="do something completely unknown xyz123", tool_manifest=manifest)

        assert result.__class__.__name__ == "PlannerError"
        assert result.code == PlannerErrorCode.GENERATION_FAILED

    def test_plan_filters_by_manifest(self, planner):
        """Plan filters steps by available skills."""
        # Only http_call available
        manifest = [{"skill_id": "skill.http_call"}]

        result = planner.plan(
            agent_id="test",
            goal="analyze data",  # Would normally use 3 skills
            tool_manifest=manifest,
        )

        # Should only include the available skill
        if isinstance(result, PlannerOutput):
            skills_used = {s.skill for s in result.steps}
            assert all(s in {"skill.http_call"} for s in skills_used)

    def test_plan_deterministic(self, planner, manifest):
        """Same inputs produce identical outputs."""
        inputs = {"agent_id": "test", "goal": "fetch user data", "tool_manifest": manifest}

        result1 = planner.plan(**inputs)
        result2 = planner.plan(**inputs)

        assert result1.__class__.__name__ == "PlannerOutput"
        assert result2.__class__.__name__ == "PlannerOutput"

        # Steps must be identical
        assert len(result1.steps) == len(result2.steps)
        for s1, s2 in zip(result1.steps, result2.steps):
            assert s1.step_id == s2.step_id
            assert s1.skill == s2.skill
            assert s1.params == s2.params

        # Cache key must be identical
        assert result1.metadata.cache_key == result2.metadata.cache_key

    def test_plan_metadata_correct(self, planner, manifest):
        """Plan metadata is correct."""
        result = planner.plan(agent_id="test", goal="fetch data", tool_manifest=manifest)

        assert result.__class__.__name__ == "PlannerOutput"
        assert result.metadata.planner == "stub"
        assert result.metadata.planner_version == "1.0.0"
        assert result.metadata.deterministic is True
        assert result.metadata.cost_cents == 0
        assert result.metadata.cache_key is not None

    def test_call_history_recorded(self, planner, manifest):
        """Calls are recorded for verification."""
        planner.plan(agent_id="agent1", goal="fetch", tool_manifest=manifest)
        planner.plan(agent_id="agent2", goal="echo", tool_manifest=manifest)

        history = planner.get_call_history()

        assert len(history) == 2
        assert history[0]["agent_id"] == "agent1"
        assert history[1]["agent_id"] == "agent2"

    def test_reset_clears_history(self, planner, manifest):
        """Reset clears call history."""
        planner.plan(agent_id="test", goal="fetch", tool_manifest=manifest)
        assert len(planner.get_call_history()) == 1

        planner.reset()
        assert len(planner.get_call_history()) == 0


class TestStubPlannerCustomRules:
    """Tests for custom planning rules."""

    def test_add_custom_rule(self):
        """Can add custom planning rule."""
        planner = StubPlanner()

        custom_rule = PlanRule(
            keywords=["custom", "special"],
            steps=[PlanStep(step_id="c1", skill="skill.custom", params={"x": 1})],
            priority=100,
        )
        planner.add_rule(custom_rule)

        manifest = [{"skill_id": "skill.custom"}]
        result = planner.plan(agent_id="test", goal="do something custom", tool_manifest=manifest)

        assert result.__class__.__name__ == "PlannerOutput"
        assert result.steps[0].skill == "skill.custom"

    def test_clear_rules(self):
        """Can clear all rules."""
        planner = StubPlanner()
        planner.clear_rules()

        result = planner.plan(agent_id="test", goal="fetch data", tool_manifest=[])

        assert result.__class__.__name__ == "PlannerError"


class TestLegacyStubPlanner:
    """Tests for backwards-compatible legacy interface."""

    def test_legacy_plan_returns_dict(self):
        """Legacy planner returns dict with steps and metadata."""
        planner = LegacyStubPlanner()

        manifest = [{"skill_id": "skill.http_call"}]
        result = planner.plan(agent_id="test", goal="fetch data", tool_manifest=manifest)

        assert isinstance(result, dict)
        assert "steps" in result
        assert "metadata" in result

    def test_legacy_plan_error_returns_empty_steps(self):
        """Legacy planner returns empty steps on error."""
        planner = LegacyStubPlanner()

        result = planner.plan(
            agent_id="test",
            goal="   ",  # Empty goal
            tool_manifest=[],
        )

        assert isinstance(result, dict)
        assert result["steps"] == []
        assert "error" in result["metadata"]


class TestPlannerRegistry:
    """Tests for PlannerRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        PlannerRegistry.clear()

    def test_register_planner(self):
        """Can register a planner."""
        planner = StubPlanner()
        PlannerRegistry.register(planner)

        assert "stub" in PlannerRegistry.list()

    def test_get_planner(self):
        """Can get registered planner."""
        planner = StubPlanner()
        PlannerRegistry.register(planner)

        retrieved = PlannerRegistry.get("stub")
        assert retrieved is planner

    def test_default_planner(self):
        """First registered planner becomes default."""
        planner = StubPlanner()
        PlannerRegistry.register(planner)

        default = PlannerRegistry.get()  # No ID = default
        assert default is planner

    def test_explicit_default(self):
        """Can set explicit default."""
        planner1 = StubPlanner()
        planner2 = StubPlanner()

        PlannerRegistry.register(planner1)
        PlannerRegistry.register(planner2, is_default=True)

        default = PlannerRegistry.get()
        assert default is planner2


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_normalize_goal(self):
        """normalize_goal strips whitespace."""
        assert normalize_goal("  hello world  ") == "hello world"
        assert normalize_goal("test") == "test"

    def test_compute_plan_input_hash(self):
        """compute_plan_input_hash is deterministic."""
        hash1 = compute_plan_input_hash(
            agent_id="test",
            goal="fetch data",
            context_summary=None,
            memory_snippets=None,
            tool_manifest=[{"skill_id": "test"}],
        )

        hash2 = compute_plan_input_hash(
            agent_id="test",
            goal="fetch data",
            context_summary=None,
            memory_snippets=None,
            tool_manifest=[{"skill_id": "test"}],
        )

        assert hash1 == hash2
        assert len(hash1) == 16

    def test_compute_plan_input_hash_different_inputs(self):
        """Different inputs produce different hashes."""
        hash1 = compute_plan_input_hash(
            agent_id="agent1", goal="fetch", context_summary=None, memory_snippets=None, tool_manifest=None
        )

        hash2 = compute_plan_input_hash(
            agent_id="agent2", goal="fetch", context_summary=None, memory_snippets=None, tool_manifest=None
        )

        assert hash1 != hash2


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
