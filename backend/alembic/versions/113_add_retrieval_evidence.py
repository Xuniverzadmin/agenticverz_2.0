"""Add retrieval_evidence table for mediated data access audit

Revision ID: 113_add_retrieval_evidence
Revises: 112_runs_observability_status
Create Date: 2026-01-21

Reference: GAP-058 (RetrievalEvidence Model)

This migration creates the retrieval_evidence table which serves as
an immutable audit log for all data access through the mediation layer.
A database trigger enforces immutability by preventing UPDATE/DELETE.

Purpose:
- SOC2 compliance audit trail
- Forensic analysis of data access patterns
- Token usage tracking per retrieval
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "113_add_retrieval_evidence"
down_revision = "112_runs_observability_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the retrieval_evidence table
    op.create_table(
        "retrieval_evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("run_id", sa.String(100), nullable=False, index=True),
        sa.Column("plane_id", sa.String(100), nullable=False, index=True),
        sa.Column("connector_id", sa.String(100), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("query_hash", sa.String(64), nullable=False),
        sa.Column("doc_ids", JSONB, nullable=False, server_default="[]"),
        sa.Column("token_count", sa.Integer, nullable=False, default=0),
        sa.Column("policy_snapshot_id", sa.String(100), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create composite index for common query patterns
    op.create_index(
        "ix_retrieval_evidence_tenant_run",
        "retrieval_evidence",
        ["tenant_id", "run_id"],
    )

    # Create index on query_hash for deduplication queries
    op.create_index(
        "ix_retrieval_evidence_query_hash",
        "retrieval_evidence",
        ["query_hash"],
    )

    # Create index on requested_at for time-range queries
    op.create_index(
        "ix_retrieval_evidence_requested_at",
        "retrieval_evidence",
        ["requested_at"],
    )

    # Create the immutability trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_retrieval_evidence_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'retrieval_evidence is immutable. UPDATE and DELETE are forbidden. (GAP-058)';
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create the trigger that prevents UPDATE and DELETE
    op.execute("""
        CREATE TRIGGER retrieval_evidence_immutable
            BEFORE UPDATE OR DELETE ON retrieval_evidence
            FOR EACH ROW
            EXECUTE FUNCTION prevent_retrieval_evidence_mutation();
    """)

    # Add comment to table
    op.execute("""
        COMMENT ON TABLE retrieval_evidence IS
        'Immutable audit log for mediated data access (GAP-058). Every access through the mediation layer creates one record. SOC2 compliance.';
    """)


def downgrade() -> None:
    # Drop the immutability trigger first
    op.execute("DROP TRIGGER IF EXISTS retrieval_evidence_immutable ON retrieval_evidence;")

    # Drop the trigger function
    op.execute("DROP FUNCTION IF EXISTS prevent_retrieval_evidence_mutation();")

    # Drop indexes
    op.drop_index("ix_retrieval_evidence_requested_at", table_name="retrieval_evidence")
    op.drop_index("ix_retrieval_evidence_query_hash", table_name="retrieval_evidence")
    op.drop_index("ix_retrieval_evidence_tenant_run", table_name="retrieval_evidence")

    # Drop the table
    op.drop_table("retrieval_evidence")
