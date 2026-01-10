"""Add SDSR columns to remaining CLEANUP_ORDER tables.

Revision ID: 079_sdsr_column_parity
Revises: 078_aos_traces_sdsr_columns
Create Date: 2026-01-10

This migration ensures all tables in CLEANUP_ORDER have SDSR columns:
- is_synthetic: BOOLEAN NOT NULL DEFAULT false
- synthetic_scenario_id: VARCHAR (nullable)

Tables modified:
- policy_proposals: Add both columns
- aos_trace_steps: Add both columns
- prevention_records: Add is_synthetic only (synthetic_scenario_id exists)

Reference: SDSR E2E Testing Protocol, PIN-379
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "079_sdsr_column_parity"
down_revision = "078_aos_traces_sdsr_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # policy_proposals: Add both SDSR columns
    op.add_column(
        "policy_proposals",
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "policy_proposals",
        sa.Column("synthetic_scenario_id", sa.String(), nullable=True),
    )

    # aos_trace_steps: Add both SDSR columns
    op.add_column(
        "aos_trace_steps",
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "aos_trace_steps",
        sa.Column("synthetic_scenario_id", sa.String(), nullable=True),
    )

    # prevention_records: Add is_synthetic only (synthetic_scenario_id already exists)
    op.add_column(
        "prevention_records",
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # Create indexes for efficient SDSR cleanup queries
    op.create_index(
        "ix_policy_proposals_sdsr",
        "policy_proposals",
        ["is_synthetic", "synthetic_scenario_id"],
        unique=False,
    )
    op.create_index(
        "ix_aos_trace_steps_sdsr",
        "aos_trace_steps",
        ["is_synthetic", "synthetic_scenario_id"],
        unique=False,
    )
    op.create_index(
        "ix_prevention_records_sdsr",
        "prevention_records",
        ["is_synthetic", "synthetic_scenario_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("ix_prevention_records_sdsr", table_name="prevention_records")
    op.drop_index("ix_aos_trace_steps_sdsr", table_name="aos_trace_steps")
    op.drop_index("ix_policy_proposals_sdsr", table_name="policy_proposals")

    # Drop columns
    op.drop_column("prevention_records", "is_synthetic")
    op.drop_column("aos_trace_steps", "synthetic_scenario_id")
    op.drop_column("aos_trace_steps", "is_synthetic")
    op.drop_column("policy_proposals", "synthetic_scenario_id")
    op.drop_column("policy_proposals", "is_synthetic")
