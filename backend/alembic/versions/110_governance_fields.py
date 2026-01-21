"""Add governance fields for cross-domain data flow

Revision ID: 110_governance_fields
Revises: 109_logs_domain_v2
Create Date: 2026-01-20

Reference: BACKEND_REMEDIATION_PLAN.md

This migration implements governance fields required for the cross-domain data flow:
1. Creates policy_snapshots table (GAP-006)
2. Adds governance fields to runs table (GAP-001, GAP-002, GAP-007)
3. Adds inflection point fields to aos_traces table (GAP-003)
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "110_governance_fields"
down_revision = "109_logs_domain_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # 1. Create policy_snapshots table (GAP-006)
    # =========================================================================
    op.create_table(
        "policy_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("snapshot_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("tenant_id", sa.String(64), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        # Snapshot content (JSON serialized)
        sa.Column("policies_json", sa.Text(), nullable=False),
        sa.Column("thresholds_json", sa.Text(), nullable=False),
        # Integrity
        sa.Column("content_hash", sa.String(64), nullable=False),
        # Metadata
        sa.Column("policy_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Index for policy_snapshots
    op.create_index(
        "idx_policy_snapshots_tenant_created",
        "policy_snapshots",
        ["tenant_id", sa.text("created_at DESC")],
    )

    # Immutability trigger for policy_snapshots
    op.execute("""
        CREATE OR REPLACE FUNCTION reject_policy_snapshot_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'policy_snapshots is immutable: UPDATE and DELETE are forbidden';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS policy_snapshots_immutable ON policy_snapshots;
        CREATE TRIGGER policy_snapshots_immutable
        BEFORE UPDATE OR DELETE ON policy_snapshots
        FOR EACH ROW
        EXECUTE FUNCTION reject_policy_snapshot_mutation();
    """)

    # =========================================================================
    # 2. Add governance fields to runs table (GAP-001, GAP-002, GAP-007)
    # =========================================================================

    # Policy snapshot reference (GAP-006)
    op.add_column(
        "runs",
        sa.Column("policy_snapshot_id", sa.String(64), nullable=True),
    )
    op.create_index(
        "idx_runs_policy_snapshot_id",
        "runs",
        ["policy_snapshot_id"],
    )

    # Termination tracking (GAP-002, GAP-007)
    op.add_column(
        "runs",
        sa.Column("termination_reason", sa.String(32), nullable=True),
    )
    op.add_column(
        "runs",
        sa.Column("stopped_at_step", sa.Integer(), nullable=True),
    )
    op.add_column(
        "runs",
        sa.Column("violation_policy_id", sa.String(64), nullable=True),
    )

    # Check constraint for termination_reason values
    op.create_check_constraint(
        "ck_runs_termination_reason",
        "runs",
        """termination_reason IS NULL OR termination_reason IN (
            'completed', 'policy_block', 'budget_exceeded', 'rate_limited',
            'user_abort', 'system_failure', 'timeout'
        )""",
    )

    # =========================================================================
    # 3. Add inflection point fields to aos_traces table (GAP-003)
    # =========================================================================

    op.add_column(
        "aos_traces",
        sa.Column("violation_step_index", sa.Integer(), nullable=True),
    )
    op.add_column(
        "aos_traces",
        sa.Column("violation_timestamp", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "aos_traces",
        sa.Column("violation_policy_id", sa.String(64), nullable=True),
    )
    op.add_column(
        "aos_traces",
        sa.Column("violation_reason", sa.String(512), nullable=True),
    )

    # Index for finding traces with violations
    op.create_index(
        "idx_aos_traces_violation",
        "aos_traces",
        ["tenant_id", "violation_step_index"],
        postgresql_where=sa.text("violation_step_index IS NOT NULL"),
    )


def downgrade() -> None:
    # Remove aos_traces columns
    op.drop_index("idx_aos_traces_violation", table_name="aos_traces")
    op.drop_column("aos_traces", "violation_reason")
    op.drop_column("aos_traces", "violation_policy_id")
    op.drop_column("aos_traces", "violation_timestamp")
    op.drop_column("aos_traces", "violation_step_index")

    # Remove runs columns
    op.drop_constraint("ck_runs_termination_reason", "runs", type_="check")
    op.drop_column("runs", "violation_policy_id")
    op.drop_column("runs", "stopped_at_step")
    op.drop_column("runs", "termination_reason")
    op.drop_index("idx_runs_policy_snapshot_id", table_name="runs")
    op.drop_column("runs", "policy_snapshot_id")

    # Remove policy_snapshots
    op.execute("DROP TRIGGER IF EXISTS policy_snapshots_immutable ON policy_snapshots")
    op.execute("DROP FUNCTION IF EXISTS reject_policy_snapshot_mutation()")
    op.drop_index("idx_policy_snapshots_tenant_created", table_name="policy_snapshots")
    op.drop_table("policy_snapshots")
