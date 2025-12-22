"""Add costsim_provenance and costsim_alert_queue tables

Revision ID: 008_add_provenance_and_alert_queue
Revises: 007_add_costsim_cb_state
Create Date: 2025-12-04

This migration creates:
1. costsim_provenance - Stores V1/V2 comparison records for drift analysis
2. costsim_alert_queue - Reliable alert delivery queue with retry

The provenance table enables:
- V1 baseline backfill from historical simulations
- Drift detection between V1 and V2 costs
- Audit trail for all simulations
- Deduplication via input_hash

The alert queue enables:
- Reliable alert delivery even if Alertmanager is down
- Exponential backoff retry logic
- Audit trail of all alerts sent
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "008_provenance_alerts"
down_revision = "007_costsim_cb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # COSTSIM_PROVENANCE TABLE
    # ==========================================================================
    op.create_table(
        "costsim_provenance",
        # Primary key
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        # Context
        sa.Column("run_id", sa.Text(), nullable=True),
        sa.Column("tenant_id", sa.Text(), nullable=True),
        sa.Column("variant_slug", sa.Text(), nullable=True),  # v1, v2, canary
        sa.Column("source", sa.Text(), nullable=True),  # sandbox, canary, manual, backfill
        # Version tracking
        sa.Column("model_version", sa.Text(), nullable=True),
        sa.Column("adapter_version", sa.Text(), nullable=True),
        sa.Column("commit_sha", sa.Text(), nullable=True),
        # Hashes for deduplication
        sa.Column("input_hash", sa.Text(), nullable=True),
        sa.Column("output_hash", sa.Text(), nullable=True),
        # Cost data (nullable for error cases)
        sa.Column("v1_cost", sa.Float(), nullable=True),
        sa.Column("v2_cost", sa.Float(), nullable=True),
        sa.Column("cost_delta", sa.Float(), nullable=True),
        # Full payload (JSONB for query support)
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Timing
        sa.Column("runtime_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for provenance queries
    op.create_index("idx_costsim_prov_run", "costsim_provenance", ["run_id"])
    op.create_index("idx_costsim_prov_tenant", "costsim_provenance", ["tenant_id"])
    op.create_index("idx_costsim_prov_variant", "costsim_provenance", ["variant_slug"])
    op.create_index("idx_costsim_prov_input_hash", "costsim_provenance", ["input_hash"])
    op.create_index("idx_costsim_prov_source", "costsim_provenance", ["source"])
    op.create_index("idx_costsim_prov_created_at", "costsim_provenance", ["created_at"])

    # Composite index for tenant + time range queries
    op.create_index("idx_costsim_prov_tenant_created", "costsim_provenance", ["tenant_id", "created_at"])

    # Composite index for variant + time range queries (drift analysis)
    op.create_index("idx_costsim_prov_variant_created", "costsim_provenance", ["variant_slug", "created_at"])

    # ==========================================================================
    # COSTSIM_ALERT_QUEUE TABLE
    # ==========================================================================
    op.create_table(
        "costsim_alert_queue",
        # Primary key
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        # Alert payload (JSONB for Alertmanager format)
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        # Context
        sa.Column("alert_type", sa.Text(), nullable=True),  # disable, enable, canary_fail
        sa.Column("circuit_breaker_name", sa.Text(), nullable=True),
        sa.Column("incident_id", sa.Text(), nullable=True),
        # Retry tracking
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_error", sa.Text(), nullable=True),
        # Status
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for alert queue processing
    op.create_index("idx_costsim_alert_queue_next", "costsim_alert_queue", ["next_attempt_at"])
    op.create_index("idx_costsim_alert_queue_status", "costsim_alert_queue", ["status"])

    # Composite index for finding pending alerts ready to send
    op.create_index(
        "idx_costsim_alert_queue_pending_ready",
        "costsim_alert_queue",
        ["status", "next_attempt_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    # Drop alert_queue indexes and table
    op.drop_index("idx_costsim_alert_queue_pending_ready", table_name="costsim_alert_queue")
    op.drop_index("idx_costsim_alert_queue_status", table_name="costsim_alert_queue")
    op.drop_index("idx_costsim_alert_queue_next", table_name="costsim_alert_queue")
    op.drop_table("costsim_alert_queue")

    # Drop provenance indexes and table
    op.drop_index("idx_costsim_prov_variant_created", table_name="costsim_provenance")
    op.drop_index("idx_costsim_prov_tenant_created", table_name="costsim_provenance")
    op.drop_index("idx_costsim_prov_created_at", table_name="costsim_provenance")
    op.drop_index("idx_costsim_prov_source", table_name="costsim_provenance")
    op.drop_index("idx_costsim_prov_input_hash", table_name="costsim_provenance")
    op.drop_index("idx_costsim_prov_variant", table_name="costsim_provenance")
    op.drop_index("idx_costsim_prov_tenant", table_name="costsim_provenance")
    op.drop_index("idx_costsim_prov_run", table_name="costsim_provenance")
    op.drop_table("costsim_provenance")
