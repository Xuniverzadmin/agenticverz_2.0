"""M12 Credit Tables Fix

Revision ID: 026_m12_credit_tables_fix
Revises: 025_m12_agents_schema
Create Date: 2025-12-13

Adds missing tables and indexes from M12.1 stabilization:
- credit_balances table
- credit_ledger context column
- idx_messages_reply_to index
- idx_credit_ledger_job_tenant index
- invoke_audit table (for M12.1 audit trail)

Based on: PIN-063-m12.1-stabilization.md
"""

revision = "026_m12_credit_tables_fix"
down_revision = "025_m12_agents_schema"
branch_labels = None
depends_on = None

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op


def upgrade():
    # 1. Create credit_balances table (IF NOT EXISTS — 025 may have created it)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS agents.credit_balances (
            id UUID DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
            tenant_id VARCHAR(128) NOT NULL UNIQUE,
            total_credits NUMERIC(12, 2) NOT NULL DEFAULT 1000,
            reserved_credits NUMERIC(12, 2) NOT NULL DEFAULT 0,
            spent_credits NUMERIC(12, 2) NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )

    # 2. Add context column to credit_ledger (if not exists)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'agents'
                AND table_name = 'credit_ledger'
                AND column_name = 'context'
            ) THEN
                ALTER TABLE agents.credit_ledger ADD COLUMN context JSONB;
            END IF;
        END $$;
    """
    )

    # 3. Add reply_to index for message latency
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_reply_to
        ON agents.messages(reply_to_id)
        WHERE reply_to_id IS NOT NULL
    """
    )

    # 4. Add composite index for credit ledger job+tenant lookups
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_credit_ledger_job_tenant
        ON agents.credit_ledger(job_id, tenant_id)
        WHERE job_id IS NOT NULL
    """
    )

    # 5. Create invoke_audit table for M12.1 audit trail
    op.create_table(
        "invoke_audit",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("invoke_id", sa.String(64), nullable=False, unique=True),
        sa.Column("caller_instance_id", sa.String(128), nullable=False, index=True),
        sa.Column("target_instance_id", sa.String(128), nullable=False, index=True),
        sa.Column("job_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("request_payload", JSONB, nullable=False),
        sa.Column("response_payload", JSONB, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("credits_charged", sa.Numeric(12, 2), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        schema="agents",
    )

    # 6. Create job_cancellations table for M12.1
    op.create_table(
        "job_cancellations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("cancelled_by", sa.String(128), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("items_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_cancelled", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credits_refunded", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="agents",
    )

    # FK constraint for job_cancellations
    op.create_foreign_key(
        "fk_job_cancellations_job",
        "job_cancellations",
        "jobs",
        ["job_id"],
        ["id"],
        source_schema="agents",
        referent_schema="agents",
        ondelete="CASCADE",
    )


def downgrade():
    # Drop FK first
    op.drop_constraint("fk_job_cancellations_job", "job_cancellations", schema="agents", type_="foreignkey")

    # Drop tables
    op.drop_table("job_cancellations", schema="agents")
    op.drop_table("invoke_audit", schema="agents")
    op.drop_table("credit_balances", schema="agents")

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS agents.idx_credit_ledger_job_tenant")
    op.execute("DROP INDEX IF EXISTS agents.idx_messages_reply_to")

    # Drop column
    op.execute("ALTER TABLE agents.credit_ledger DROP COLUMN IF EXISTS context")
