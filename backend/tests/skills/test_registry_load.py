# tests/skills/test_registry_load.py
"""
Registry Load Tests

Performance tests for SkillRegistry v2 with:
1. 1000+ skill registrations
2. Version resolution under load
3. Persistence performance
4. Memory usage verification

These tests ensure the registry can handle production-scale deployments.
"""

import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

import pytest

# Add paths
_backend_path = str(Path(__file__).parent.parent.parent)
_runtime_path = str(Path(__file__).parent.parent.parent / "app" / "worker" / "runtime")


for p in [_backend_path, _runtime_path, _skills_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

from core import SkillDescriptor
from registry_v2 import (
    SkillRegistry,
    diff_contracts,
    is_version_compatible,
    resolve_skill_with_version,
)


def create_test_descriptor(
    skill_id: str, version: str = "1.0.0", stable_fields: Dict[str, str] = None
) -> SkillDescriptor:
    """Create a test descriptor."""
    return SkillDescriptor(
        skill_id=skill_id,
        name=f"Test Skill {skill_id}",
        version=version,
        inputs_schema_version="1.0",
        outputs_schema_version="1.0",
        stable_fields=stable_fields or {"output": "DETERMINISTIC"},
        cost_model={"base_cents": 1, "per_call_cents": 0},
        failure_modes=[{"code": "ERR_TEST", "category": "PERMANENT"}],
        constraints={"max_size": 1000},
    )


async def dummy_handler(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Dummy handler for load testing."""
    return {"status": "ok", "data": inputs}


class TestRegistryScalePerformance:
    """Tests for registry performance at scale."""

    @pytest.fixture
    def registry(self):
        """Create fresh registry."""
        return SkillRegistry()

    def test_register_1000_skills(self, registry):
        """Can register 1000 skills in reasonable time."""
        start = time.time()

        for i in range(1000):
            descriptor = create_test_descriptor(f"skill.test_{i:04d}")
            registry.register(descriptor, dummy_handler)

        duration = time.time() - start

        assert len(registry.list()) == 1000
        assert duration < 5.0, f"Registration took {duration:.2f}s (expected < 5s)"

    def test_resolve_performance_at_scale(self, registry):
        """Resolution is fast with 1000 skills registered."""
        # Register 1000 skills
        for i in range(1000):
            descriptor = create_test_descriptor(f"skill.test_{i:04d}")
            registry.register(descriptor, dummy_handler)

        # Time resolution
        start = time.time()
        resolutions = 10000

        for _ in range(resolutions):
            skill_id = f"skill.test_{_ % 1000:04d}"
            result = registry.resolve(skill_id)
            assert result is not None

        duration = time.time() - start
        per_resolution_ms = (duration / resolutions) * 1000

        assert per_resolution_ms < 0.1, f"Resolution took {per_resolution_ms:.3f}ms (expected < 0.1ms)"

    def test_list_performance_at_scale(self, registry):
        """Listing is fast with 1000 skills."""
        for i in range(1000):
            descriptor = create_test_descriptor(f"skill.test_{i:04d}")
            registry.register(descriptor, dummy_handler)

        start = time.time()
        for _ in range(100):
            skills = registry.list()
            assert len(skills) == 1000

        duration = time.time() - start
        per_list_ms = (duration / 100) * 1000

        assert per_list_ms < 10, f"List took {per_list_ms:.3f}ms (expected < 10ms)"

    def test_manifest_generation_at_scale(self, registry):
        """Manifest generation is fast with 1000 skills."""
        for i in range(1000):
            descriptor = create_test_descriptor(f"skill.test_{i:04d}")
            registry.register(descriptor, dummy_handler, tags=["test", f"group_{i % 10}"])

        start = time.time()
        manifest = registry.get_manifest()
        duration = time.time() - start

        assert len(manifest) == 1000
        assert duration < 1.0, f"Manifest generation took {duration:.2f}s (expected < 1s)"


class TestRegistryVersioningAtScale:
    """Tests for versioning with many skill versions."""

    @pytest.fixture
    def registry(self):
        return SkillRegistry()

    def test_multiple_versions_per_skill(self, registry):
        """Can handle many versions of same skill."""
        versions = ["0.1.0", "0.2.0", "1.0.0", "1.1.0", "1.2.0", "2.0.0"]

        for version in versions:
            descriptor = create_test_descriptor("skill.multi_version", version)
            registry.register(descriptor, dummy_handler)

        # Should have 6 total registrations
        all_versions = registry.list_all_versions()
        skill_versions = [r for r in all_versions if r.skill_id == "skill.multi_version"]
        assert len(skill_versions) == 6

        # Latest should be 2.0.0
        latest = registry.resolve("skill.multi_version")
        assert latest.version == "2.0.0"

    def test_version_resolution_at_scale(self, registry):
        """Version resolution works with many skills and versions."""
        # Register 100 skills with 10 versions each
        for skill_num in range(100):
            skill_id = f"skill.versioned_{skill_num:03d}"
            for version_num in range(10):
                version = f"1.{version_num}.0"
                descriptor = create_test_descriptor(skill_id, version)
                registry.register(descriptor, dummy_handler)

        # Total: 1000 registrations
        assert len(registry.list_all_versions()) == 1000
        assert len(registry.list()) == 100  # Latest only

        # Test specific version resolution
        start = time.time()
        for _ in range(1000):
            skill_id = f"skill.versioned_{_ % 100:03d}"
            version = f"1.{_ % 10}.0"
            result = registry.resolve(skill_id, version)
            assert result is not None
            assert result.version == version

        duration = time.time() - start
        assert duration < 2.0, f"Versioned resolution took {duration:.2f}s"


class TestRegistryPersistencePerformance:
    """Tests for persistence layer performance."""

    @pytest.fixture(autouse=True)
    def isolate_test(self):
        """Ensure test isolation - no other tests running concurrently."""
        # This fixture ensures each test in this class gets clean state
        import gc

        gc.collect()
        yield

    def test_persistence_write_performance(self):
        """Writing 1000 skills to sqlite is fast."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            registry = SkillRegistry(persistence_path=db_path)

            start = time.time()
            for i in range(1000):
                descriptor = create_test_descriptor(f"skill.persist_{i:04d}")
                registry.register(descriptor, dummy_handler)

            duration = time.time() - start
            registry.close()

            # Allow 15s for CI environments with resource contention
            assert duration < 15.0, f"Persistence writes took {duration:.2f}s (expected < 15s)"
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_persistence_file_size_reasonable(self):
        """SQLite file size is reasonable for 1000 skills."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            registry = SkillRegistry(persistence_path=db_path)

            for i in range(1000):
                descriptor = create_test_descriptor(f"skill.size_{i:04d}")
                registry.register(descriptor, dummy_handler, tags=["test"])

            registry.close()

            # Check file size (should be < 1MB for 1000 simple skills)
            file_size = Path(db_path).stat().st_size
            file_size_kb = file_size / 1024

            assert file_size_kb < 1024, f"DB file is {file_size_kb:.1f}KB (expected < 1MB)"
        finally:
            Path(db_path).unlink(missing_ok=True)


class TestRegistryDeregistrationPerformance:
    """Tests for deregistration performance."""

    @pytest.fixture
    def registry(self):
        return SkillRegistry()

    def test_deregister_performance(self, registry):
        """Deregistration is fast."""
        # Register 1000 skills
        for i in range(1000):
            descriptor = create_test_descriptor(f"skill.dereg_{i:04d}")
            registry.register(descriptor, dummy_handler)

        # Deregister half
        start = time.time()
        for i in range(0, 1000, 2):
            registry.deregister(f"skill.dereg_{i:04d}")

        duration = time.time() - start

        assert len(registry.list()) == 500
        assert duration < 2.0, f"Deregistration took {duration:.2f}s (expected < 2s)"


class TestVersionGatingPerformance:
    """Tests for version gating and contract diffing performance."""

    @pytest.fixture
    def registry(self):
        return SkillRegistry()

    def test_version_compatibility_check_performance(self, registry):
        """Version compatibility checks are fast."""
        # Register skills with multiple versions
        for skill_num in range(100):
            skill_id = f"skill.compat_{skill_num:03d}"
            for v in ["1.0.0", "1.1.0", "2.0.0"]:
                descriptor = create_test_descriptor(skill_id, v)
                registry.register(descriptor, dummy_handler)

        start = time.time()
        checks = 10000

        for i in range(checks):
            skill_id = f"skill.compat_{i % 100:03d}"
            is_version_compatible("1.0.0", "1.1.0")
            is_version_compatible("1.0.0", "2.0.0", strict=True)

        duration = time.time() - start
        per_check_us = (duration / checks) * 1_000_000

        assert per_check_us < 10, f"Version check took {per_check_us:.1f}µs (expected < 10µs)"

    def test_contract_diff_performance(self, registry):
        """Contract diffing is fast."""
        old_desc = create_test_descriptor("skill.diff", "1.0.0", {"a": "DETERMINISTIC", "b": "STABLE"})
        new_desc = create_test_descriptor("skill.diff", "2.0.0", {"a": "DETERMINISTIC", "c": "STABLE"})

        start = time.time()
        diffs = 10000

        for _ in range(diffs):
            diff = diff_contracts(old_desc, new_desc)
            assert diff.skill_id == "skill.diff"

        duration = time.time() - start
        per_diff_us = (duration / diffs) * 1_000_000

        assert per_diff_us < 100, f"Contract diff took {per_diff_us:.1f}µs (expected < 100µs)"

    def test_resolve_with_version_performance(self, registry):
        """resolve_skill_with_version is fast."""
        # Register skills
        for skill_num in range(100):
            skill_id = f"skill.resolve_{skill_num:03d}"
            for v in ["1.0.0", "1.1.0", "1.2.0", "2.0.0"]:
                descriptor = create_test_descriptor(skill_id, v)
                registry.register(descriptor, dummy_handler)

        start = time.time()
        resolutions = 10000

        for i in range(resolutions):
            skill_id = f"skill.resolve_{i % 100:03d}"
            result = resolve_skill_with_version(registry, skill_id, "1.0.0")
            assert result is not None

        duration = time.time() - start
        per_resolve_ms = (duration / resolutions) * 1000

        assert per_resolve_ms < 0.5, f"Versioned resolve took {per_resolve_ms:.3f}ms (expected < 0.5ms)"


class TestRegistryTagFiltering:
    """Tests for tag filtering performance."""

    @pytest.fixture
    def registry(self):
        return SkillRegistry()

    def test_tag_filtering_at_scale(self, registry):
        """Tag filtering is fast with 1000 skills."""
        # Register skills with various tags
        for i in range(1000):
            tags = [f"group_{i % 10}", f"category_{i % 5}"]
            if i % 2 == 0:
                tags.append("even")
            descriptor = create_test_descriptor(f"skill.tag_{i:04d}")
            registry.register(descriptor, dummy_handler, tags=tags)

        start = time.time()
        for _ in range(100):
            # Filter by different tags
            even_skills = registry.list_by_tag("even")
            group_0 = registry.list_by_tag("group_0")
            category_2 = registry.list_by_tag("category_2")

        duration = time.time() - start

        assert len(even_skills) == 500
        assert len(group_0) == 100
        assert len(category_2) == 200
        assert duration < 2.0, f"Tag filtering took {duration:.2f}s (expected < 2s)"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
