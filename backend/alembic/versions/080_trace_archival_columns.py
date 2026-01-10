"""Add archival columns to trace tables for SDSR soft-delete.

Revision ID: 080_trace_archival_columns
Revises: 079_sdsr_column_parity
Create Date: 2026-01-10

This migration adds archival semantics to trace tables to resolve the conflict
between S6 immutability (no DELETE) and SDSR cleanup requirements.

Contract Resolution:
- S6 Immutability: Prohibits DELETE, not archival state transitions
- SDSR Cleanup: Archives synthetic trace data instead of deleting

Tables modified:
- aos_traces: Add archived_at
- aos_trace_steps: Add archived_at

Views and queries MUST exclude: WHERE archived_at IS NULL

Reference: SDSR E2E Testing Protocol, S6 Immutability Guarantee
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "080_trace_archival_columns"
down_revision = "079_sdsr_column_parity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # aos_traces: Add archived_at for soft-archive
    op.add_column(
        "aos_traces",
        sa.Column("archived_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # aos_trace_steps: Add archived_at for soft-archive
    op.add_column(
        "aos_trace_steps",
        sa.Column("archived_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # Create indexes for efficient exclusion queries (WHERE archived_at IS NULL)
    op.create_index(
        "ix_aos_traces_archived",
        "aos_traces",
        ["archived_at"],
        unique=False,
        postgresql_where=sa.text("archived_at IS NULL"),
    )
    op.create_index(
        "ix_aos_trace_steps_archived",
        "aos_trace_steps",
        ["archived_at"],
        unique=False,
        postgresql_where=sa.text("archived_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_aos_trace_steps_archived", table_name="aos_trace_steps")
    op.drop_index("ix_aos_traces_archived", table_name="aos_traces")
    op.drop_column("aos_trace_steps", "archived_at")
    op.drop_column("aos_traces", "archived_at")
