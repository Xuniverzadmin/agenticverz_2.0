"""Add costsim_cb_state table for DB-backed circuit breaker

Revision ID: 007_add_costsim_cb_state
Revises: 006_add_archival_partitioning
Create Date: 2025-12-04

This migration creates the costsim_cb_state table for centralized
circuit breaker state management across multiple replicas.

The table is designed to:
- Replace file-based circuit breaker state
- Support atomic updates via SELECT FOR UPDATE
- Track who/why/when state changes occurred
- Support TTL-based auto-recovery via disabled_until
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "007_costsim_cb"
down_revision = "006_add_archival_partitioning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create costsim_cb_state table
    op.create_table(
        "costsim_cb_state",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("disabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("disabled_by", sa.Text(), nullable=True),
        sa.Column("disabled_reason", sa.Text(), nullable=True),
        sa.Column("disabled_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("incident_id", sa.Text(), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_costsim_cb_state_name"),
    )

    # Create index for fast lookups by name
    op.create_index("idx_costsim_cb_state_name", "costsim_cb_state", ["name"])

    # Create costsim_cb_incidents table for audit trail
    op.create_table(
        "costsim_cb_incidents",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("circuit_breaker_name", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("drift_score", sa.Float(), nullable=True),
        sa.Column("sample_count", sa.Integer(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.Text(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("alert_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("alert_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("alert_response", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for incidents
    op.create_index("idx_costsim_cb_incidents_cb_name", "costsim_cb_incidents", ["circuit_breaker_name"])
    op.create_index("idx_costsim_cb_incidents_timestamp", "costsim_cb_incidents", ["timestamp"])
    op.create_index("idx_costsim_cb_incidents_resolved", "costsim_cb_incidents", ["resolved"])

    # Insert default row for costsim_v2
    op.execute(
        """
        INSERT INTO costsim_cb_state (name, disabled, consecutive_failures)
        VALUES ('costsim_v2', false, 0)
        ON CONFLICT (name) DO NOTHING
    """
    )


def downgrade() -> None:
    op.drop_index("idx_costsim_cb_incidents_resolved", table_name="costsim_cb_incidents")
    op.drop_index("idx_costsim_cb_incidents_timestamp", table_name="costsim_cb_incidents")
    op.drop_index("idx_costsim_cb_incidents_cb_name", table_name="costsim_cb_incidents")
    op.drop_table("costsim_cb_incidents")

    op.drop_index("idx_costsim_cb_state_name", table_name="costsim_cb_state")
    op.drop_table("costsim_cb_state")
