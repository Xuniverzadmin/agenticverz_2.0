"""LOGS Domain V2: log_exports table, correlation_id, indexes

Revision ID: 109_logs_domain_v2
Revises: 108_limit_breaches_evaluation_type
Create Date: 2026-01-19

Reference: LOGS_DOMAIN_V2_CONTRACT.md

This migration implements the LOGS Domain V2 schema:
1. Creates log_exports table for O5 evidence bundles
2. Adds correlation_id to audit_ledger for correlation spine
3. Creates required indexes for efficient queries
4. Creates immutability triggers (append-only enforcement)
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "109_logs_domain_v2"
down_revision = "108_limit_breaches_evaluation_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # 1. Create log_exports table
    # =========================================================================
    op.create_table(
        "log_exports",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column(
            "scope",
            sa.String(32),
            nullable=False,
        ),
        sa.Column("run_id", sa.String(64), nullable=True),  # Nullable for audit/system exports
        # Request metadata
        sa.Column("requested_by", sa.String(128), nullable=False),
        sa.Column(
            "format",
            sa.String(16),
            nullable=False,
        ),
        # Provenance (per Evidence Metadata Contract)
        sa.Column(
            "origin",
            sa.String(32),
            nullable=False,
        ),
        sa.Column("source_component", sa.String(64), nullable=False, server_default="LogExportService"),
        sa.Column("correlation_id", sa.String(64), nullable=True),
        # Completion
        sa.Column("checksum", sa.String(128), nullable=True),
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("delivered_at", sa.TIMESTAMP(timezone=True), nullable=True),
        # Immutable timestamp
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Add check constraints for enum-like columns
    op.create_check_constraint(
        "ck_log_exports_scope",
        "log_exports",
        "scope IN ('llm_run', 'system', 'audit', 'compliance')",
    )
    op.create_check_constraint(
        "ck_log_exports_format",
        "log_exports",
        "format IN ('json', 'csv', 'pdf', 'zip')",
    )
    op.create_check_constraint(
        "ck_log_exports_origin",
        "log_exports",
        "origin IN ('SYSTEM', 'HUMAN', 'AGENT')",
    )
    op.create_check_constraint(
        "ck_log_exports_status",
        "log_exports",
        "status IN ('pending', 'completed', 'failed')",
    )

    # =========================================================================
    # 2. Add correlation_id to audit_ledger
    # =========================================================================
    op.add_column(
        "audit_ledger",
        sa.Column("correlation_id", sa.String(64), nullable=True),
    )

    # =========================================================================
    # 3. Create required indexes
    # =========================================================================

    # log_exports index
    op.create_index(
        "idx_log_exports_tenant_created",
        "log_exports",
        ["tenant_id", sa.text("created_at DESC")],
    )

    # llm_run_records index (if not exists)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_llm_run_records_tenant_created
        ON llm_run_records(tenant_id, created_at DESC)
    """)

    # audit_ledger index (if not exists)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_ledger_tenant_created
        ON audit_ledger(tenant_id, created_at DESC)
    """)

    # system_records index (if not exists)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_system_records_tenant_created
        ON system_records(tenant_id, created_at DESC)
    """)

    # aos_trace_steps index for replay window queries (if not exists)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_aos_trace_steps_trace_timestamp
        ON aos_trace_steps(trace_id, timestamp)
    """)

    # =========================================================================
    # 4. Create immutability trigger for log_exports
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION reject_log_exports_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'log_exports is immutable: UPDATE and DELETE are forbidden';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS log_exports_immutable ON log_exports;
        CREATE TRIGGER log_exports_immutable
        BEFORE UPDATE OR DELETE ON log_exports
        FOR EACH ROW
        EXECUTE FUNCTION reject_log_exports_mutation();
    """)


def downgrade() -> None:
    # Remove trigger
    op.execute("DROP TRIGGER IF EXISTS log_exports_immutable ON log_exports")
    op.execute("DROP FUNCTION IF EXISTS reject_log_exports_mutation()")

    # Remove indexes (only the ones we explicitly created)
    op.drop_index("idx_log_exports_tenant_created", table_name="log_exports")

    # Remove correlation_id from audit_ledger
    op.drop_column("audit_ledger", "correlation_id")

    # Drop log_exports table (constraints drop automatically)
    op.drop_table("log_exports")
