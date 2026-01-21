# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-066 (Skill Registry Filter)
"""
Unit tests for GAP-066: Skill Registry Filter.

Tests that ungoverned skills are properly filtered from the
registry in governed environments.
"""

import pytest
from app.skills.skill_registry_filter import (
    filter_skills_for_governance,
    FilterResult,
    UNGOVERNED_SKILLS,
)


class TestSkillRegistryFilter:
    """Test suite for skill registry filter."""

    def test_ungoverned_skills_defined(self):
        """UNGOVERNED_SKILLS should be defined with known dangerous skills."""
        assert isinstance(UNGOVERNED_SKILLS, set)
        assert len(UNGOVERNED_SKILLS) > 0

        # Should include known dangerous skills
        dangerous_skills = {"raw_sql_query", "shell_execute", "file_system_access"}
        assert dangerous_skills.issubset(UNGOVERNED_SKILLS)

    def test_filter_returns_result(self):
        """filter_skills_for_governance should return FilterResult."""
        registry = {
            "json_transform": {"name": "json_transform"},
            "http_connector": {"name": "http_connector"},
        }

        result = filter_skills_for_governance(registry, governance_profile="strict")

        assert isinstance(result, FilterResult)

    def test_filter_removes_ungoverned_skills(self):
        """Filter should remove ungoverned skills from registry."""
        registry = {
            "llm_invoke": {"name": "llm_invoke"},  # Should be removed (ungoverned)
            "json_transform": {"name": "json_transform"},  # Should remain (governed)
            "raw_sql_query": {"name": "raw_sql_query"},  # Should be removed (ungoverned)
        }

        result = filter_skills_for_governance(registry, governance_profile="strict")

        assert "raw_sql_query" not in result.filtered_registry
        assert "raw_sql_query" in result.removed_skills
        assert "json_transform" in result.filtered_registry

    def test_strict_profile_removes_ungoverned(self):
        """Strict governance profile should remove ungoverned skills."""
        registry = {
            "json_transform": {"name": "json_transform"},
            "raw_http_call": {"name": "raw_http_call"},
        }

        result = filter_skills_for_governance(registry, governance_profile="strict")

        assert "raw_http_call" in result.removed_skills

    def test_observe_only_profile_keeps_all(self):
        """Observe-only profile should keep all skills."""
        registry = {
            "llm_invoke": {"name": "llm_invoke"},
            "json_transform": {"name": "json_transform"},
        }

        result = filter_skills_for_governance(registry, governance_profile="observe_only")

        # Observe mode keeps all skills
        assert "llm_invoke" in result.filtered_registry
        assert len(result.removed_skills) == 0

    def test_result_includes_warnings(self):
        """FilterResult should include warnings for ungoverned skills."""
        registry = {
            "raw_sql_query": {"name": "raw_sql_query"},
        }

        result = filter_skills_for_governance(registry, governance_profile="strict")

        # Should have warnings about missing replacement
        assert isinstance(result.warnings, list)

    def test_empty_registry_returns_empty(self):
        """Empty registry should return empty result."""
        result = filter_skills_for_governance({}, governance_profile="strict")

        assert len(result.filtered_registry) == 0
        assert len(result.removed_skills) == 0


class TestFilterResult:
    """Test FilterResult dataclass."""

    def test_result_creation(self):
        """FilterResult should be creatable with required fields."""
        result = FilterResult(
            filtered_registry={"http_connector": {}, "json_transform": {}},
            removed_skills=["raw_sql_query"],
            replaced_skills={"raw_sql_query": "sql_gateway"},
            warnings=["raw_sql_query is ungoverned"],
        )

        assert len(result.filtered_registry) == 2
        assert len(result.removed_skills) == 1
        assert len(result.warnings) == 1

    def test_result_has_required_fields(self):
        """FilterResult should have all required fields."""
        result = FilterResult(
            filtered_registry={},
            removed_skills=[],
            replaced_skills={},
            warnings=[],
        )

        assert hasattr(result, "filtered_registry")
        assert hasattr(result, "removed_skills")
        assert hasattr(result, "replaced_skills")
        assert hasattr(result, "warnings")


class TestUngovernedSkills:
    """Test UNGOVERNED_SKILLS constant."""

    def test_ungoverned_includes_raw_sql(self):
        """UNGOVERNED_SKILLS should include raw_sql_query."""
        assert "raw_sql_query" in UNGOVERNED_SKILLS

    def test_ungoverned_includes_shell_execute(self):
        """UNGOVERNED_SKILLS should include shell_execute."""
        assert "shell_execute" in UNGOVERNED_SKILLS

    def test_ungoverned_includes_file_system(self):
        """UNGOVERNED_SKILLS should include file_system_access."""
        assert "file_system_access" in UNGOVERNED_SKILLS

    def test_ungoverned_includes_llm_invoke(self):
        """UNGOVERNED_SKILLS should include llm_invoke."""
        assert "llm_invoke" in UNGOVERNED_SKILLS

    def test_ungoverned_includes_raw_http_call(self):
        """UNGOVERNED_SKILLS should include raw_http_call."""
        assert "raw_http_call" in UNGOVERNED_SKILLS
