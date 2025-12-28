"""PB-S3: Pattern Feedback Table

This migration creates the pattern_feedback table for storing
observed patterns WITHOUT modifying execution history.

PB-S3 Guarantee: Feedback observes but never mutates.
- Pattern detection creates feedback records
- Feedback references runs via provenance (read-only)
- No execution data is modified

Revision ID: 056_pb_s3_pattern_feedback
Revises: 055_pb_s2_crashed_status
Create Date: 2025-12-27

CRITICAL: This table is SEPARATE from execution tables (worker_runs, traces).
Feedback is observation, not truth modification.
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers
revision = "056_pb_s3_pattern_feedback"
down_revision = "055_pb_s2_crashed_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create pattern_feedback table for PB-S3."""

    # ============================================================
    # STEP 1: Create pattern_feedback table
    # ============================================================
    # Note: tenant_id is VARCHAR to match existing tenants table schema
    op.create_table(
        "pattern_feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.String(255), nullable=False, index=True),
        # Pattern classification
        sa.Column("pattern_type", sa.String(50), nullable=False, index=True),  # failure_pattern, cost_spike, etc.
        sa.Column("severity", sa.String(20), nullable=False, default="info"),  # info, warning, critical
        # Pattern description
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("signature", sa.String(255), nullable=True, index=True),  # For deduplication
        # Provenance - references to source runs (READ-ONLY observation)
        # This is a JSONB array of run_ids that triggered detection
        # We store IDs, not modify the runs
        sa.Column("provenance", JSONB, nullable=False, default=[]),
        # Detection metadata
        sa.Column("occurrence_count", sa.Integer, nullable=False, default=1),
        sa.Column("time_window_minutes", sa.Integer, nullable=True),
        sa.Column("threshold_used", sa.String(100), nullable=True),
        # Additional context
        sa.Column("metadata", JSONB, nullable=True),
        # Timestamps
        sa.Column("detected_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        # Status tracking (for UI visibility)
        sa.Column("acknowledged", sa.Boolean, nullable=False, default=False),
        sa.Column("acknowledged_at", sa.DateTime, nullable=True),
        sa.Column("acknowledged_by", sa.String(255), nullable=True),
    )

    # ============================================================
    # STEP 2: Add indexes for common queries
    # ============================================================
    op.create_index(
        "ix_pattern_feedback_tenant_type",
        "pattern_feedback",
        ["tenant_id", "pattern_type"],
    )
    op.create_index(
        "ix_pattern_feedback_detected_at",
        "pattern_feedback",
        ["detected_at"],
    )
    op.create_index(
        "ix_pattern_feedback_unacknowledged",
        "pattern_feedback",
        ["tenant_id", "acknowledged"],
        postgresql_where=sa.text("acknowledged = false"),
    )

    # ============================================================
    # STEP 3: Add table comment documenting PB-S3 contract
    # ============================================================
    op.execute(
        """
        COMMENT ON TABLE pattern_feedback IS
        'PB-S3 Pattern Feedback: Observations about execution patterns. '
        'This table is SEPARATE from execution history. '
        'Provenance links to runs are READ-ONLY references. '
        'No execution data (worker_runs, traces, costs) may be modified by feedback. '
        'Feedback is observation, not action.';
    """
    )


def downgrade() -> None:
    """Remove pattern_feedback table."""
    op.drop_index("ix_pattern_feedback_unacknowledged", table_name="pattern_feedback")
    op.drop_index("ix_pattern_feedback_detected_at", table_name="pattern_feedback")
    op.drop_index("ix_pattern_feedback_tenant_type", table_name="pattern_feedback")
    op.drop_table("pattern_feedback")
