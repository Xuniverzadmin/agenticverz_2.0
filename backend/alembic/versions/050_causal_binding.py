"""Phase 4B Extension: Decision Records Causal Binding

Revision ID: 050_decision_records_causal_binding
Revises: 049_decision_records
Create Date: 2025-12-25

Adds request_id and causal_role to decision_records for temporal truth.

The Problem:
  - Pre-run decisions (routing, policy, memory) are emitted BEFORE run exists
  - run_id is NULL at emission time
  - Founder cannot trace causality from run back to pre-run decisions

The Fix:
  - request_id: First-class causal key (always present for pre-run)
  - causal_role: Declares when in lifecycle decision occurred
  - run_id backfill: Bind decisions when run is created

This is context enrichment, not mutation.
"""

import sqlalchemy as sa

from alembic import op

revision = "050_decision_records_causal_binding"
down_revision = "049_decision_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add request_id column (nullable, indexed)
    # Pre-run decisions have request_id but no run_id
    op.add_column(
        "decision_records",
        sa.Column("request_id", sa.String(64), nullable=True),
        schema="contracts",
    )
    op.create_index(
        "ix_decision_records_request",
        "decision_records",
        ["request_id"],
        schema="contracts",
    )

    # Add causal_role column
    # Declares when in lifecycle this decision occurred
    op.add_column(
        "decision_records",
        sa.Column(
            "causal_role",
            sa.String(16),
            nullable=False,
            server_default="in_run",
        ),
        schema="contracts",
    )
    op.create_index(
        "ix_decision_records_causal",
        "decision_records",
        ["causal_role", "decided_at"],
        schema="contracts",
    )

    # Composite index for run_id backfill query
    # Used when binding pre-run decisions to newly created run
    op.create_index(
        "ix_decision_records_backfill",
        "decision_records",
        ["request_id", "run_id"],
        schema="contracts",
        postgresql_where=sa.text("run_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_decision_records_backfill", table_name="decision_records", schema="contracts")
    op.drop_index("ix_decision_records_causal", table_name="decision_records", schema="contracts")
    op.drop_index("ix_decision_records_request", table_name="decision_records", schema="contracts")
    op.drop_column("decision_records", "causal_role", schema="contracts")
    op.drop_column("decision_records", "request_id", schema="contracts")
