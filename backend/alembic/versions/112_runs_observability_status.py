"""Add observability_status to runs table

Revision ID: 112_runs_observability_status
Revises: 111_policy_control_lever
Create Date: 2026-01-20

Reference: PIN-454 Cross-Domain Orchestration Audit (FIX-004)

This migration adds observability_status to the runs table to track
whether full observability (tracing) was available during run execution.

Values:
- FULL: All observability working (default)
- DEGRADED: Trace creation failed, run continued
- NONE: No observability (legacy runs or permissive mode)
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "112_runs_observability_status"
down_revision = "111_policy_control_lever"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add observability_status column with default FULL for new runs
    op.add_column(
        "runs",
        sa.Column(
            "observability_status",
            sa.String(20),
            nullable=True,
            server_default="FULL",
            comment="Observability status: FULL, DEGRADED, NONE (PIN-454 FIX-004)",
        ),
    )

    # Add observability_error column to capture why observability degraded
    op.add_column(
        "runs",
        sa.Column(
            "observability_error",
            sa.Text(),
            nullable=True,
            comment="Error message if observability was degraded",
        ),
    )

    # Create index for querying degraded runs (operational monitoring)
    op.create_index(
        "ix_runs_observability_status",
        "runs",
        ["observability_status"],
        postgresql_where=sa.text("observability_status != 'FULL'"),
    )


def downgrade() -> None:
    op.drop_index("ix_runs_observability_status", table_name="runs")
    op.drop_column("runs", "observability_error")
    op.drop_column("runs", "observability_status")
