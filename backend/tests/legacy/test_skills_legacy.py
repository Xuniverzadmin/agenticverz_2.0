# Tests for Skills Registry and Skills (Legacy)
# Moved from app/skills/test_skills.py
# Run with: pytest tests/legacy/ -v
#
# DEPRECATION NOTICE:
# These tests are scheduled for removal. Coverage has been migrated to:
# - tests/integration/test_registry_snapshot.py (registry tests)
# - tests/skills/test_http_call_v2.py (http_call tests)
# - tests/skills/test_registry_v2.py (registry v2 tests)
#
# DEPRECATE_ON: 2026-03-01
# MIGRATION_TICKET: M4-LEGACY-001
# REASON: Legacy tests maintain coverage parity during migration period

import re

import pytest


@pytest.fixture(autouse=True, scope="module")
def load_skills_once():
    """Load all skills once before running legacy tests."""
    from app.skills import load_all_skills

    load_all_skills()


class TestSkillRegistry:
    """Tests for the skill registry."""

    def test_registry_has_http_call(self):
        """http_call skill is registered."""
        from app.skills.registry import get_skill

        entry = get_skill("http_call")
        assert entry is not None
        assert "class" in entry
        assert entry["version"] == "0.2.0"

    def test_registry_has_calendar_write(self):
        """calendar_write skill is registered."""
        from app.skills.registry import get_skill

        entry = get_skill("calendar_write")
        assert entry is not None
        assert "class" in entry
        assert entry["version"] == "0.1.0"

    def test_list_skills(self):
        """list_skills returns both registered skills."""
        from app.skills.registry import list_skills

        skills = list_skills()
        skill_names = [s["name"] for s in skills]
        assert "http_call" in skill_names
        assert "calendar_write" in skill_names

    def test_get_skill_manifest(self):
        """get_skill_manifest returns proper manifest format."""
        from app.skills.registry import get_skill_manifest

        manifest = get_skill_manifest()
        assert isinstance(manifest, list)
        assert len(manifest) >= 2

        for item in manifest:
            assert "name" in item
            assert "version" in item
            assert "description" in item

    def test_get_nonexistent_skill(self):
        """get_skill returns None for unknown skill."""
        from app.skills.registry import get_skill

        entry = get_skill("nonexistent_skill")
        assert entry is None


class TestHttpCallSkill:
    """Tests for HttpCallSkill."""

    def test_instantiation(self):
        """HttpCallSkill instantiates correctly."""
        from app.skills.http_call import HttpCallSkill

        skill = HttpCallSkill()
        assert skill.VERSION == "0.2.0"
        assert skill.allow_external is True

    def test_instantiation_with_external_disabled(self):
        """HttpCallSkill respects allow_external flag."""
        from app.skills.http_call import HttpCallSkill

        skill = HttpCallSkill(allow_external=False)
        assert skill.allow_external is False

    @pytest.mark.asyncio
    async def test_execute_local_url_forbidden(self):
        """HttpCallSkill returns FORBIDDEN for local URLs when allow_external=False.

        Contract: http_call.yaml -> url_behavior.local_urls.when_allow_external_false
        Local URLs are forbidden in stub mode to ensure deterministic behavior.
        """
        from app.skills.http_call import HttpCallSkill

        skill = HttpCallSkill(allow_external=False)

        result = await skill.execute({"url": "https://example.local/ping", "method": "GET"})

        assert result["skill"] == "http_call"
        assert result["skill_version"] == "0.2.0"
        # Contract: status=forbidden, code=403 for local URLs in stub mode
        assert result["result"]["status"] == "forbidden"
        assert result["result"]["code"] == 403
        assert result["result"]["body"]["error"] == "LOCAL_URL_FORBIDDEN"
        assert "duration" in result

    @pytest.mark.asyncio
    async def test_execute_external_stubbed(self):
        """HttpCallSkill stubs external URLs when disabled."""
        from app.skills.http_call import HttpCallSkill

        skill = HttpCallSkill(allow_external=False)

        result = await skill.execute({"url": "https://api.github.com/zen", "method": "GET"})

        assert result["result"]["status"] == "stubbed"
        assert result["result"]["code"] == 501

    @pytest.mark.asyncio
    async def test_execute_missing_url(self):
        """HttpCallSkill handles missing URL gracefully."""
        from app.skills.http_call import HttpCallSkill

        skill = HttpCallSkill(allow_external=False)

        result = await skill.execute({"method": "GET"})

        # Should use default URL or handle gracefully
        assert "result" in result
        assert result["skill"] == "http_call"


class TestCalendarWriteSkill:
    """Tests for CalendarWriteSkill."""

    def test_instantiation(self):
        """CalendarWriteSkill instantiates correctly."""
        from app.skills.calendar_write import CalendarWriteSkill

        skill = CalendarWriteSkill()
        assert skill.VERSION == "0.1.0"
        assert skill.provider == "mock"

    def test_instantiation_with_provider(self):
        """CalendarWriteSkill accepts custom provider."""
        from app.skills.calendar_write import CalendarWriteSkill

        skill = CalendarWriteSkill(provider="google")
        assert skill.provider == "google"

    @pytest.mark.asyncio
    async def test_execute_creates_event(self):
        """CalendarWriteSkill creates mock event."""
        from app.skills.calendar_write import CalendarWriteSkill

        skill = CalendarWriteSkill(provider="mock")

        result = await skill.execute(
            {"title": "Test Meeting", "start": "2025-12-01T10:00:00Z", "end": "2025-12-01T11:00:00Z"}
        )

        assert result["skill"] == "calendar_write"
        assert result["skill_version"] == "0.1.0"
        assert result["result"]["status"] == "ok"
        assert "event_id" in result["result"]
        assert re.match(r"[0-9a-fA-F-]{36}", result["result"]["event_id"])
        assert result["result"]["title"] == "Test Meeting"

    @pytest.mark.asyncio
    async def test_execute_side_effects(self):
        """CalendarWriteSkill returns side effects."""
        from app.skills.calendar_write import CalendarWriteSkill

        skill = CalendarWriteSkill(provider="mock")

        result = await skill.execute({"title": "Side Effect Test"})

        assert "side_effects" in result
        assert result["side_effects"]["written_to_memory"] is True
        assert "memory_key" in result["side_effects"]
        assert result["side_effects"]["memory_key"].startswith("calendar_event:")

    @pytest.mark.asyncio
    async def test_execute_default_title(self):
        """CalendarWriteSkill uses default title if not provided."""
        from app.skills.calendar_write import CalendarWriteSkill

        skill = CalendarWriteSkill(provider="mock")

        result = await skill.execute({})

        assert result["result"]["title"] == "Untitled Event"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
