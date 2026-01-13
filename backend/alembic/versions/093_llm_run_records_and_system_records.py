# Layer: L6 — Platform Substrate
# Product: ai-console
# Temporal:
#   Trigger: alembic upgrade
#   Execution: sync
# Role: LLM Run Records and System Records tables for Logs domain
# Reference: PIN-413 Domain Design — Logs v1 Expansion

"""
093 — LLM Run Records and System Records

Creates immutable record tables for the Logs domain:
- llm_run_records: Immutable execution record for every LLM run
- system_records: Immutable records for system-level events

Both tables are:
- APPEND-ONLY (enforced by DB trigger)
- WRITE-ONCE (no UPDATE, no DELETE)
- Trust anchors for verification

Revision ID: 093_llm_run_records_system_records
Revises: 092_rollback_decisions
Create Date: 2026-01-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "093_llm_run_records_system_records"
down_revision = "092_rollback_decisions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create llm_run_records and system_records tables."""

    # =========================================================================
    # 1. LLM Run Records — Immutable execution record
    # =========================================================================

    op.create_table(
        "llm_run_records",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(64),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("run_id", sa.String(64), nullable=False, index=True),
        sa.Column("trace_id", sa.String(64), nullable=True),

        # Provider / Model
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),

        # Content hashes (for verification without storing content)
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("response_hash", sa.String(64), nullable=True),

        # Token counts
        sa.Column("input_tokens", sa.Integer, nullable=False, default=0),
        sa.Column("output_tokens", sa.Integer, nullable=False, default=0),
        sa.Column("cost_cents", sa.Integer, nullable=False, default=0),

        # Execution status
        sa.Column("execution_status", sa.String(32), nullable=False),

        # Timestamps
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),

        # Source tracking
        sa.Column("source", sa.String(32), nullable=False),  # API, SDK, SYSTEM, SYNTHETIC
        sa.Column("is_synthetic", sa.Boolean, nullable=False, default=False),
        sa.Column("synthetic_scenario_id", sa.String(64), nullable=True),

        # Record timestamp (immutable)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Indexes for llm_run_records
    op.create_index(
        "idx_llm_run_records_tenant_time",
        "llm_run_records",
        ["tenant_id", "created_at"],
        postgresql_using="btree",
    )

    op.create_index(
        "idx_llm_run_records_provider_model",
        "llm_run_records",
        ["provider", "model"],
    )

    op.create_index(
        "idx_llm_run_records_status",
        "llm_run_records",
        ["tenant_id", "execution_status"],
    )

    # Check constraints for llm_run_records
    op.create_check_constraint(
        "ck_llm_run_records_execution_status",
        "llm_run_records",
        "execution_status IN ('SUCCEEDED', 'FAILED', 'ABORTED', 'TIMEOUT')",
    )

    op.create_check_constraint(
        "ck_llm_run_records_source",
        "llm_run_records",
        "source IN ('API', 'SDK', 'SYSTEM', 'SYNTHETIC', 'WORKER')",
    )

    # Immutability trigger for llm_run_records
    op.execute(
        """
        CREATE OR REPLACE FUNCTION forbid_llm_run_records_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'llm_run_records is immutable: UPDATE not allowed';
            ELSIF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'llm_run_records is immutable: DELETE not allowed';
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_llm_run_records_immutable
        BEFORE UPDATE OR DELETE ON llm_run_records
        FOR EACH ROW
        EXECUTE FUNCTION forbid_llm_run_records_mutation();
        """
    )

    # =========================================================================
    # 2. System Records — Immutable system event log
    # =========================================================================

    op.create_table(
        "system_records",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=True),  # NULL for system-wide events

        # Event classification
        sa.Column("component", sa.String(64), nullable=False),  # worker, api, scheduler, db
        sa.Column("event_type", sa.String(64), nullable=False),  # RESTART, DEPLOY, MIGRATION, etc.
        sa.Column("severity", sa.String(16), nullable=False),  # INFO, WARN, CRITICAL

        # Event content
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("details", postgresql.JSONB, nullable=True),

        # Causation
        sa.Column("caused_by", sa.String(32), nullable=True),  # SYSTEM, HUMAN, AUTOMATION
        sa.Column("correlation_id", sa.String(64), nullable=True),

        # Record timestamp (immutable)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Indexes for system_records
    op.create_index(
        "idx_system_records_time",
        "system_records",
        ["created_at"],
        postgresql_using="btree",
    )

    op.create_index(
        "idx_system_records_event",
        "system_records",
        ["event_type", "severity"],
    )

    op.create_index(
        "idx_system_records_component",
        "system_records",
        ["component"],
    )

    op.create_index(
        "idx_system_records_tenant",
        "system_records",
        ["tenant_id"],
        postgresql_where=sa.text("tenant_id IS NOT NULL"),
    )

    # Check constraints for system_records
    op.create_check_constraint(
        "ck_system_records_severity",
        "system_records",
        "severity IN ('INFO', 'WARN', 'CRITICAL')",
    )

    op.create_check_constraint(
        "ck_system_records_component",
        "system_records",
        "component IN ('worker', 'api', 'scheduler', 'db', 'auth', 'migration')",
    )

    op.create_check_constraint(
        "ck_system_records_event_type",
        "system_records",
        "event_type IN ('STARTUP', 'SHUTDOWN', 'RESTART', 'DEPLOY', 'MIGRATION', 'AUTH_CHANGE', 'CONFIG_CHANGE', 'ERROR', 'HEALTH_CHECK')",
    )

    op.create_check_constraint(
        "ck_system_records_caused_by",
        "system_records",
        "caused_by IS NULL OR caused_by IN ('SYSTEM', 'HUMAN', 'AUTOMATION')",
    )

    # Immutability trigger for system_records
    op.execute(
        """
        CREATE OR REPLACE FUNCTION forbid_system_records_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'system_records is immutable: UPDATE not allowed';
            ELSIF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'system_records is immutable: DELETE not allowed';
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_system_records_immutable
        BEFORE UPDATE OR DELETE ON system_records
        FOR EACH ROW
        EXECUTE FUNCTION forbid_system_records_mutation();
        """
    )


def downgrade() -> None:
    """Remove llm_run_records and system_records tables."""

    # Drop system_records
    op.execute("DROP TRIGGER IF EXISTS trg_system_records_immutable ON system_records")
    op.execute("DROP FUNCTION IF EXISTS forbid_system_records_mutation()")

    op.drop_constraint("ck_system_records_caused_by", "system_records", type_="check")
    op.drop_constraint("ck_system_records_event_type", "system_records", type_="check")
    op.drop_constraint("ck_system_records_component", "system_records", type_="check")
    op.drop_constraint("ck_system_records_severity", "system_records", type_="check")

    op.drop_index("idx_system_records_tenant", table_name="system_records")
    op.drop_index("idx_system_records_component", table_name="system_records")
    op.drop_index("idx_system_records_event", table_name="system_records")
    op.drop_index("idx_system_records_time", table_name="system_records")

    op.drop_table("system_records")

    # Drop llm_run_records
    op.execute("DROP TRIGGER IF EXISTS trg_llm_run_records_immutable ON llm_run_records")
    op.execute("DROP FUNCTION IF EXISTS forbid_llm_run_records_mutation()")

    op.drop_constraint("ck_llm_run_records_source", "llm_run_records", type_="check")
    op.drop_constraint("ck_llm_run_records_execution_status", "llm_run_records", type_="check")

    op.drop_index("idx_llm_run_records_status", table_name="llm_run_records")
    op.drop_index("idx_llm_run_records_provider_model", table_name="llm_run_records")
    op.drop_index("idx_llm_run_records_tenant_time", table_name="llm_run_records")

    op.drop_table("llm_run_records")
