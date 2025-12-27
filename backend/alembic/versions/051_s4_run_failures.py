"""S4: LLM Failure Truth Schema

Revision ID: 051_s4_run_failures
Revises: 050_causal_binding
Create Date: 2025-12-26

PIN-196 Schema Requirements:
- run_failures: Authoritative failure fact persistence
- failure_evidence: Immutable evidence capture

Critical Invariant:
> A failed run must never appear as "successful" or "completed with results."
> Failure fact must be persisted BEFORE any classification or recovery action.

No retries, fallbacks, or silent healing in S4 scope.
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = "051_s4_run_failures"
down_revision = "048_m29_anomaly_rules"  # Skip 049/050 (decision records) - independent feature
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create run_failures table
    # Stores authoritative failure facts (PIN-196 AC-1)
    op.create_table(
        "run_failures",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column(
            "failure_type",
            sa.String(32),
            nullable=False,
            comment="timeout | exception | invalid_output",
        ),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True, comment="LLM request correlation ID"),
        sa.Column("duration_ms", sa.Integer, nullable=True, comment="Time until failure"),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["worker_runs.id"],
            name="fk_run_failures_run_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_run_failures_tenant_id",
            ondelete="CASCADE",
        ),
    )

    # Indexes for run_failures
    op.create_index("ix_run_failures_run_id", "run_failures", ["run_id"])
    op.create_index("ix_run_failures_tenant_id", "run_failures", ["tenant_id"])
    op.create_index("ix_run_failures_failure_type", "run_failures", ["failure_type"])
    op.create_index("ix_run_failures_created_at", "run_failures", ["created_at"])

    # Composite index for tenant-scoped queries
    op.create_index(
        "ix_run_failures_tenant_created",
        "run_failures",
        ["tenant_id", "created_at"],
    )

    # Create failure_evidence table
    # Stores immutable evidence for each failure (PIN-196 AC-3)
    op.create_table(
        "failure_evidence",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("failure_id", UUID, nullable=False),
        sa.Column(
            "evidence_type",
            sa.String(64),
            nullable=False,
            comment="llm_failure_capture | timeout_trace | exception_stack",
        ),
        sa.Column("evidence_data", JSONB, nullable=False),
        sa.Column(
            "is_immutable",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("TRUE"),
            comment="Evidence must never be mutated",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        # Foreign key constraint
        sa.ForeignKeyConstraint(
            ["failure_id"],
            ["run_failures.id"],
            name="fk_failure_evidence_failure_id",
            ondelete="CASCADE",
        ),
    )

    # Indexes for failure_evidence
    op.create_index("ix_failure_evidence_failure_id", "failure_evidence", ["failure_id"])
    op.create_index("ix_failure_evidence_type", "failure_evidence", ["evidence_type"])

    # Create check constraint to prevent evidence mutation
    # (Note: This is advisory - enforcement is in application layer)
    op.execute(
        """
        COMMENT ON TABLE run_failures IS
        'PIN-196 S4: Authoritative LLM failure facts. Failure MUST be persisted before any classification.';
    """
    )

    op.execute(
        """
        COMMENT ON TABLE failure_evidence IS
        'PIN-196 S4: Immutable failure evidence. Evidence MUST exist for every failure.';
    """
    )


def downgrade() -> None:
    op.drop_index("ix_failure_evidence_type", table_name="failure_evidence")
    op.drop_index("ix_failure_evidence_failure_id", table_name="failure_evidence")
    op.drop_table("failure_evidence")

    op.drop_index("ix_run_failures_tenant_created", table_name="run_failures")
    op.drop_index("ix_run_failures_created_at", table_name="run_failures")
    op.drop_index("ix_run_failures_failure_type", table_name="run_failures")
    op.drop_index("ix_run_failures_tenant_id", table_name="run_failures")
    op.drop_index("ix_run_failures_run_id", table_name="run_failures")
    op.drop_table("run_failures")
