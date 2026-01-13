# Layer: L7 — Ops & Deployment
# Product: system-wide
# Role: Migration for evidence capture failures resolution semantics
# Reference: Evidence Architecture v1.1, Category C3

"""085: Evidence Capture Failures Resolution Column

Add resolution column to evidence_capture_failures table to formalize
failure resolution semantics (transient/permanent/superseded).

Category C3: Failures must have resolution semantics so integrity
doesn't over-penalize transient issues.

Revision ID: 085_evidence_failure_resolution
Revises: 084_evidence_capture_failures
Create Date: 2026-01-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '085_evidence_failure_resolution'
down_revision = '084_evidence_capture_failures'
branch_labels = None
depends_on = None


def upgrade():
    """Add resolution column to evidence_capture_failures."""

    # Add resolution column with default 'transient'
    op.add_column(
        "evidence_capture_failures",
        sa.Column(
            "resolution",
            sa.String(32),
            nullable=False,
            server_default="transient",
        ),
    )

    # Add check constraint for valid resolution values
    op.create_check_constraint(
        "ck_ecf_resolution_valid",
        "evidence_capture_failures",
        "resolution IN ('transient', 'permanent', 'superseded')",
    )


def downgrade():
    """Remove resolution column."""
    op.drop_constraint("ck_ecf_resolution_valid", "evidence_capture_failures")
    op.drop_column("evidence_capture_failures", "resolution")
