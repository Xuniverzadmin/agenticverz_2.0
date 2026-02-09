# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Immutable policy snapshot for run-time governance
# Callers: worker/runner.py, policy/engine.py
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: BACKEND_REMEDIATION_PLAN.md GAP-006, GAP-022

"""
Policy Snapshot Model

Captures immutable snapshot of active policies at run start.
Ensures that policy evaluation during a run uses the SAME rules
that were active when the run began, not current rules.

Key Invariants:
1. Snapshot is created ONCE at run start
2. Snapshot is IMMUTABLE (never updated)
3. All policy evaluations during run use snapshot, not live policies
4. Content hash provides integrity verification
5. Threshold hash provides independent threshold audit trail (GAP-022)

Remediation: GAP-006 (Policy Snapshots), GAP-022 (Threshold Snapshot Hash)
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import sqlalchemy as sa
from pydantic import BaseModel
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class PolicySnapshot(SQLModel, table=True):
    """
    Immutable snapshot of policies at run start.

    Created when a run starts, referenced throughout execution.
    Never modified after creation - provides audit trail.
    """
    __tablename__ = "policy_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    snapshot_id: str = Field(index=True, unique=True)
    tenant_id: str = Field(index=True)

    # Snapshot content (JSON serialized)
    policies_json: str = Field(
        description="JSON array of active policy definitions at snapshot time"
    )
    thresholds_json: str = Field(
        description="JSON object of threshold values (token limits, cost caps, etc.)"
    )

    # Integrity verification
    content_hash: str = Field(
        description="SHA256 hash of policies_json + thresholds_json for integrity"
    )

    # Threshold-specific hash (GAP-022)
    threshold_snapshot_hash: Optional[str] = Field(
        default=None,
        description="SHA256 hash of thresholds_json only, for independent threshold audit (GAP-022)"
    )

    # Metadata
    policy_count: int = Field(description="Number of policies in snapshot")
    policy_version: Optional[str] = Field(
        default=None,
        description="Optional version string from policy engine"
    )

    # Immutable timestamp
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    @classmethod
    def create_snapshot(
        cls,
        tenant_id: str,
        policies: list[dict[str, Any]],
        thresholds: dict[str, Any],
        policy_version: Optional[str] = None
    ) -> "PolicySnapshot":
        """
        Create immutable snapshot with content hash.

        Args:
            tenant_id: Tenant this snapshot belongs to
            policies: List of active policy definitions
            thresholds: Dict of threshold values
            policy_version: Optional version from policy engine

        Returns:
            PolicySnapshot ready for persistence
        """
        # Serialize deterministically (sorted keys)
        policies_json = json.dumps(policies, sort_keys=True, default=str)
        thresholds_json = json.dumps(thresholds, sort_keys=True, default=str)

        # Compute content hash for integrity (combined)
        content = policies_json + thresholds_json
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Compute threshold-specific hash for independent audit (GAP-022)
        threshold_snapshot_hash = hashlib.sha256(thresholds_json.encode()).hexdigest()

        # Generate snapshot ID from hash prefix
        snapshot_id = f"SNAP-{content_hash[:12]}"

        return cls(
            snapshot_id=snapshot_id,
            tenant_id=tenant_id,
            policies_json=policies_json,
            thresholds_json=thresholds_json,
            content_hash=content_hash,
            threshold_snapshot_hash=threshold_snapshot_hash,
            policy_count=len(policies),
            policy_version=policy_version
        )

    def get_policies(self) -> list[dict[str, Any]]:
        """Deserialize policies from JSON."""
        return json.loads(self.policies_json)

    def get_thresholds(self) -> dict[str, Any]:
        """Deserialize thresholds from JSON."""
        return json.loads(self.thresholds_json)

    def verify_integrity(self) -> bool:
        """Verify content hash matches stored data."""
        content = self.policies_json + self.thresholds_json
        computed_hash = hashlib.sha256(content.encode()).hexdigest()
        return computed_hash == self.content_hash

    def verify_threshold_integrity(self) -> bool:
        """Verify threshold hash matches stored threshold data (GAP-022)."""
        if self.threshold_snapshot_hash is None:
            return True  # Backward compatible: old snapshots without hash are valid
        computed_hash = hashlib.sha256(self.thresholds_json.encode()).hexdigest()
        return computed_hash == self.threshold_snapshot_hash

    def get_threshold_hash(self) -> str:
        """Get or compute threshold hash (GAP-022)."""
        if self.threshold_snapshot_hash:
            return self.threshold_snapshot_hash
        # Compute on-the-fly for backward compatibility
        return hashlib.sha256(self.thresholds_json.encode()).hexdigest()


# Pydantic models for API/Service use

class PolicySnapshotCreate(BaseModel):
    """Input for creating a policy snapshot."""
    tenant_id: str
    policies: list[dict[str, Any]]
    thresholds: dict[str, Any]
    policy_version: Optional[str] = None


class PolicySnapshotResponse(BaseModel):
    """API response for policy snapshot."""
    snapshot_id: str
    tenant_id: str
    policy_count: int
    policy_version: Optional[str]
    content_hash: str
    threshold_snapshot_hash: Optional[str] = None  # GAP-022
    created_at: datetime
    integrity_verified: bool = True
    threshold_integrity_verified: bool = True  # GAP-022

    class Config:
        from_attributes = True


class ThresholdSnapshot(BaseModel):
    """
    Threshold values captured in snapshot.

    Standard thresholds tracked per run.
    """
    # Token limits
    max_tokens_per_run: Optional[int] = None
    max_tokens_per_step: Optional[int] = None

    # Cost limits
    max_cost_cents_per_run: Optional[int] = None
    max_cost_cents_per_step: Optional[int] = None

    # Rate limits
    max_requests_per_minute: Optional[int] = None
    max_requests_per_hour: Optional[int] = None

    # Custom thresholds (extensible)
    custom: dict[str, Any] = {}
