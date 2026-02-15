# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Add analytics_artifacts table for UC-MON-06 reproducibility
# Reference: UC-MON (Monitoring), UC_MONITORING_IMPLEMENTATION_METHODS.md

"""Add analytics_artifacts table for UC-MON-06 reproducibility

Revision ID: 131_monitoring_analytics_reproducibility_fields
Revises: 130_monitoring_controls_binding_fields
Create Date: 2026-02-11

Purpose:
Persist analytics artifact metadata for reproducible computation.
Supports UC-MON-06 reproducibility contract.
Fields: dataset_version, input_window_hash, as_of, compute_code_version.
"""

from alembic import op
import sqlalchemy as sa

revision = "131_monitoring_analytics_reproducibility_fields"
down_revision = "130_monitoring_controls_binding_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analytics_artifacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=64), nullable=False),
        sa.Column("dataset_version", sa.String(length=64), nullable=False),
        sa.Column("input_window_hash", sa.String(length=64), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("compute_code_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "dataset_id", "dataset_version", name="uq_analytics_artifacts_tenant_dataset_version"),
    )
    op.create_index(
        "ix_analytics_artifacts_tenant",
        "analytics_artifacts",
        ["tenant_id"],
    )
    op.create_index(
        "ix_analytics_artifacts_dataset",
        "analytics_artifacts",
        ["dataset_id", "dataset_version"],
    )


def downgrade() -> None:
    op.drop_index("ix_analytics_artifacts_dataset", table_name="analytics_artifacts")
    op.drop_index("ix_analytics_artifacts_tenant", table_name="analytics_artifacts")
    op.drop_table("analytics_artifacts")
