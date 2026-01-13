# Layer: L7 — Ops & Deployment
# Product: system-wide
# Role: Migration for evidence capture failures tracking table
# Reference: Evidence Architecture v1.0, Watch-out #3

"""084: Evidence Capture Failures Table

Add governance.evidence_capture_failures table to track evidence capture
failures for integrity reporting.

Watch-out #3: Best-effort evidence failures must surface in integrity.

Revision ID: 084_evidence_capture_failures
Revises: 083_s6_lifecycle_aware_immutability
Create Date: 2026-01-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '084_evidence_capture_failures'
down_revision = '083_s6_lifecycle_aware_immutability'
branch_labels = None
depends_on = None


def upgrade():
    """Create evidence_capture_failures table."""

    # Create table using SQLAlchemy ops for consistency with other migrations
    op.create_table(
        "evidence_capture_failures",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("evidence_type", sa.String(64), nullable=False),
        sa.Column("failure_reason", sa.String(64), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index(
        "idx_evidence_capture_failures_run_id",
        "evidence_capture_failures",
        ["run_id"],
    )

    op.create_unique_constraint(
        "uq_ecf_run_evidence_reason",
        "evidence_capture_failures",
        ["run_id", "evidence_type", "failure_reason"],
    )


def downgrade():
    """Drop evidence_capture_failures table."""
    op.drop_table("evidence_capture_failures")
