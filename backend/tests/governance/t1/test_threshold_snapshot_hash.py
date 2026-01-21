# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-022 (Threshold Snapshot Hash)
"""
Unit tests for GAP-022: Threshold Snapshot Hash.

Tests the independent threshold hash computation for SOC2 audit compliance.
"""

import pytest
import hashlib
import json


class TestThresholdSnapshotHash:
    """Test suite for threshold_snapshot_hash (GAP-022)."""

    def test_policy_snapshot_has_threshold_hash_field(self):
        """PolicySnapshot should have threshold_snapshot_hash field."""
        from app.models.policy_snapshot import PolicySnapshot

        # Check field exists
        assert hasattr(PolicySnapshot, "threshold_snapshot_hash")

    def test_create_snapshot_computes_threshold_hash(self):
        """create_snapshot should compute threshold_snapshot_hash."""
        from app.models.policy_snapshot import PolicySnapshot

        policies = [{"id": "pol-1", "name": "Test Policy"}]
        thresholds = {"max_tokens": 1000, "max_cost_cents": 500}

        snapshot = PolicySnapshot.create_snapshot(
            tenant_id="tenant-001",
            policies=policies,
            thresholds=thresholds,
        )

        assert snapshot.threshold_snapshot_hash is not None
        assert len(snapshot.threshold_snapshot_hash) == 64  # SHA256 hex

    def test_threshold_hash_computed_from_thresholds_only(self):
        """threshold_snapshot_hash should be computed from thresholds_json only."""
        from app.models.policy_snapshot import PolicySnapshot

        thresholds = {"max_tokens": 1000, "max_cost_cents": 500}
        thresholds_json = json.dumps(thresholds, sort_keys=True, default=str)
        expected_hash = hashlib.sha256(thresholds_json.encode()).hexdigest()

        snapshot = PolicySnapshot.create_snapshot(
            tenant_id="tenant-001",
            policies=[{"id": "pol-1"}],
            thresholds=thresholds,
        )

        assert snapshot.threshold_snapshot_hash == expected_hash

    def test_threshold_hash_independent_of_policies(self):
        """Two snapshots with same thresholds should have same threshold_hash."""
        from app.models.policy_snapshot import PolicySnapshot

        thresholds = {"max_tokens": 1000}

        snapshot1 = PolicySnapshot.create_snapshot(
            tenant_id="tenant-001",
            policies=[{"id": "pol-1", "name": "Policy A"}],
            thresholds=thresholds,
        )

        snapshot2 = PolicySnapshot.create_snapshot(
            tenant_id="tenant-001",
            policies=[{"id": "pol-2", "name": "Policy B"}],
            thresholds=thresholds,
        )

        # Different content_hash (policies differ)
        assert snapshot1.content_hash != snapshot2.content_hash

        # Same threshold_hash (thresholds same)
        assert snapshot1.threshold_snapshot_hash == snapshot2.threshold_snapshot_hash

    def test_threshold_hash_changes_when_thresholds_change(self):
        """threshold_snapshot_hash should change when thresholds change."""
        from app.models.policy_snapshot import PolicySnapshot

        policies = [{"id": "pol-1"}]

        snapshot1 = PolicySnapshot.create_snapshot(
            tenant_id="tenant-001",
            policies=policies,
            thresholds={"max_tokens": 1000},
        )

        snapshot2 = PolicySnapshot.create_snapshot(
            tenant_id="tenant-001",
            policies=policies,
            thresholds={"max_tokens": 2000},  # Changed
        )

        assert snapshot1.threshold_snapshot_hash != snapshot2.threshold_snapshot_hash

    def test_verify_threshold_integrity_success(self):
        """verify_threshold_integrity should return True for valid snapshot."""
        from app.models.policy_snapshot import PolicySnapshot

        snapshot = PolicySnapshot.create_snapshot(
            tenant_id="tenant-001",
            policies=[{"id": "pol-1"}],
            thresholds={"max_tokens": 1000},
        )

        assert snapshot.verify_threshold_integrity() is True

    def test_verify_threshold_integrity_backward_compatible(self):
        """verify_threshold_integrity should return True if hash is None."""
        from app.models.policy_snapshot import PolicySnapshot

        # Simulate old snapshot without threshold_hash
        snapshot = PolicySnapshot(
            snapshot_id="SNAP-old",
            tenant_id="tenant-001",
            policies_json="[]",
            thresholds_json="{}",
            content_hash="abc123",
            threshold_snapshot_hash=None,  # Old snapshot
            policy_count=0,
        )

        # Should return True for backward compatibility
        assert snapshot.verify_threshold_integrity() is True

    def test_get_threshold_hash_returns_stored(self):
        """get_threshold_hash should return stored hash if present."""
        from app.models.policy_snapshot import PolicySnapshot

        snapshot = PolicySnapshot.create_snapshot(
            tenant_id="tenant-001",
            policies=[{"id": "pol-1"}],
            thresholds={"max_tokens": 1000},
        )

        assert snapshot.get_threshold_hash() == snapshot.threshold_snapshot_hash

    def test_get_threshold_hash_computes_if_missing(self):
        """get_threshold_hash should compute hash if not stored."""
        from app.models.policy_snapshot import PolicySnapshot

        thresholds = {"max_tokens": 1000}
        thresholds_json = json.dumps(thresholds, sort_keys=True, default=str)
        expected_hash = hashlib.sha256(thresholds_json.encode()).hexdigest()

        # Simulate old snapshot without threshold_hash
        snapshot = PolicySnapshot(
            snapshot_id="SNAP-old",
            tenant_id="tenant-001",
            policies_json="[]",
            thresholds_json=thresholds_json,
            content_hash="abc123",
            threshold_snapshot_hash=None,  # Old snapshot
            policy_count=0,
        )

        # Should compute on-the-fly
        assert snapshot.get_threshold_hash() == expected_hash


class TestPolicySnapshotResponse:
    """Test PolicySnapshotResponse model includes threshold fields."""

    def test_response_has_threshold_hash_field(self):
        """PolicySnapshotResponse should have threshold_snapshot_hash field."""
        from app.models.policy_snapshot import PolicySnapshotResponse

        # Check field exists in model
        assert "threshold_snapshot_hash" in PolicySnapshotResponse.model_fields

    def test_response_has_threshold_integrity_field(self):
        """PolicySnapshotResponse should have threshold_integrity_verified field."""
        from app.models.policy_snapshot import PolicySnapshotResponse

        assert "threshold_integrity_verified" in PolicySnapshotResponse.model_fields

    def test_response_creation(self):
        """PolicySnapshotResponse should be creatable with threshold fields."""
        from datetime import datetime, timezone
        from app.models.policy_snapshot import PolicySnapshotResponse

        response = PolicySnapshotResponse(
            snapshot_id="SNAP-abc123",
            tenant_id="tenant-001",
            policy_count=5,
            policy_version="v1.0",
            content_hash="abc123def456",
            threshold_snapshot_hash="xyz789",
            created_at=datetime.now(timezone.utc),
            integrity_verified=True,
            threshold_integrity_verified=True,
        )

        assert response.threshold_snapshot_hash == "xyz789"
        assert response.threshold_integrity_verified is True
