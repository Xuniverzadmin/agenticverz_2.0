"""Phase 4B: Decision Records

Revision ID: 049_decision_records
Revises: 048_m29_anomaly_rules_alignment
Create Date: 2025-12-25

Creates contract-aligned decision records table per DECISION_RECORD_CONTRACT v0.2.

Every decision (routing, recovery, memory, policy, budget) emits a record here.
Append-only. No business logic. Just emission.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "049_decision_records"
down_revision = "048_m29_anomaly_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create contracts schema for Phase 4B artifacts
    op.execute("CREATE SCHEMA IF NOT EXISTS contracts")

    # Decision records table - contract-aligned sink
    op.create_table(
        "decision_records",
        # Identity
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("decision_id", sa.String(64), nullable=False, index=True),

        # Contract-mandated metadata (DECISION_RECORD_CONTRACT v0.2)
        sa.Column("decision_type", sa.String(32), nullable=False),  # routing | recovery | memory | policy | budget
        sa.Column("decision_source", sa.String(16), nullable=False),  # human | system | hybrid
        sa.Column("decision_trigger", sa.String(16), nullable=False),  # explicit | autonomous | reactive

        # Decision content
        sa.Column("decision_inputs", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("decision_outcome", sa.String(64), nullable=False),  # selected | rejected | skipped | blocked | none
        sa.Column("decision_reason", sa.Text(), nullable=True),

        # Context
        sa.Column("run_id", sa.String(64), nullable=True, index=True),
        sa.Column("workflow_id", sa.String(64), nullable=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, server_default="default"),

        # Timing
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),

        # Extended details (type-specific)
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default="{}"),

        schema="contracts",
    )

    # Indexes for common queries
    op.create_index("ix_decision_records_decided_at", "decision_records", ["decided_at"], schema="contracts")
    op.create_index("ix_decision_records_type", "decision_records", ["decision_type"], schema="contracts")
    op.create_index("ix_decision_records_run", "decision_records", ["run_id", "decided_at"], schema="contracts")
    op.create_index("ix_decision_records_tenant", "decision_records", ["tenant_id", "decided_at"], schema="contracts")


def downgrade() -> None:
    op.drop_table("decision_records", schema="contracts")
    op.execute("DROP SCHEMA IF EXISTS contracts")
