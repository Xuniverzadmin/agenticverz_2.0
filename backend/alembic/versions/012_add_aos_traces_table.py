"""Add aos_traces table for deterministic trace storage

Revision ID: 012_add_aos_traces
Revises: 011_create_memory_audit
Create Date: 2025-12-06

M8 Deliverable: Trace storage with PostgreSQL for production deployment
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision = "012_add_aos_traces"
down_revision = "011_create_memory_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create aos_traces table with indexes for fast lookup
    op.create_table(
        "aos_traces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("trace_id", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("run_id", sa.String(64), nullable=False, index=True),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("agent_id", sa.String(64), nullable=True),
        sa.Column("plan_id", sa.String(64), nullable=True),
        # Determinism fields (v1.1)
        sa.Column("seed", sa.BigInteger(), nullable=True, default=42),
        sa.Column("frozen_timestamp", sa.String(64), nullable=True),
        sa.Column("root_hash", sa.String(64), nullable=False),
        sa.Column("plan_hash", sa.String(64), nullable=True),
        sa.Column("schema_version", sa.String(16), nullable=False, default="1.1"),
        # Trace data
        sa.Column("plan", postgresql.JSONB(), nullable=False),
        sa.Column("trace", postgresql.JSONB(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True, default={}),
        # Status
        sa.Column("status", sa.String(32), nullable=False, default="running"),
        # Timestamps
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        # Audit
        sa.Column("stored_by", sa.String(64), nullable=True),
    )

    # Create aos_trace_steps table
    op.create_table(
        "aos_trace_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("trace_id", sa.String(64), sa.ForeignKey("aos_traces.trace_id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.String(128), nullable=False),
        sa.Column("skill_name", sa.String(128), nullable=False),
        sa.Column("params", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("outcome_category", sa.String(64), nullable=False),
        sa.Column("outcome_code", sa.String(64), nullable=True),
        sa.Column("outcome_data", postgresql.JSONB(), nullable=True),
        # Cost and timing
        sa.Column("cost_cents", sa.Float(), nullable=False, default=0.0),
        sa.Column("duration_ms", sa.Float(), nullable=False, default=0.0),
        sa.Column("retry_count", sa.Integer(), nullable=False, default=0),
        # v1.1 determinism fields
        sa.Column("input_hash", sa.String(64), nullable=True),
        sa.Column("output_hash", sa.String(64), nullable=True),
        sa.Column("rng_state_before", sa.String(128), nullable=True),
        # v1.1 idempotency fields
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("replay_behavior", sa.String(16), nullable=False, default="execute"),
        # Timestamp
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # Create indexes for fast lookup
    op.create_index("idx_aos_traces_tenant", "aos_traces", ["tenant_id"])
    op.create_index("idx_aos_traces_root_hash", "aos_traces", ["root_hash"])
    op.create_index("idx_aos_traces_plan_hash", "aos_traces", ["plan_hash"])
    op.create_index("idx_aos_traces_seed", "aos_traces", ["seed"])
    op.create_index("idx_aos_traces_agent", "aos_traces", ["agent_id"])
    op.create_index("idx_aos_traces_status", "aos_traces", ["status"])
    op.create_index("idx_aos_traces_created_at", "aos_traces", ["created_at"])
    op.create_index("idx_aos_traces_run_id", "aos_traces", ["run_id"])

    # Step indexes
    op.create_index("idx_aos_trace_steps_trace", "aos_trace_steps", ["trace_id"])
    op.create_index("idx_aos_trace_steps_idempotency", "aos_trace_steps", ["idempotency_key"])
    op.create_index("idx_aos_trace_steps_composite", "aos_trace_steps", ["trace_id", "step_index"], unique=True)

    # Create archive table for retention lifecycle
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS aos_traces_archive (LIKE aos_traces INCLUDING ALL);
    """
    )
    op.create_index("idx_aos_traces_archive_root_hash", "aos_traces_archive", ["root_hash"])
    op.create_index("idx_aos_traces_archive_created_at", "aos_traces_archive", ["created_at"])


def downgrade() -> None:
    op.drop_table("aos_trace_steps")
    op.drop_table("aos_traces_archive")
    op.drop_table("aos_traces")
