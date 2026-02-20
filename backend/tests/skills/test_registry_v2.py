# tests/skills/test_registry_v2.py
"""
Skill Registry v2 Tests (M2)

Tests for:
- Registration, idempotence, version resolution
- Persistence layer
- Concurrent registration
- Integration with runtime interfaces
"""

import os
import tempfile

import pytest

from app.hoc.int.agent.drivers.registry_v2 import (
    SkillRegistry,
    SkillVersion,
    get_global_registry,
    get_skill_handler,
    register_skill,
    set_global_registry,
)
from app.hoc.int.worker.runtime.core import SkillDescriptor

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def registry():
    """Create a fresh in-memory registry."""
    return SkillRegistry()


@pytest.fixture
def persistent_registry():
    """Create a registry with sqlite persistence."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    reg = SkillRegistry(persistence_path=db_path)
    yield reg
    reg.close()
    os.unlink(db_path)


@pytest.fixture
def sample_descriptor():
    """Create a sample skill descriptor."""
    return SkillDescriptor(
        skill_id="skill.test",
        name="Test Skill",
        version="1.0.0",
        inputs_schema_version="1.0",
        outputs_schema_version="1.0",
        cost_model={"base_cents": 5},
    )


@pytest.fixture
def sample_handler():
    """Create a sample async handler."""

    async def handler(inputs):
        return {"processed": inputs}

    return handler


# ============================================================================
# Test: SkillVersion
# ============================================================================


class TestSkillVersion:
    """Tests for SkillVersion parsing and comparison."""

    def test_parse_full_version(self):
        """Parse version with all components."""
        v = SkillVersion.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_parse_partial_version(self):
        """Parse version with missing components."""
        v = SkillVersion.parse("1.2")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 0

    def test_version_comparison(self):
        """Compare versions correctly."""
        v1 = SkillVersion.parse("1.0.0")
        v2 = SkillVersion.parse("1.0.1")
        v3 = SkillVersion.parse("1.1.0")
        v4 = SkillVersion.parse("2.0.0")

        assert v1 < v2
        assert v2 < v3
        assert v3 < v4
        assert v1 == SkillVersion.parse("1.0.0")

    def test_version_string(self):
        """Convert version to string."""
        v = SkillVersion(1, 2, 3)
        assert str(v) == "1.2.3"


# ============================================================================
# Test: Registration
# ============================================================================


class TestRegistration:
    """Tests for skill registration."""

    def test_register_success(self, registry, sample_descriptor, sample_handler):
        """Register a skill successfully."""
        reg = registry.register(sample_descriptor, sample_handler)

        assert reg.skill_id == "skill.test"
        assert reg.version == "1.0.0"
        assert registry.exists("skill.test")

    def test_register_duplicate_fails(self, registry, sample_descriptor, sample_handler):
        """Registering same version twice should fail."""
        registry.register(sample_descriptor, sample_handler)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(sample_descriptor, sample_handler)

    def test_register_different_versions(self, registry, sample_handler):
        """Can register different versions of same skill."""
        desc_v1 = SkillDescriptor(skill_id="skill.test", name="Test", version="1.0.0")
        desc_v2 = SkillDescriptor(skill_id="skill.test", name="Test", version="2.0.0")

        registry.register(desc_v1, sample_handler)
        registry.register(desc_v2, sample_handler)

        assert registry.exists("skill.test", "1.0.0")
        assert registry.exists("skill.test", "2.0.0")

    def test_latest_version_resolved(self, registry, sample_handler):
        """resolve() without version returns latest."""
        desc_v1 = SkillDescriptor(skill_id="skill.test", name="Test", version="1.0.0")
        desc_v2 = SkillDescriptor(skill_id="skill.test", name="Test", version="2.0.0")

        registry.register(desc_v1, sample_handler)
        registry.register(desc_v2, sample_handler)

        resolved = registry.resolve("skill.test")
        assert resolved.version == "2.0.0"

    def test_specific_version_resolved(self, registry, sample_handler):
        """resolve() with version returns specific version."""
        desc_v1 = SkillDescriptor(skill_id="skill.test", name="Test", version="1.0.0")
        desc_v2 = SkillDescriptor(skill_id="skill.test", name="Test", version="2.0.0")

        registry.register(desc_v1, sample_handler)
        registry.register(desc_v2, sample_handler)

        resolved = registry.resolve("skill.test", "1.0.0")
        assert resolved.version == "1.0.0"

    def test_register_with_tags(self, registry, sample_descriptor, sample_handler):
        """Register skill with tags."""
        reg = registry.register(sample_descriptor, sample_handler, tags=["core", "io"])

        assert "core" in reg.tags
        assert "io" in reg.tags

    def test_list_by_tag(self, registry, sample_handler):
        """List skills by tag."""
        desc1 = SkillDescriptor(skill_id="skill.a", name="A", version="1.0.0")
        desc2 = SkillDescriptor(skill_id="skill.b", name="B", version="1.0.0")

        registry.register(desc1, sample_handler, tags=["io"])
        registry.register(desc2, sample_handler, tags=["compute"])

        io_skills = registry.list_by_tag("io")
        assert len(io_skills) == 1
        assert io_skills[0].skill_id == "skill.a"


# ============================================================================
# Test: Deregistration
# ============================================================================


class TestDeregistration:
    """Tests for skill deregistration."""

    def test_deregister_specific_version(self, registry, sample_handler):
        """Deregister specific version."""
        desc_v1 = SkillDescriptor(skill_id="skill.test", name="Test", version="1.0.0")
        desc_v2 = SkillDescriptor(skill_id="skill.test", name="Test", version="2.0.0")

        registry.register(desc_v1, sample_handler)
        registry.register(desc_v2, sample_handler)

        result = registry.deregister("skill.test", "1.0.0")

        assert result is True
        assert not registry.exists("skill.test", "1.0.0")
        assert registry.exists("skill.test", "2.0.0")

    def test_deregister_all_versions(self, registry, sample_handler):
        """Deregister all versions of a skill."""
        desc_v1 = SkillDescriptor(skill_id="skill.test", name="Test", version="1.0.0")
        desc_v2 = SkillDescriptor(skill_id="skill.test", name="Test", version="2.0.0")

        registry.register(desc_v1, sample_handler)
        registry.register(desc_v2, sample_handler)

        result = registry.deregister("skill.test")

        assert result is True
        assert not registry.exists("skill.test")

    def test_deregister_nonexistent(self, registry):
        """Deregistering nonexistent skill returns False."""
        result = registry.deregister("skill.nonexistent")
        assert result is False


# ============================================================================
# Test: Handler Access
# ============================================================================


class TestHandlerAccess:
    """Tests for handler retrieval."""

    def test_get_handler(self, registry, sample_descriptor, sample_handler):
        """Get handler for registered skill."""
        registry.register(sample_descriptor, sample_handler)

        handler = registry.get_handler("skill.test")
        assert handler is sample_handler

    def test_get_handler_missing(self, registry):
        """Get handler for missing skill returns None."""
        handler = registry.get_handler("skill.missing")
        assert handler is None

    @pytest.mark.asyncio
    async def test_handler_execution(self, registry, sample_descriptor, sample_handler):
        """Execute handler through registry."""
        registry.register(sample_descriptor, sample_handler)

        handler = registry.get_handler("skill.test")
        result = await handler({"key": "value"})

        assert result == {"processed": {"key": "value"}}


# ============================================================================
# Test: Persistence
# ============================================================================


class TestPersistence:
    """Tests for sqlite persistence layer."""

    def test_persist_registration(self, persistent_registry, sample_descriptor, sample_handler):
        """Registration is persisted to sqlite."""
        persistent_registry.register(sample_descriptor, sample_handler)

        # Check sqlite directly
        cursor = persistent_registry._db.execute(
            "SELECT skill_id, version FROM skills WHERE skill_id = ?", ("skill.test",)
        )
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == "skill.test"
        assert row[1] == "1.0.0"

    def test_persist_deregistration(self, persistent_registry, sample_descriptor, sample_handler):
        """Deregistration removes from sqlite."""
        persistent_registry.register(sample_descriptor, sample_handler)
        persistent_registry.deregister("skill.test")

        cursor = persistent_registry._db.execute("SELECT * FROM skills WHERE skill_id = ?", ("skill.test",))
        row = cursor.fetchone()

        assert row is None


# ============================================================================
# Test: Manifest
# ============================================================================


class TestManifest:
    """Tests for skill manifest generation."""

    def test_get_manifest(self, registry, sample_handler):
        """Get manifest for planner."""
        desc = SkillDescriptor(skill_id="skill.test", name="Test", version="1.0.0", cost_model={"base_cents": 5})
        registry.register(desc, sample_handler, tags=["core"])

        manifest = registry.get_manifest()

        assert len(manifest) == 1
        assert manifest[0]["skill_id"] == "skill.test"
        assert manifest[0]["cost_model"]["base_cents"] == 5
        assert "core" in manifest[0]["tags"]


# ============================================================================
# Test: Global Registry
# ============================================================================


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def test_get_global_registry(self):
        """Global registry is created on first access."""
        reg = get_global_registry()
        assert reg is not None

    def test_set_global_registry(self):
        """Can replace global registry."""
        new_reg = SkillRegistry()
        set_global_registry(new_reg)

        assert get_global_registry() is new_reg

    def test_register_skill_helper(self, sample_descriptor, sample_handler):
        """register_skill helper uses global registry."""
        # Set up fresh global registry
        set_global_registry(SkillRegistry())

        reg = register_skill(sample_descriptor, sample_handler)

        assert reg.skill_id == "skill.test"
        assert get_global_registry().exists("skill.test")

    def test_get_skill_handler_helper(self, sample_descriptor, sample_handler):
        """get_skill_handler helper uses global registry."""
        set_global_registry(SkillRegistry())
        register_skill(sample_descriptor, sample_handler)

        handler = get_skill_handler("skill.test")
        assert handler is sample_handler


# ============================================================================
# Test: Listing
# ============================================================================


class TestListing:
    """Tests for skill listing."""

    def test_list_skills(self, registry, sample_handler):
        """List all registered skills."""
        desc1 = SkillDescriptor(skill_id="skill.a", name="A", version="1.0.0")
        desc2 = SkillDescriptor(skill_id="skill.b", name="B", version="1.0.0")

        registry.register(desc1, sample_handler)
        registry.register(desc2, sample_handler)

        skills = registry.list()
        skill_ids = [s.skill_id for s in skills]

        assert "skill.a" in skill_ids
        assert "skill.b" in skill_ids

    def test_list_all_versions(self, registry, sample_handler):
        """List all versions of all skills."""
        desc_v1 = SkillDescriptor(skill_id="skill.test", name="Test", version="1.0.0")
        desc_v2 = SkillDescriptor(skill_id="skill.test", name="Test", version="2.0.0")

        registry.register(desc_v1, sample_handler)
        registry.register(desc_v2, sample_handler)

        all_versions = registry.list_all_versions()
        assert len(all_versions) == 2

    def test_get_all_skill_ids(self, registry, sample_handler):
        """Get list of all skill IDs."""
        desc1 = SkillDescriptor(skill_id="skill.a", name="A", version="1.0.0")
        desc2 = SkillDescriptor(skill_id="skill.b", name="B", version="1.0.0")

        registry.register(desc1, sample_handler)
        registry.register(desc2, sample_handler)

        ids = registry.get_all_skill_ids()
        assert "skill.a" in ids
        assert "skill.b" in ids
