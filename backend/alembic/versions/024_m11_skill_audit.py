"""M11 Skill Audit Tables

Revision ID: 024_m11_skill_audit
Revises: 023_m10_archive_partitioning
Create Date: 2025-12-09

Creates audit infrastructure for M11 skills to support deterministic replay.

Tables:
- m11_audit.ops: Append-only skill operation log with op_index sequencing
- m11_audit.replay_runs: Track replay verification runs

Key Design:
- op_index is monotonically increasing per workflow_run_id
- transient flag marks operations safe to skip in replay
- result is nullable (filled after execution)
- Append-only: no UPDATE/DELETE triggers enforced at app level
"""

revision = "024_m11_skill_audit"
down_revision = "023_m10_archive_partitioning"
branch_labels = None
depends_on = None

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


def upgrade():
    # Create schema
    op.execute("CREATE SCHEMA IF NOT EXISTS m11_audit")

    # Main ops table - append-only skill execution log
    op.create_table(
        "ops",
        sa.Column("op_id", sa.String(64), primary_key=True),
        sa.Column("workflow_run_id", sa.String(128), nullable=False, index=True),
        sa.Column("op_index", sa.Integer(), nullable=False),
        sa.Column("op_type", sa.String(64), nullable=False),  # skill name
        sa.Column("skill_version", sa.String(32), nullable=True),
        sa.Column("args", JSONB, nullable=False),
        sa.Column("args_hash", sa.String(64), nullable=True),  # SHA256 for comparison
        sa.Column("result", JSONB, nullable=True),  # Filled after execution
        sa.Column("result_hash", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("transient", sa.Boolean(), nullable=False, server_default=sa.sql.expression.false()),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, server_default="default"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        schema="m11_audit",
    )

    # Composite unique index for workflow + op_index
    op.create_index(
        "idx_ops_workflow_op_index", "ops", ["workflow_run_id", "op_index"], unique=True, schema="m11_audit"
    )

    # Index for idempotency lookups
    op.create_index(
        "idx_ops_idempotency",
        "ops",
        ["idempotency_key"],
        schema="m11_audit",
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    # Index for tenant queries
    op.create_index("idx_ops_tenant_created", "ops", ["tenant_id", "created_at"], schema="m11_audit")

    # Replay runs table - track verification runs
    op.create_table(
        "replay_runs",
        sa.Column("replay_id", sa.String(64), primary_key=True),
        sa.Column("workflow_run_id", sa.String(128), nullable=False, index=True),
        sa.Column("mode", sa.String(32), nullable=False),  # 'verify', 'rehydrate', 'dry_run'
        sa.Column("status", sa.String(32), nullable=False, server_default="running"),
        sa.Column("ops_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ops_verified", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ops_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ops_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_mismatch_op_index", sa.Integer(), nullable=True),
        sa.Column("mismatch_diff", JSONB, nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        schema="m11_audit",
    )

    # Circuit breaker state table (persistent)
    op.create_table(
        "circuit_breaker_state",
        sa.Column("target", sa.String(128), primary_key=True),
        sa.Column("state", sa.String(16), nullable=False, server_default="CLOSED"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_failure_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("opened_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("cooldown_until", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="m11_audit",
    )

    # Metrics aggregation table (for Prometheus exposition)
    op.create_table(
        "skill_metrics",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("skill_name", sa.String(64), nullable=False),
        sa.Column("metric_name", sa.String(64), nullable=False),
        sa.Column("labels", JSONB, nullable=False, server_default="{}"),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="m11_audit",
    )

    op.create_index("idx_skill_metrics_skill_time", "skill_metrics", ["skill_name", "timestamp"], schema="m11_audit")

    # Function to get next op_index for a workflow
    op.execute(
        """
        CREATE OR REPLACE FUNCTION m11_audit.next_op_index(p_workflow_run_id TEXT)
        RETURNS INTEGER AS $$
        DECLARE
            v_next_index INTEGER;
        BEGIN
            SELECT COALESCE(MAX(op_index), 0) + 1 INTO v_next_index
            FROM m11_audit.ops
            WHERE workflow_run_id = p_workflow_run_id;
            RETURN v_next_index;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    # View for easy workflow summary
    op.execute(
        """
        CREATE OR REPLACE VIEW m11_audit.workflow_summary AS
        SELECT
            workflow_run_id,
            tenant_id,
            COUNT(*) as total_ops,
            COUNT(*) FILTER (WHERE status = 'completed') as completed_ops,
            COUNT(*) FILTER (WHERE status = 'failed') as failed_ops,
            COUNT(*) FILTER (WHERE transient = true) as transient_ops,
            MIN(created_at) as started_at,
            MAX(completed_at) as last_op_at,
            SUM(duration_ms) as total_duration_ms
        FROM m11_audit.ops
        GROUP BY workflow_run_id, tenant_id;
    """
    )

    # Comment for documentation
    op.execute(
        """
        COMMENT ON TABLE m11_audit.ops IS
        'Append-only skill operation log for M11 deterministic replay. '
        'Each row represents a single skill invocation with monotonic op_index per workflow.';
    """
    )

    op.execute(
        """
        COMMENT ON TABLE m11_audit.replay_runs IS
        'Tracks replay verification runs for determinism testing. '
        'Records mismatch details when replay diverges from recorded execution.';
    """
    )


def downgrade():
    op.execute("DROP VIEW IF EXISTS m11_audit.workflow_summary")
    op.execute("DROP FUNCTION IF EXISTS m11_audit.next_op_index(TEXT)")
    op.drop_table("skill_metrics", schema="m11_audit")
    op.drop_table("circuit_breaker_state", schema="m11_audit")
    op.drop_table("replay_runs", schema="m11_audit")
    op.drop_table("ops", schema="m11_audit")
    op.execute("DROP SCHEMA IF EXISTS m11_audit")
