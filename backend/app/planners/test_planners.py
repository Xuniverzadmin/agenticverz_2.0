# Tests for Planner Adapters
# Run with: pytest backend/app/planners/test_planners.py -v

import os
from unittest.mock import patch

import pytest


class TestStubPlanner:
    """Tests for the StubPlanner adapter."""

    def test_stub_planner_initialization(self):
        """StubPlanner initializes without errors."""
        from app.hoc.int.platform.facades.stub_adapter import StubPlanner

        planner = StubPlanner()
        assert planner is not None

    def test_stub_planner_generates_plan(self):
        """StubPlanner returns a valid plan structure."""
        from app.hoc.int.platform.facades.stub_adapter import StubPlanner

        planner = StubPlanner()

        plan = planner.plan(agent_id="test-agent-123", goal="Fetch data from API")

        assert "plan_id" in plan
        assert "agent_id" in plan
        assert "steps" in plan
        assert len(plan["steps"]) >= 1
        assert plan["planner"] == "stub"

    def test_stub_planner_step_structure(self):
        """StubPlanner steps have required fields."""
        from app.hoc.int.platform.facades.stub_adapter import StubPlanner

        planner = StubPlanner()

        plan = planner.plan(agent_id="test-agent-456", goal="Test goal")

        step = plan["steps"][0]
        assert "step_id" in step
        assert "description" in step
        assert "skill" in step
        assert "params" in step
        assert "depends_on" in step

    def test_stub_planner_with_tool_manifest(self):
        """StubPlanner uses first tool from manifest."""
        from app.hoc.int.platform.facades.stub_adapter import StubPlanner

        planner = StubPlanner()

        tool_manifest = [
            {"name": "custom_skill", "description": "Custom skill"},
            {"name": "http_call", "description": "HTTP requests"},
        ]

        plan = planner.plan(agent_id="test-agent-789", goal="Run custom task", tool_manifest=tool_manifest)

        # Should use first skill from manifest
        assert plan["steps"][0]["skill"] == "custom_skill"

    def test_stub_planner_metadata(self):
        """StubPlanner includes metadata."""
        from app.hoc.int.platform.facades.stub_adapter import StubPlanner

        planner = StubPlanner()

        plan = planner.plan(agent_id="test-agent", goal="Test")

        assert "metadata" in plan
        assert plan["metadata"]["model"] is None
        assert plan["metadata"]["tokens_used"] == 0


class TestAnthropicPlanner:
    """Tests for the AnthropicPlanner adapter."""

    def test_anthropic_planner_initialization_without_key(self):
        """AnthropicPlanner initializes without API key (skeleton mode)."""
        from .anthropic_adapter import AnthropicPlanner

        planner = AnthropicPlanner()
        assert planner is not None
        assert planner.api_key is None

    def test_anthropic_planner_initialization_with_key(self):
        """AnthropicPlanner initializes with API key."""
        from .anthropic_adapter import AnthropicPlanner

        planner = AnthropicPlanner(api_key="test-key-123")
        assert planner.api_key == "test-key-123"

    def test_anthropic_planner_generates_stub_without_key(self):
        """AnthropicPlanner returns stub plan when no API key."""
        from .anthropic_adapter import AnthropicPlanner

        planner = AnthropicPlanner()

        plan = planner.plan(agent_id="test-agent", goal="Test goal")

        assert "plan_id" in plan
        assert "steps" in plan
        # Planner info is in metadata
        assert plan["metadata"]["planner"] == "anthropic"

    def test_anthropic_planner_custom_model(self):
        """AnthropicPlanner accepts custom model."""
        from .anthropic_adapter import AnthropicPlanner

        planner = AnthropicPlanner(model="claude-3-opus-20240229")
        assert planner.model == "claude-3-opus-20240229"

    def test_anthropic_planner_builds_prompts(self):
        """AnthropicPlanner builds system and user prompts."""
        from .anthropic_adapter import AnthropicPlanner

        planner = AnthropicPlanner()

        system_prompt = planner._build_system_prompt(None)
        assert "planner" in system_prompt.lower()  # "AI planner for AOS"
        assert "steps" in system_prompt.lower()

        user_prompt = planner._build_user_prompt(
            goal="Test goal",
            context_summary="Previous context",
            memory_snippets=[{"text": "Memory 1", "memory_type": "fact"}],
        )
        assert "Test goal" in user_prompt
        assert "Previous context" in user_prompt
        assert "Memory 1" in user_prompt

    def test_anthropic_planner_with_tool_manifest(self):
        """AnthropicPlanner includes tools in system prompt."""
        from .anthropic_adapter import AnthropicPlanner

        planner = AnthropicPlanner()

        tool_manifest = [{"name": "http_call", "description": "Make HTTP requests"}]

        system_prompt = planner._build_system_prompt(tool_manifest)
        assert "http_call" in system_prompt
        assert "Make HTTP requests" in system_prompt


class TestPlannerFactory:
    """Tests for the planner factory function."""

    def test_get_planner_default_stub(self):
        """get_planner returns StubPlanner by default."""
        with patch.dict(os.environ, {"PLANNER_BACKEND": "stub"}, clear=False):
            from . import get_planner
            from app.hoc.int.platform.facades.stub_adapter import StubPlanner

            # get_planner reads env at call time
            planner = get_planner()
            assert isinstance(planner, StubPlanner)

    def test_get_planner_anthropic(self):
        """get_planner returns AnthropicPlanner when configured."""
        with patch.dict(os.environ, {"PLANNER_BACKEND": "anthropic", "ANTHROPIC_API_KEY": "test-key"}, clear=False):
            from . import get_planner
            from .anthropic_adapter import AnthropicPlanner

            planner = get_planner()
            assert isinstance(planner, AnthropicPlanner)

    def test_get_planner_fallback_to_stub(self):
        """get_planner falls back to stub for unknown backends."""
        with patch.dict(os.environ, {"PLANNER_BACKEND": "unknown"}, clear=False):
            from . import get_planner
            from app.hoc.int.platform.facades.stub_adapter import StubPlanner

            planner = get_planner()
            assert isinstance(planner, StubPlanner)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
