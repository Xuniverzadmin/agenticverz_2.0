"""Add costsim_canary_reports table

Revision ID: 121_canary_reports
Revises: 120_add_is_frozen_to_api_keys
Create Date: 2026-02-03

This migration creates the costsim_canary_reports table for storing
canary run results. Enables:
- Canary report retrieval via /canary/reports endpoint
- Trend analysis of V1/V2 drift over time
- Audit trail of all canary validations
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "121_canary_reports"
down_revision = "120_add_is_frozen_to_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "costsim_canary_reports",
        # Primary key
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Text(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("status", sa.Text(), nullable=False),  # pass, fail, error, skipped
        # Sample stats
        sa.Column("total_samples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("matching_samples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("minor_drift_samples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("major_drift_samples", sa.Integer(), nullable=False, server_default="0"),
        # Metrics
        sa.Column("median_cost_diff", sa.Float(), nullable=True),
        sa.Column("p90_cost_diff", sa.Float(), nullable=True),
        sa.Column("kl_divergence", sa.Float(), nullable=True),
        sa.Column("outlier_count", sa.Integer(), nullable=True),
        # Verdict
        sa.Column("passed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("failure_reasons_json", sa.Text(), nullable=True),
        # Artifacts and golden comparison
        sa.Column("artifact_paths_json", sa.Text(), nullable=True),
        sa.Column("golden_comparison_json", sa.Text(), nullable=True),
        # Metadata
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes
    op.create_index("idx_costsim_canary_run_id", "costsim_canary_reports", ["run_id"], unique=True)
    op.create_index("idx_costsim_canary_timestamp", "costsim_canary_reports", ["timestamp"])
    op.create_index("idx_costsim_canary_status", "costsim_canary_reports", ["status"])
    op.create_index("idx_costsim_canary_passed", "costsim_canary_reports", ["passed"])


def downgrade() -> None:
    op.drop_index("idx_costsim_canary_passed", table_name="costsim_canary_reports")
    op.drop_index("idx_costsim_canary_status", table_name="costsim_canary_reports")
    op.drop_index("idx_costsim_canary_timestamp", table_name="costsim_canary_reports")
    op.drop_index("idx_costsim_canary_run_id", table_name="costsim_canary_reports")
    op.drop_table("costsim_canary_reports")
