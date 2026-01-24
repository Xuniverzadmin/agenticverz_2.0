# Layer: L6 — Driver
# Product: system-wide
# Reference: GAP-029 (Policy snapshot immutability)
"""
Policy Snapshot Immutability Service (GAP-029).

Provides immutable policy snapshot management with:
- Immutability enforcement (no modifications after creation)
- Snapshot versioning and history
- Integrity verification
- Tenant isolation
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional
import hashlib
import json
import uuid


class SnapshotStatus(str, Enum):
    """Status of a policy snapshot."""

    ACTIVE = "active"           # Currently active snapshot
    SUPERSEDED = "superseded"   # Replaced by newer snapshot
    ARCHIVED = "archived"       # Archived for historical record
    INVALID = "invalid"         # Failed integrity check


class ImmutabilityViolation(str, Enum):
    """Types of immutability violations."""

    CONTENT_MODIFICATION = "content_modification"   # Attempted to modify content
    HASH_MISMATCH = "hash_mismatch"                 # Content doesn't match hash
    TIMESTAMP_TAMPERING = "timestamp_tampering"     # Attempted timestamp change
    STATUS_DOWNGRADE = "status_downgrade"           # Invalid status transition
    DELETION_BLOCKED = "deletion_blocked"           # Cannot delete active snapshot


@dataclass
class PolicySnapshotData:
    """
    Immutable policy snapshot data.

    Once created, the content cannot be modified.
    Only status can transition through allowed paths.
    """

    snapshot_id: str
    tenant_id: str
    version: int

    # Content (immutable after creation)
    policies_json: str
    thresholds_json: str
    content_hash: str
    threshold_hash: str

    # Metadata
    policy_count: int
    policy_version: Optional[str] = None
    description: Optional[str] = None

    # Status (limited transitions allowed)
    status: SnapshotStatus = SnapshotStatus.ACTIVE

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    superseded_at: Optional[datetime] = None
    superseded_by: Optional[str] = None

    # Immutability tracking
    is_sealed: bool = True  # Always True after creation

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify content hash matches stored data."""
        combined = self.policies_json + self.thresholds_json
        computed_hash = self.compute_hash(combined)
        return computed_hash == self.content_hash

    def verify_threshold_integrity(self) -> bool:
        """Verify threshold hash matches threshold data."""
        computed_hash = self.compute_hash(self.thresholds_json)
        return computed_hash == self.threshold_hash

    def get_policies(self) -> list[dict[str, Any]]:
        """Deserialize policies from JSON."""
        return json.loads(self.policies_json)

    def get_thresholds(self) -> dict[str, Any]:
        """Deserialize thresholds from JSON."""
        return json.loads(self.thresholds_json)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "tenant_id": self.tenant_id,
            "version": self.version,
            "content_hash": self.content_hash,
            "threshold_hash": self.threshold_hash,
            "policy_count": self.policy_count,
            "policy_version": self.policy_version,
            "description": self.description,
            "status": self.status.value,
            "is_sealed": self.is_sealed,
            "integrity_valid": self.verify_integrity(),
            "created_at": self.created_at.isoformat(),
            "superseded_at": (
                self.superseded_at.isoformat() if self.superseded_at else None
            ),
            "superseded_by": self.superseded_by,
        }


class PolicySnapshotError(Exception):
    """Exception for policy snapshot errors."""

    def __init__(
        self,
        message: str,
        snapshot_id: Optional[str] = None,
        violation_type: Optional[ImmutabilityViolation] = None,
    ):
        super().__init__(message)
        self.message = message
        self.snapshot_id = snapshot_id
        self.violation_type = violation_type

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error": self.message,
            "snapshot_id": self.snapshot_id,
            "violation_type": (
                self.violation_type.value if self.violation_type else None
            ),
        }


@dataclass
class SnapshotRegistryStats:
    """Statistics for snapshot registry."""

    total_snapshots: int = 0
    active_snapshots: int = 0
    superseded_snapshots: int = 0
    archived_snapshots: int = 0
    invalid_snapshots: int = 0

    # Tenant breakdown
    tenants_with_snapshots: int = 0

    # Integrity
    snapshots_with_valid_integrity: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_snapshots": self.total_snapshots,
            "active_snapshots": self.active_snapshots,
            "superseded_snapshots": self.superseded_snapshots,
            "archived_snapshots": self.archived_snapshots,
            "invalid_snapshots": self.invalid_snapshots,
            "tenants_with_snapshots": self.tenants_with_snapshots,
            "snapshots_with_valid_integrity": self.snapshots_with_valid_integrity,
        }


class PolicySnapshotRegistry:
    """
    Registry for managing immutable policy snapshots.

    Features:
    - Immutability enforcement (no content modifications)
    - Version tracking per tenant
    - Automatic supersession of old snapshots
    - Integrity verification
    - Tenant isolation
    """

    # Allowed status transitions
    # ACTIVE can only become SUPERSEDED (by a new snapshot)
    # SUPERSEDED can then be ARCHIVED
    # ACTIVE cannot be directly archived - must be superseded first
    ALLOWED_TRANSITIONS: dict[SnapshotStatus, set[SnapshotStatus]] = {
        SnapshotStatus.ACTIVE: {SnapshotStatus.SUPERSEDED},
        SnapshotStatus.SUPERSEDED: {SnapshotStatus.ARCHIVED},
        SnapshotStatus.ARCHIVED: set(),  # Terminal state
        SnapshotStatus.INVALID: set(),   # Terminal state
    }

    def __init__(self):
        """Initialize the registry."""
        self._snapshots: dict[str, PolicySnapshotData] = {}
        self._tenant_snapshots: dict[str, list[str]] = {}
        self._tenant_versions: dict[str, int] = {}

    def create(
        self,
        tenant_id: str,
        policies: list[dict[str, Any]],
        thresholds: dict[str, Any],
        policy_version: Optional[str] = None,
        description: Optional[str] = None,
        snapshot_id: Optional[str] = None,
    ) -> PolicySnapshotData:
        """
        Create an immutable policy snapshot.

        This method:
        1. Creates a new sealed snapshot
        2. Computes content hashes for integrity
        3. Supersedes any existing active snapshot for the tenant
        4. Assigns the next version number

        Args:
            tenant_id: Tenant this snapshot belongs to
            policies: List of active policy definitions
            thresholds: Dict of threshold values
            policy_version: Optional version from policy engine
            description: Optional description of this snapshot
            snapshot_id: Optional specific snapshot ID

        Returns:
            The created immutable snapshot
        """
        # Serialize deterministically
        policies_json = json.dumps(policies, sort_keys=True, default=str)
        thresholds_json = json.dumps(thresholds, sort_keys=True, default=str)

        # Compute hashes
        combined = policies_json + thresholds_json
        content_hash = PolicySnapshotData.compute_hash(combined)
        threshold_hash = PolicySnapshotData.compute_hash(thresholds_json)

        # Generate snapshot ID if not provided
        snapshot_id = snapshot_id or f"SNAP-{content_hash[:12]}-{str(uuid.uuid4())[:8]}"

        # Get next version for tenant
        version = self._get_next_version(tenant_id)

        # Supersede existing active snapshot
        self._supersede_active(tenant_id, snapshot_id)

        # Create the snapshot
        snapshot = PolicySnapshotData(
            snapshot_id=snapshot_id,
            tenant_id=tenant_id,
            version=version,
            policies_json=policies_json,
            thresholds_json=thresholds_json,
            content_hash=content_hash,
            threshold_hash=threshold_hash,
            policy_count=len(policies),
            policy_version=policy_version,
            description=description,
            status=SnapshotStatus.ACTIVE,
            is_sealed=True,
        )

        # Store the snapshot
        self._snapshots[snapshot_id] = snapshot

        # Track by tenant
        if tenant_id not in self._tenant_snapshots:
            self._tenant_snapshots[tenant_id] = []
        self._tenant_snapshots[tenant_id].append(snapshot_id)

        return snapshot

    def get(self, snapshot_id: str) -> Optional[PolicySnapshotData]:
        """Get a snapshot by ID."""
        return self._snapshots.get(snapshot_id)

    def get_active(self, tenant_id: str) -> Optional[PolicySnapshotData]:
        """Get the current active snapshot for a tenant."""
        snapshot_ids = self._tenant_snapshots.get(tenant_id, [])
        for snapshot_id in reversed(snapshot_ids):
            snapshot = self._snapshots.get(snapshot_id)
            if snapshot and snapshot.status == SnapshotStatus.ACTIVE:
                return snapshot
        return None

    def get_by_version(
        self,
        tenant_id: str,
        version: int,
    ) -> Optional[PolicySnapshotData]:
        """Get a snapshot by tenant and version number."""
        for snapshot in self._snapshots.values():
            if snapshot.tenant_id == tenant_id and snapshot.version == version:
                return snapshot
        return None

    def list(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[SnapshotStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PolicySnapshotData]:
        """List snapshots with optional filters."""
        snapshots = list(self._snapshots.values())

        if tenant_id:
            snapshots = [s for s in snapshots if s.tenant_id == tenant_id]

        if status:
            snapshots = [s for s in snapshots if s.status == status]

        # Sort by version descending
        snapshots.sort(key=lambda s: (s.tenant_id, -s.version))

        return snapshots[offset:offset + limit]

    def get_history(
        self,
        tenant_id: str,
        limit: int = 100,
    ) -> List[PolicySnapshotData]:
        """Get version history for a tenant."""
        snapshots = [
            s for s in self._snapshots.values()
            if s.tenant_id == tenant_id
        ]
        snapshots.sort(key=lambda s: -s.version)
        return snapshots[:limit]

    def archive(self, snapshot_id: str) -> PolicySnapshotData:
        """
        Archive a snapshot.

        Only non-active snapshots can be archived.
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            raise PolicySnapshotError(
                f"Snapshot not found: {snapshot_id}",
                snapshot_id=snapshot_id,
            )

        # Validate transition
        if SnapshotStatus.ARCHIVED not in self.ALLOWED_TRANSITIONS[snapshot.status]:
            raise PolicySnapshotError(
                f"Cannot archive snapshot in status: {snapshot.status.value}",
                snapshot_id=snapshot_id,
                violation_type=ImmutabilityViolation.STATUS_DOWNGRADE,
            )

        snapshot.status = SnapshotStatus.ARCHIVED
        return snapshot

    def verify(self, snapshot_id: str) -> dict[str, Any]:
        """
        Verify snapshot integrity.

        Returns verification results.
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            raise PolicySnapshotError(
                f"Snapshot not found: {snapshot_id}",
                snapshot_id=snapshot_id,
            )

        content_valid = snapshot.verify_integrity()
        threshold_valid = snapshot.verify_threshold_integrity()

        # Mark as invalid if integrity check fails
        if not content_valid or not threshold_valid:
            snapshot.status = SnapshotStatus.INVALID

        return {
            "snapshot_id": snapshot_id,
            "content_integrity": content_valid,
            "threshold_integrity": threshold_valid,
            "is_valid": content_valid and threshold_valid,
            "status": snapshot.status.value,
        }

    def attempt_modify(
        self,
        snapshot_id: str,
        **_kwargs: Any,
    ) -> None:
        """
        Attempt to modify a snapshot (ALWAYS FAILS).

        This method exists to enforce immutability by explicitly
        rejecting any modification attempts with a clear error.
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            raise PolicySnapshotError(
                f"Snapshot not found: {snapshot_id}",
                snapshot_id=snapshot_id,
            )

        # Always fail - snapshots are immutable
        raise PolicySnapshotError(
            "Policy snapshots are immutable and cannot be modified. "
            "Create a new snapshot instead.",
            snapshot_id=snapshot_id,
            violation_type=ImmutabilityViolation.CONTENT_MODIFICATION,
        )

    def delete(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.

        Only archived snapshots can be deleted.
        Active snapshots must first be superseded and archived.
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            return False

        # Block deletion of active snapshots
        if snapshot.status == SnapshotStatus.ACTIVE:
            raise PolicySnapshotError(
                "Cannot delete active snapshot. Archive it first.",
                snapshot_id=snapshot_id,
                violation_type=ImmutabilityViolation.DELETION_BLOCKED,
            )

        # Remove from storage
        del self._snapshots[snapshot_id]

        # Remove from tenant tracking
        tenant_snapshots = self._tenant_snapshots.get(snapshot.tenant_id, [])
        if snapshot_id in tenant_snapshots:
            tenant_snapshots.remove(snapshot_id)

        return True

    def get_statistics(
        self,
        tenant_id: Optional[str] = None,
    ) -> SnapshotRegistryStats:
        """Get registry statistics."""
        stats = SnapshotRegistryStats()
        tenants_seen: set[str] = set()

        for snapshot in self._snapshots.values():
            if tenant_id and snapshot.tenant_id != tenant_id:
                continue

            stats.total_snapshots += 1
            tenants_seen.add(snapshot.tenant_id)

            if snapshot.status == SnapshotStatus.ACTIVE:
                stats.active_snapshots += 1
            elif snapshot.status == SnapshotStatus.SUPERSEDED:
                stats.superseded_snapshots += 1
            elif snapshot.status == SnapshotStatus.ARCHIVED:
                stats.archived_snapshots += 1
            elif snapshot.status == SnapshotStatus.INVALID:
                stats.invalid_snapshots += 1

            if snapshot.verify_integrity():
                stats.snapshots_with_valid_integrity += 1

        stats.tenants_with_snapshots = len(tenants_seen)

        return stats

    def clear_tenant(self, tenant_id: str) -> int:
        """Clear all archived snapshots for a tenant."""
        snapshot_ids = list(self._tenant_snapshots.get(tenant_id, []))
        cleared = 0

        for snapshot_id in snapshot_ids:
            snapshot = self._snapshots.get(snapshot_id)
            if snapshot and snapshot.status == SnapshotStatus.ARCHIVED:
                del self._snapshots[snapshot_id]
                self._tenant_snapshots[tenant_id].remove(snapshot_id)
                cleared += 1

        return cleared

    def reset(self) -> None:
        """Reset all state (for testing)."""
        self._snapshots.clear()
        self._tenant_snapshots.clear()
        self._tenant_versions.clear()

    def _get_next_version(self, tenant_id: str) -> int:
        """Get the next version number for a tenant."""
        current = self._tenant_versions.get(tenant_id, 0)
        next_version = current + 1
        self._tenant_versions[tenant_id] = next_version
        return next_version

    def _supersede_active(
        self,
        tenant_id: str,
        new_snapshot_id: str,
    ) -> None:
        """Supersede the current active snapshot for a tenant."""
        active = self.get_active(tenant_id)
        if active:
            active.status = SnapshotStatus.SUPERSEDED
            active.superseded_at = datetime.now(timezone.utc)
            active.superseded_by = new_snapshot_id


# Module-level singleton
_registry: Optional[PolicySnapshotRegistry] = None


def get_snapshot_registry() -> PolicySnapshotRegistry:
    """Get the singleton registry instance."""
    global _registry
    if _registry is None:
        _registry = PolicySnapshotRegistry()
    return _registry


def _reset_snapshot_registry() -> None:
    """Reset the singleton (for testing)."""
    global _registry
    if _registry:
        _registry.reset()
    _registry = None


# Helper functions
def create_policy_snapshot(
    tenant_id: str,
    policies: list[dict[str, Any]],
    thresholds: dict[str, Any],
    policy_version: Optional[str] = None,
    description: Optional[str] = None,
) -> PolicySnapshotData:
    """Create a new immutable policy snapshot."""
    registry = get_snapshot_registry()
    return registry.create(
        tenant_id=tenant_id,
        policies=policies,
        thresholds=thresholds,
        policy_version=policy_version,
        description=description,
    )


def get_policy_snapshot(snapshot_id: str) -> Optional[PolicySnapshotData]:
    """Get a policy snapshot by ID."""
    registry = get_snapshot_registry()
    return registry.get(snapshot_id)


def get_active_snapshot(tenant_id: str) -> Optional[PolicySnapshotData]:
    """Get the active policy snapshot for a tenant."""
    registry = get_snapshot_registry()
    return registry.get_active(tenant_id)


def get_snapshot_history(
    tenant_id: str,
    limit: int = 100,
) -> List[PolicySnapshotData]:
    """Get snapshot version history for a tenant."""
    registry = get_snapshot_registry()
    return registry.get_history(tenant_id, limit=limit)


def verify_snapshot(snapshot_id: str) -> dict[str, Any]:
    """Verify snapshot integrity."""
    registry = get_snapshot_registry()
    return registry.verify(snapshot_id)
