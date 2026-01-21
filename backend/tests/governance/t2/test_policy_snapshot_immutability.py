# Layer: L8 — Catalyst/Meta
# Product: system-wide
# Reference: GAP-029 (Policy snapshot immutability)
"""
Tests for Policy Snapshot Immutability (GAP-029).

Verifies that policy snapshots are truly immutable once created.
"""

import pytest
from datetime import datetime, timezone


class TestPolicySnapshotImports:
    """Test that all components are properly exported."""

    def test_status_import(self):
        """SnapshotStatus should be importable."""
        from app.services.policy import SnapshotStatus
        assert SnapshotStatus.ACTIVE == "active"

    def test_violation_import(self):
        """ImmutabilityViolation should be importable."""
        from app.services.policy import ImmutabilityViolation
        assert ImmutabilityViolation.CONTENT_MODIFICATION == "content_modification"

    def test_snapshot_data_import(self):
        """PolicySnapshotData should be importable."""
        from app.services.policy import PolicySnapshotData
        assert PolicySnapshotData is not None

    def test_registry_import(self):
        """PolicySnapshotRegistry should be importable."""
        from app.services.policy import PolicySnapshotRegistry
        registry = PolicySnapshotRegistry()
        assert registry is not None

    def test_error_import(self):
        """PolicySnapshotError should be importable."""
        from app.services.policy import PolicySnapshotError
        error = PolicySnapshotError("test")
        assert str(error) == "test"

    def test_stats_import(self):
        """SnapshotRegistryStats should be importable."""
        from app.services.policy import SnapshotRegistryStats
        stats = SnapshotRegistryStats()
        assert stats.total_snapshots == 0


class TestPolicySnapshotData:
    """Test PolicySnapshotData dataclass."""

    def test_snapshot_creation(self):
        """Snapshot should be created with required fields."""
        from app.services.policy.snapshot_service import PolicySnapshotData

        snapshot = PolicySnapshotData(
            snapshot_id="SNAP-test-123",
            tenant_id="tenant-1",
            version=1,
            policies_json='[{"rule": "test"}]',
            thresholds_json='{"max_tokens": 1000}',
            content_hash="abc123",
            threshold_hash="def456",
            policy_count=1,
        )

        assert snapshot.snapshot_id == "SNAP-test-123"
        assert snapshot.tenant_id == "tenant-1"
        assert snapshot.version == 1
        assert snapshot.is_sealed is True

    def test_is_sealed_always_true(self):
        """Snapshots should always be sealed after creation."""
        from app.services.policy.snapshot_service import PolicySnapshotData

        snapshot = PolicySnapshotData(
            snapshot_id="SNAP-test",
            tenant_id="tenant-1",
            version=1,
            policies_json="[]",
            thresholds_json="{}",
            content_hash="hash",
            threshold_hash="hash",
            policy_count=0,
        )

        assert snapshot.is_sealed is True

    def test_compute_hash(self):
        """Hash computation should be deterministic."""
        from app.services.policy.snapshot_service import PolicySnapshotData

        hash1 = PolicySnapshotData.compute_hash("test content")
        hash2 = PolicySnapshotData.compute_hash("test content")
        hash3 = PolicySnapshotData.compute_hash("different content")

        assert hash1 == hash2
        assert hash1 != hash3

    def test_verify_integrity_valid(self):
        """Integrity verification should pass for valid snapshot."""
        from app.services.policy.snapshot_service import PolicySnapshotData

        policies_json = '[{"rule": "test"}]'
        thresholds_json = '{"max_tokens": 1000}'
        content_hash = PolicySnapshotData.compute_hash(
            policies_json + thresholds_json
        )

        snapshot = PolicySnapshotData(
            snapshot_id="SNAP-test",
            tenant_id="tenant-1",
            version=1,
            policies_json=policies_json,
            thresholds_json=thresholds_json,
            content_hash=content_hash,
            threshold_hash=PolicySnapshotData.compute_hash(thresholds_json),
            policy_count=1,
        )

        assert snapshot.verify_integrity() is True

    def test_verify_integrity_invalid(self):
        """Integrity verification should fail for tampered snapshot."""
        from app.services.policy.snapshot_service import PolicySnapshotData

        snapshot = PolicySnapshotData(
            snapshot_id="SNAP-test",
            tenant_id="tenant-1",
            version=1,
            policies_json='[{"rule": "test"}]',
            thresholds_json='{"max_tokens": 1000}',
            content_hash="wrong_hash",
            threshold_hash="wrong_hash",
            policy_count=1,
        )

        assert snapshot.verify_integrity() is False

    def test_get_policies(self):
        """Policies should be deserializable."""
        from app.services.policy.snapshot_service import PolicySnapshotData

        snapshot = PolicySnapshotData(
            snapshot_id="SNAP-test",
            tenant_id="tenant-1",
            version=1,
            policies_json='[{"rule": "test", "enabled": true}]',
            thresholds_json="{}",
            content_hash="hash",
            threshold_hash="hash",
            policy_count=1,
        )

        policies = snapshot.get_policies()
        assert len(policies) == 1
        assert policies[0]["rule"] == "test"

    def test_get_thresholds(self):
        """Thresholds should be deserializable."""
        from app.services.policy.snapshot_service import PolicySnapshotData

        snapshot = PolicySnapshotData(
            snapshot_id="SNAP-test",
            tenant_id="tenant-1",
            version=1,
            policies_json="[]",
            thresholds_json='{"max_tokens": 1000, "max_cost": 50}',
            content_hash="hash",
            threshold_hash="hash",
            policy_count=0,
        )

        thresholds = snapshot.get_thresholds()
        assert thresholds["max_tokens"] == 1000
        assert thresholds["max_cost"] == 50

    def test_to_dict(self):
        """Snapshot should serialize to dict."""
        from app.services.policy.snapshot_service import PolicySnapshotData, SnapshotStatus

        snapshot = PolicySnapshotData(
            snapshot_id="SNAP-test",
            tenant_id="tenant-1",
            version=1,
            policies_json="[]",
            thresholds_json="{}",
            content_hash=PolicySnapshotData.compute_hash("[]{}"),
            threshold_hash=PolicySnapshotData.compute_hash("{}"),
            policy_count=0,
            status=SnapshotStatus.ACTIVE,
        )
        result = snapshot.to_dict()

        assert result["snapshot_id"] == "SNAP-test"
        assert result["version"] == 1
        assert result["is_sealed"] is True
        assert result["integrity_valid"] is True


class TestPolicySnapshotRegistry:
    """Test PolicySnapshotRegistry."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.policy.snapshot_service import _reset_snapshot_registry
        _reset_snapshot_registry()
        yield
        _reset_snapshot_registry()

    def test_registry_creation(self):
        """Registry should be created."""
        from app.services.policy import PolicySnapshotRegistry

        registry = PolicySnapshotRegistry()
        assert registry is not None

    def test_create_snapshot(self):
        """Creating a snapshot should work."""
        from app.services.policy import PolicySnapshotRegistry, SnapshotStatus

        registry = PolicySnapshotRegistry()
        snapshot = registry.create(
            tenant_id="tenant-1",
            policies=[{"rule": "test", "enabled": True}],
            thresholds={"max_tokens": 1000},
        )

        assert snapshot.snapshot_id is not None
        assert snapshot.tenant_id == "tenant-1"
        assert snapshot.version == 1
        assert snapshot.policy_count == 1
        assert snapshot.status == SnapshotStatus.ACTIVE
        assert snapshot.is_sealed is True

    def test_get_snapshot(self):
        """Getting a snapshot by ID should work."""
        from app.services.policy import PolicySnapshotRegistry

        registry = PolicySnapshotRegistry()
        snapshot = registry.create(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )

        retrieved = registry.get(snapshot.snapshot_id)
        assert retrieved is not None
        assert retrieved.snapshot_id == snapshot.snapshot_id

    def test_get_active_snapshot(self):
        """Getting active snapshot for tenant should work."""
        from app.services.policy import PolicySnapshotRegistry, SnapshotStatus

        registry = PolicySnapshotRegistry()
        registry.create(
            tenant_id="tenant-1",
            policies=[{"rule": "v1"}],
            thresholds={},
        )

        active = registry.get_active("tenant-1")
        assert active is not None
        assert active.status == SnapshotStatus.ACTIVE

    def test_version_incrementing(self):
        """Versions should increment for each tenant snapshot."""
        from app.services.policy import PolicySnapshotRegistry

        registry = PolicySnapshotRegistry()

        snapshot1 = registry.create(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )
        snapshot2 = registry.create(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )
        snapshot3 = registry.create(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )

        assert snapshot1.version == 1
        assert snapshot2.version == 2
        assert snapshot3.version == 3

    def test_automatic_supersession(self):
        """Creating new snapshot should supersede previous active."""
        from app.services.policy import PolicySnapshotRegistry, SnapshotStatus

        registry = PolicySnapshotRegistry()

        snapshot1 = registry.create(
            tenant_id="tenant-1",
            policies=[{"rule": "v1"}],
            thresholds={},
        )
        snapshot2 = registry.create(
            tenant_id="tenant-1",
            policies=[{"rule": "v2"}],
            thresholds={},
        )

        # Check first snapshot is superseded
        assert snapshot1.status == SnapshotStatus.SUPERSEDED
        assert snapshot1.superseded_by == snapshot2.snapshot_id
        assert snapshot1.superseded_at is not None

        # Check second snapshot is active
        assert snapshot2.status == SnapshotStatus.ACTIVE

    def test_immutability_content_modification_blocked(self):
        """Attempting to modify snapshot content should fail."""
        from app.services.policy import (
            PolicySnapshotRegistry,
            PolicySnapshotError,
            ImmutabilityViolation,
        )

        registry = PolicySnapshotRegistry()
        snapshot = registry.create(
            tenant_id="tenant-1",
            policies=[{"rule": "original"}],
            thresholds={},
        )

        with pytest.raises(PolicySnapshotError) as exc_info:
            registry.attempt_modify(
                snapshot.snapshot_id,
                policies=[{"rule": "modified"}],
            )

        assert exc_info.value.violation_type == ImmutabilityViolation.CONTENT_MODIFICATION
        assert "immutable" in str(exc_info.value).lower()

    def test_immutability_deletion_of_active_blocked(self):
        """Deleting active snapshot should be blocked."""
        from app.services.policy import (
            PolicySnapshotRegistry,
            PolicySnapshotError,
            ImmutabilityViolation,
        )

        registry = PolicySnapshotRegistry()
        snapshot = registry.create(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )

        with pytest.raises(PolicySnapshotError) as exc_info:
            registry.delete(snapshot.snapshot_id)

        assert exc_info.value.violation_type == ImmutabilityViolation.DELETION_BLOCKED

    def test_archive_superseded_snapshot(self):
        """Archiving superseded snapshot should work."""
        from app.services.policy import PolicySnapshotRegistry, SnapshotStatus

        registry = PolicySnapshotRegistry()

        snapshot1 = registry.create(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )
        registry.create(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )

        # First snapshot should now be superseded
        assert snapshot1.status == SnapshotStatus.SUPERSEDED

        # Archive the superseded snapshot
        archived = registry.archive(snapshot1.snapshot_id)
        assert archived.status == SnapshotStatus.ARCHIVED

    def test_archive_active_blocked(self):
        """Archiving active snapshot should be blocked."""
        from app.services.policy import PolicySnapshotRegistry, PolicySnapshotError

        registry = PolicySnapshotRegistry()
        snapshot = registry.create(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )

        with pytest.raises(PolicySnapshotError):
            registry.archive(snapshot.snapshot_id)

    def test_delete_archived_snapshot(self):
        """Deleting archived snapshot should work."""
        from app.services.policy import PolicySnapshotRegistry, SnapshotStatus

        registry = PolicySnapshotRegistry()

        snapshot1 = registry.create(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )
        registry.create(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )

        # Archive and then delete
        registry.archive(snapshot1.snapshot_id)
        result = registry.delete(snapshot1.snapshot_id)

        assert result is True
        assert registry.get(snapshot1.snapshot_id) is None

    def test_get_by_version(self):
        """Getting snapshot by version should work."""
        from app.services.policy import PolicySnapshotRegistry

        registry = PolicySnapshotRegistry()

        registry.create(
            tenant_id="tenant-1",
            policies=[{"rule": "v1"}],
            thresholds={},
        )
        registry.create(
            tenant_id="tenant-1",
            policies=[{"rule": "v2"}],
            thresholds={},
        )

        snapshot_v1 = registry.get_by_version("tenant-1", 1)
        snapshot_v2 = registry.get_by_version("tenant-1", 2)

        assert snapshot_v1 is not None
        assert snapshot_v1.version == 1
        assert snapshot_v2 is not None
        assert snapshot_v2.version == 2

    def test_list_by_tenant(self):
        """Listing snapshots by tenant should work."""
        from app.services.policy import PolicySnapshotRegistry

        registry = PolicySnapshotRegistry()

        for i in range(3):
            registry.create(
                tenant_id="tenant-1",
                policies=[{"rule": f"v{i}"}],
                thresholds={},
            )
        registry.create(
            tenant_id="tenant-2",
            policies=[],
            thresholds={},
        )

        tenant1_snapshots = registry.list(tenant_id="tenant-1")
        tenant2_snapshots = registry.list(tenant_id="tenant-2")

        assert len(tenant1_snapshots) == 3
        assert len(tenant2_snapshots) == 1

    def test_list_by_status(self):
        """Listing snapshots by status should work."""
        from app.services.policy import PolicySnapshotRegistry, SnapshotStatus

        registry = PolicySnapshotRegistry()

        # Create multiple snapshots (only last is active)
        for i in range(3):
            registry.create(
                tenant_id="tenant-1",
                policies=[{"rule": f"v{i}"}],
                thresholds={},
            )

        active = registry.list(status=SnapshotStatus.ACTIVE)
        superseded = registry.list(status=SnapshotStatus.SUPERSEDED)

        assert len(active) == 1
        assert len(superseded) == 2

    def test_get_history(self):
        """Getting version history should work."""
        from app.services.policy import PolicySnapshotRegistry

        registry = PolicySnapshotRegistry()

        for i in range(5):
            registry.create(
                tenant_id="tenant-1",
                policies=[{"rule": f"v{i}"}],
                thresholds={"max_tokens": (i + 1) * 1000},
            )

        history = registry.get_history("tenant-1")

        assert len(history) == 5
        # Should be sorted by version descending
        assert history[0].version == 5
        assert history[4].version == 1

    def test_verify_snapshot_integrity(self):
        """Verifying snapshot integrity should work."""
        from app.services.policy import PolicySnapshotRegistry

        registry = PolicySnapshotRegistry()
        snapshot = registry.create(
            tenant_id="tenant-1",
            policies=[{"rule": "test"}],
            thresholds={"max_tokens": 1000},
        )

        result = registry.verify(snapshot.snapshot_id)

        assert result["is_valid"] is True
        assert result["content_integrity"] is True
        assert result["threshold_integrity"] is True

    def test_get_statistics(self):
        """Getting statistics should work."""
        from app.services.policy import PolicySnapshotRegistry

        registry = PolicySnapshotRegistry()

        # Create snapshots for multiple tenants
        for i in range(3):
            registry.create(
                tenant_id="tenant-1",
                policies=[],
                thresholds={},
            )
        registry.create(
            tenant_id="tenant-2",
            policies=[],
            thresholds={},
        )

        stats = registry.get_statistics()

        assert stats.total_snapshots == 4
        assert stats.active_snapshots == 2  # One per tenant
        assert stats.superseded_snapshots == 2
        assert stats.tenants_with_snapshots == 2

    def test_clear_tenant(self):
        """Clearing archived tenant snapshots should work."""
        from app.services.policy import PolicySnapshotRegistry

        registry = PolicySnapshotRegistry()

        # Create and supersede snapshots
        for i in range(3):
            registry.create(
                tenant_id="tenant-1",
                policies=[],
                thresholds={},
            )

        # Archive superseded snapshots
        history = registry.get_history("tenant-1")
        for snapshot in history:
            if snapshot.version < 3:
                registry.archive(snapshot.snapshot_id)

        # Clear archived
        cleared = registry.clear_tenant("tenant-1")

        assert cleared == 2
        remaining = registry.list(tenant_id="tenant-1")
        assert len(remaining) == 1

    def test_tenant_isolation(self):
        """Snapshots should be isolated by tenant."""
        from app.services.policy import PolicySnapshotRegistry

        registry = PolicySnapshotRegistry()

        snapshot1 = registry.create(
            tenant_id="tenant-1",
            policies=[{"rule": "t1"}],
            thresholds={},
        )
        snapshot2 = registry.create(
            tenant_id="tenant-2",
            policies=[{"rule": "t2"}],
            thresholds={},
        )

        # Version numbers should be independent
        assert snapshot1.version == 1
        assert snapshot2.version == 1

        # Active snapshots should be different
        active1 = registry.get_active("tenant-1")
        active2 = registry.get_active("tenant-2")

        assert active1.snapshot_id != active2.snapshot_id

    def test_content_hash_uniqueness(self):
        """Different content should produce different hashes."""
        from app.services.policy import PolicySnapshotRegistry

        registry = PolicySnapshotRegistry()

        snapshot1 = registry.create(
            tenant_id="tenant-1",
            policies=[{"rule": "v1"}],
            thresholds={"max": 100},
        )
        snapshot2 = registry.create(
            tenant_id="tenant-2",
            policies=[{"rule": "v2"}],
            thresholds={"max": 200},
        )

        assert snapshot1.content_hash != snapshot2.content_hash


class TestHelperFunctions:
    """Test module-level helper functions."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.policy.snapshot_service import _reset_snapshot_registry
        _reset_snapshot_registry()
        yield
        _reset_snapshot_registry()

    def test_create_policy_snapshot(self):
        """create_policy_snapshot should use singleton."""
        from app.services.policy import create_policy_snapshot

        snapshot = create_policy_snapshot(
            tenant_id="tenant-1",
            policies=[{"rule": "test"}],
            thresholds={"max_tokens": 1000},
        )

        assert snapshot.snapshot_id is not None
        assert snapshot.is_sealed is True

    def test_get_policy_snapshot(self):
        """get_policy_snapshot should use singleton."""
        from app.services.policy import (
            create_policy_snapshot,
            get_policy_snapshot,
        )

        snapshot = create_policy_snapshot(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )

        retrieved = get_policy_snapshot(snapshot.snapshot_id)
        assert retrieved is not None

    def test_get_active_snapshot(self):
        """get_active_snapshot should use singleton."""
        from app.services.policy import (
            create_policy_snapshot,
            get_active_snapshot,
        )

        create_policy_snapshot(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )

        active = get_active_snapshot("tenant-1")
        assert active is not None

    def test_get_snapshot_history(self):
        """get_snapshot_history should use singleton."""
        from app.services.policy import (
            create_policy_snapshot,
            get_snapshot_history,
        )

        for i in range(3):
            create_policy_snapshot(
                tenant_id="tenant-1",
                policies=[{"version": i}],
                thresholds={},
            )

        history = get_snapshot_history("tenant-1")
        assert len(history) == 3

    def test_verify_snapshot(self):
        """verify_snapshot should use singleton."""
        from app.services.policy import (
            create_policy_snapshot,
            verify_snapshot,
        )

        snapshot = create_policy_snapshot(
            tenant_id="tenant-1",
            policies=[{"rule": "test"}],
            thresholds={"max": 100},
        )

        result = verify_snapshot(snapshot.snapshot_id)
        assert result["is_valid"] is True

    def test_get_snapshot_registry(self):
        """get_snapshot_registry should return singleton."""
        from app.services.policy import get_snapshot_registry

        registry1 = get_snapshot_registry()
        registry2 = get_snapshot_registry()
        assert registry1 is registry2


class TestImmutabilityEnforcement:
    """Test comprehensive immutability enforcement."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.policy.snapshot_service import _reset_snapshot_registry
        _reset_snapshot_registry()
        yield
        _reset_snapshot_registry()

    def test_no_content_modification_after_creation(self):
        """Content should be immutable after creation."""
        from app.services.policy import (
            PolicySnapshotRegistry,
            PolicySnapshotError,
        )

        registry = PolicySnapshotRegistry()
        snapshot = registry.create(
            tenant_id="tenant-1",
            policies=[{"original": True}],
            thresholds={"max": 100},
        )

        # Direct attribute access should be possible but modification
        # attempts via the registry should fail
        with pytest.raises(PolicySnapshotError):
            registry.attempt_modify(
                snapshot.snapshot_id,
                policies=[{"modified": True}],
            )

    def test_status_transitions_are_restricted(self):
        """Only allowed status transitions should work."""
        from app.services.policy import (
            PolicySnapshotRegistry,
            PolicySnapshotError,
            SnapshotStatus,
        )

        registry = PolicySnapshotRegistry()

        # Create and supersede a snapshot
        snapshot1 = registry.create(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )
        registry.create(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )

        assert snapshot1.status == SnapshotStatus.SUPERSEDED

        # Archive should work (SUPERSEDED -> ARCHIVED)
        registry.archive(snapshot1.snapshot_id)
        assert snapshot1.status == SnapshotStatus.ARCHIVED

        # Further transition should fail (ARCHIVED is terminal)
        with pytest.raises(PolicySnapshotError):
            registry.archive(snapshot1.snapshot_id)

    def test_integrity_violations_mark_as_invalid(self):
        """Integrity check failures should mark snapshot as invalid."""
        from app.services.policy.snapshot_service import (
            PolicySnapshotData,
            PolicySnapshotRegistry,
            SnapshotStatus,
        )

        registry = PolicySnapshotRegistry()
        snapshot = registry.create(
            tenant_id="tenant-1",
            policies=[{"rule": "test"}],
            thresholds={},
        )

        # Tamper with the hash (simulating corruption)
        snapshot.content_hash = "tampered_hash"

        # Verify should detect and mark as invalid
        result = registry.verify(snapshot.snapshot_id)

        assert result["is_valid"] is False
        assert snapshot.status == SnapshotStatus.INVALID

    def test_error_contains_violation_type(self):
        """Errors should contain specific violation type."""
        from app.services.policy import (
            PolicySnapshotRegistry,
            PolicySnapshotError,
            ImmutabilityViolation,
        )

        registry = PolicySnapshotRegistry()
        snapshot = registry.create(
            tenant_id="tenant-1",
            policies=[],
            thresholds={},
        )

        try:
            registry.attempt_modify(snapshot.snapshot_id)
        except PolicySnapshotError as e:
            assert e.violation_type == ImmutabilityViolation.CONTENT_MODIFICATION
            error_dict = e.to_dict()
            assert error_dict["violation_type"] == "content_modification"


class TestPolicySnapshotError:
    """Test PolicySnapshotError exception."""

    def test_error_creation(self):
        """Error should be created with message."""
        from app.services.policy import PolicySnapshotError

        error = PolicySnapshotError("Something failed")
        assert str(error) == "Something failed"

    def test_error_with_snapshot_id(self):
        """Error should store snapshot ID."""
        from app.services.policy import PolicySnapshotError

        error = PolicySnapshotError(
            "Failed",
            snapshot_id="SNAP-123",
        )
        assert error.snapshot_id == "SNAP-123"

    def test_error_with_violation_type(self):
        """Error should store violation type."""
        from app.services.policy import (
            PolicySnapshotError,
            ImmutabilityViolation,
        )

        error = PolicySnapshotError(
            "Blocked",
            violation_type=ImmutabilityViolation.DELETION_BLOCKED,
        )
        assert error.violation_type == ImmutabilityViolation.DELETION_BLOCKED

    def test_error_to_dict(self):
        """Error should serialize to dict."""
        from app.services.policy import (
            PolicySnapshotError,
            ImmutabilityViolation,
        )

        error = PolicySnapshotError(
            "Content modification blocked",
            snapshot_id="SNAP-123",
            violation_type=ImmutabilityViolation.CONTENT_MODIFICATION,
        )
        result = error.to_dict()

        assert result["error"] == "Content modification blocked"
        assert result["snapshot_id"] == "SNAP-123"
        assert result["violation_type"] == "content_modification"


class TestSnapshotRegistryStats:
    """Test SnapshotRegistryStats dataclass."""

    def test_default_values(self):
        """Default values should be zero."""
        from app.services.policy import SnapshotRegistryStats

        stats = SnapshotRegistryStats()
        assert stats.total_snapshots == 0
        assert stats.active_snapshots == 0
        assert stats.superseded_snapshots == 0
        assert stats.archived_snapshots == 0
        assert stats.invalid_snapshots == 0

    def test_to_dict(self):
        """Stats should serialize to dict."""
        from app.services.policy import SnapshotRegistryStats

        stats = SnapshotRegistryStats(
            total_snapshots=10,
            active_snapshots=3,
            superseded_snapshots=5,
            archived_snapshots=2,
        )
        result = stats.to_dict()

        assert result["total_snapshots"] == 10
        assert result["active_snapshots"] == 3
        assert result["superseded_snapshots"] == 5
        assert result["archived_snapshots"] == 2
