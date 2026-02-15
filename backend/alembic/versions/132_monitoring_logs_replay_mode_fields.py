# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Add replay mode fields to aos_traces for UC-MON-01 replay determinism
# Reference: UC-MON (Monitoring), UC_MONITORING_IMPLEMENTATION_METHODS.md

"""Add replay mode fields to aos_traces for UC-MON-01

Revision ID: 132_monitoring_logs_replay_mode_fields
Revises: 131_monitoring_analytics_reproducibility_fields
Create Date: 2026-02-11

Purpose:
Extend aos_traces with replay mode metadata for deterministic trace replay.
Supports UC-MON-01 replay determinism contract.
Fields: replay_mode (FULL|TRACE_ONLY), replay_attempt_id,
        replay_artifact_version, trace_completeness_status.
"""

from alembic import op
import sqlalchemy as sa

revision = "132_monitoring_logs_replay_mode_fields"
down_revision = "131_monitoring_analytics_reproducibility_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("aos_traces", sa.Column("replay_mode", sa.String(length=20), nullable=True))
    op.add_column("aos_traces", sa.Column("replay_attempt_id", sa.String(length=64), nullable=True))
    op.add_column("aos_traces", sa.Column("replay_artifact_version", sa.String(length=64), nullable=True))
    op.add_column("aos_traces", sa.Column("trace_completeness_status", sa.String(length=30), nullable=True))
    op.create_index(
        "ix_aos_traces_replay_mode",
        "aos_traces",
        ["replay_mode"],
    )
    op.create_index(
        "ix_aos_traces_replay_attempt",
        "aos_traces",
        ["replay_attempt_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_aos_traces_replay_attempt", table_name="aos_traces")
    op.drop_index("ix_aos_traces_replay_mode", table_name="aos_traces")
    op.drop_column("aos_traces", "trace_completeness_status")
    op.drop_column("aos_traces", "replay_artifact_version")
    op.drop_column("aos_traces", "replay_attempt_id")
    op.drop_column("aos_traces", "replay_mode")
