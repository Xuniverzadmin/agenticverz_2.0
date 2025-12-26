"""Create contracts schema and decision_records table

Phase 5E-1: Founder Decision Timeline Infrastructure

This migration creates the contracts.decision_records table
to enable founder visibility of all system decisions.

Revision ID: 001_contracts_decision_records
Revises: None
Create Date: 2025-12-26
"""

from alembic import op

# revision identifiers
revision = "001_contracts_decision_records"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create contracts schema and decision_records table."""

    # Create contracts schema
    op.execute("CREATE SCHEMA IF NOT EXISTS contracts")

    # Create decision_records table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS contracts.decision_records (
            id SERIAL PRIMARY KEY,
            decision_id VARCHAR(64) NOT NULL UNIQUE,
            decision_type VARCHAR(32) NOT NULL,
            decision_source VARCHAR(32) NOT NULL,
            decision_trigger VARCHAR(32) NOT NULL,
            decision_inputs JSONB DEFAULT '{}'::jsonb,
            decision_outcome VARCHAR(32) NOT NULL,
            decision_reason TEXT,
            run_id VARCHAR(64),
            workflow_id VARCHAR(64),
            tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
            request_id VARCHAR(64),
            causal_role VARCHAR(16) NOT NULL DEFAULT 'in_run',
            decided_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            details JSONB DEFAULT '{}'::jsonb
        )
    """
    )

    # Create indexes for query performance
    op.execute("CREATE INDEX IF NOT EXISTS ix_decision_records_run ON contracts.decision_records(run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_decision_records_request ON contracts.decision_records(request_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_decision_records_tenant ON contracts.decision_records(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_decision_records_type ON contracts.decision_records(decision_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_decision_records_time ON contracts.decision_records(decided_at)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_decision_records_causal ON contracts.decision_records(causal_role, decided_at)"
    )


def downgrade() -> None:
    """Drop contracts schema and all its objects."""
    op.execute("DROP TABLE IF EXISTS contracts.decision_records")
    op.execute("DROP SCHEMA IF EXISTS contracts")
