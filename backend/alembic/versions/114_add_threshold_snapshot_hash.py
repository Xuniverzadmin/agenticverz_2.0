"""Add threshold_snapshot_hash to policy_snapshots

Revision ID: 114_add_threshold_snapshot_hash
Revises: 113_add_retrieval_evidence
Create Date: 2026-01-21

Reference: GAP-022 (Threshold Snapshot Hash)

This migration adds a dedicated threshold_snapshot_hash column to the
policy_snapshots table. This enables independent tracking of threshold
configuration changes for SOC2 audit compliance.

Purpose:
- Independent audit trail for threshold config changes
- Answer "Did thresholds change?" without comparing entire snapshots
- SOC2 compliance evidence for threshold governance
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "114_add_threshold_snapshot_hash"
down_revision = "113_add_retrieval_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add threshold_snapshot_hash column
    op.add_column(
        "policy_snapshots",
        sa.Column(
            "threshold_snapshot_hash",
            sa.String(64),
            nullable=True,
            comment="SHA256 hash of thresholds_json only (GAP-022)"
        ),
    )

    # Create index for threshold hash lookups (useful for finding snapshots with same thresholds)
    op.create_index(
        "ix_policy_snapshots_threshold_hash",
        "policy_snapshots",
        ["threshold_snapshot_hash"],
    )

    # Backfill existing snapshots with computed threshold hash
    # This ensures backward compatibility while maintaining data consistency
    op.execute("""
        UPDATE policy_snapshots
        SET threshold_snapshot_hash = encode(sha256(thresholds_json::bytea), 'hex')
        WHERE threshold_snapshot_hash IS NULL;
    """)


def downgrade() -> None:
    op.drop_index("ix_policy_snapshots_threshold_hash", table_name="policy_snapshots")
    op.drop_column("policy_snapshots", "threshold_snapshot_hash")
