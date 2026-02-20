# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Add signal_feedback table for UC-MON-04 activity feedback lifecycle
# Reference: UC-MON (Monitoring), UC_MONITORING_IMPLEMENTATION_METHODS.md

"""Add signal_feedback table for UC-MON activity feedback contracts

Revision ID: 128_monitoring_activity_feedback_contracts
Revises: 127_create_sdk_attestations
Create Date: 2026-02-11

Purpose:
Persist activity signal feedback (ack/suppress) with TTL/expiry determinism.
Supports UC-MON-04 feedback lifecycle invariants.
Fields: ttl_seconds, expires_at, bulk_action_id, target_set_hash, target_count.
"""

from alembic import op
import sqlalchemy as sa

revision = "128_monitoring_activity_feedback_contracts"
down_revision = "127_create_sdk_attestations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    # Legacy migration path: revision 071 already created signal_feedback with a
    # different schema. Preserve that table and create the UC-MON contract table.
    if "signal_feedback" in table_names:
        existing_cols = {col["name"] for col in inspector.get_columns("signal_feedback")}
        required_cols = {"signal_fingerprint", "feedback_state", "as_of"}
        if not required_cols.issubset(existing_cols):
            legacy_name = "signal_feedback_legacy"
            suffix = 0
            while legacy_name in table_names:
                suffix += 1
                legacy_name = f"signal_feedback_legacy_{suffix}"
            op.rename_table("signal_feedback", legacy_name)
            table_names.remove("signal_feedback")
            table_names.add(legacy_name)

    if "signal_feedback" not in table_names:
        op.create_table(
            "signal_feedback",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("signal_fingerprint", sa.String(length=128), nullable=False),
            sa.Column("feedback_state", sa.String(length=20), nullable=False),
            sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ttl_seconds", sa.Integer(), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("bulk_action_id", sa.String(length=64), nullable=True),
            sa.Column("target_set_hash", sa.String(length=64), nullable=True),
            sa.Column("target_count", sa.Integer(), nullable=True),
            sa.Column("actor_id", sa.String(length=200), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    # Idempotent index creation for reruns/partial migrations.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_signal_feedback_tenant_fingerprint
        ON signal_feedback (tenant_id, signal_fingerprint)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_signal_feedback_expires_at
        ON signal_feedback (expires_at)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_signal_feedback_expires_at")
    op.execute("DROP INDEX IF EXISTS ix_signal_feedback_tenant_fingerprint")
    op.execute("DROP TABLE IF EXISTS signal_feedback")
