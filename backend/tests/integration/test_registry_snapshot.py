# tests/integration/test_registry_snapshot.py
"""
Registry Snapshot Test

Ensures skills from the committed snapshot are still registered.
Prevents silent deletion of skills.
"""
import json
from pathlib import Path

import pytest

SNAPSHOT_PATH = Path(__file__).parent.parent / "registry_snapshot.json"


class TestRegistrySnapshot:
    """Verify registry matches committed snapshot."""

    @pytest.fixture(autouse=True)
    def load_skills(self):
        """Load all skills before tests."""
        from app.skills import load_all_skills

        load_all_skills()

    def test_registry_matches_snapshot(self):
        """All skills from snapshot must be registered."""
        from app.skills import list_skills

        skills = list_skills()
        current = set(s["name"] for s in skills)
        snapshot = set(json.load(open(SNAPSHOT_PATH)))

        # Snapshot skills must exist (new skills are allowed)
        missing = snapshot - current
        assert not missing, f"Missing skills from snapshot: {sorted(missing)}"

    def test_snapshot_file_exists(self):
        """Snapshot file must exist."""
        assert SNAPSHOT_PATH.exists(), f"Snapshot file not found: {SNAPSHOT_PATH}"

    def test_expected_core_skills_registered(self):
        """Core skills (http_call, json_transform, llm_invoke) must exist."""
        from app.skills import list_skills

        skills = list_skills()
        names = {s["name"] for s in skills}

        core_skills = {"http_call", "json_transform", "llm_invoke"}
        missing = core_skills - names
        assert not missing, f"Missing core skills: {sorted(missing)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
