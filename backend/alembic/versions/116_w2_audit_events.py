# Layer: L6 — Platform (Database Migration)
# Product: system-wide
# Reference: GAP-166 (T2 Audit Events)
"""Add audit_events table for T2 compliance audit

Revision ID: 116_w2_audit_events
Revises: 115_add_inflection_point_metadata
Create Date: 2026-01-21

Reference: GAP-166 (T2 Audit Events), GAP_IMPLEMENTATION_PLAN_V2.md

This migration creates the audit_events table for T2 (Trust & Evidence) tier.
Unlike audit_log which captures user actions, audit_events captures system-level
governance events for compliance reporting.

Purpose:
- SOC2 compliance evidence
- Governance event capture (policy enforcement, budget checks, capability toggles)
- Tamper-evident audit trail with immutability trigger
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers
revision = "116_w2_audit_events"
down_revision = "115_add_inflection_point_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Create audit_events table (GAP-166)
    # =========================================================================
    op.create_table(
        "audit_events",
        # Primary key
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        # Identity
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column("event_id", sa.String(64), nullable=False, unique=True),
        # Event classification
        sa.Column(
            "event_type",
            sa.String(64),
            nullable=False,
            comment="Type: policy_check, budget_check, capability_toggle, state_transition, etc.",
        ),
        sa.Column(
            "event_category",
            sa.String(32),
            nullable=False,
            comment="Category: governance, security, lifecycle, execution",
        ),
        sa.Column(
            "severity",
            sa.String(16),
            nullable=False,
            server_default="info",
            comment="Severity: debug, info, warn, error, critical",
        ),
        # Context
        sa.Column("run_id", sa.String(100), nullable=True, index=True),
        sa.Column("step_index", sa.Integer(), nullable=True),
        sa.Column("plane_id", sa.String(100), nullable=True, index=True),
        sa.Column("job_id", sa.String(100), nullable=True, index=True),
        # Actor information
        sa.Column(
            "actor_id",
            sa.String(100),
            nullable=True,
            comment="User ID, system ID, or service name",
        ),
        sa.Column(
            "actor_type",
            sa.String(32),
            nullable=False,
            server_default="system",
            comment="Actor type: human, machine, system",
        ),
        # Event details
        sa.Column("action", sa.String(128), nullable=False, comment="Action performed"),
        sa.Column("resource_type", sa.String(64), nullable=True, comment="Resource type affected"),
        sa.Column("resource_id", sa.String(256), nullable=True, comment="Resource identifier"),
        sa.Column("outcome", sa.String(32), nullable=False, comment="Outcome: success, failure, blocked, skipped"),
        # Evidence
        sa.Column("evidence", JSONB, nullable=True, comment="Structured evidence payload"),
        sa.Column("context", JSONB, nullable=True, comment="Additional context"),
        # Policy reference
        sa.Column("policy_id", sa.String(64), nullable=True, comment="Policy that was evaluated"),
        sa.Column("policy_snapshot_id", sa.String(64), nullable=True, comment="Policy snapshot at time of event"),
        # Error details (for failures)
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Timestamps
        sa.Column(
            "occurred_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            comment="When the event occurred",
        ),
        sa.Column(
            "recorded_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="When the event was recorded",
        ),
    )

    # Create indexes for common query patterns
    op.create_index(
        "ix_audit_events_tenant_occurred",
        "audit_events",
        ["tenant_id", sa.text("occurred_at DESC")],
    )
    op.create_index(
        "ix_audit_events_event_type",
        "audit_events",
        ["event_type"],
    )
    op.create_index(
        "ix_audit_events_category_severity",
        "audit_events",
        ["event_category", "severity"],
    )
    op.create_index(
        "ix_audit_events_outcome",
        "audit_events",
        ["outcome"],
        postgresql_where=sa.text("outcome IN ('failure', 'blocked')"),
    )
    op.create_index(
        "ix_audit_events_occurred_at",
        "audit_events",
        ["occurred_at"],
    )

    # Create immutability trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_event_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_events is immutable. UPDATE and DELETE are forbidden. (GAP-166)';
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create the trigger that prevents UPDATE and DELETE
    op.execute("""
        CREATE TRIGGER audit_events_immutable
            BEFORE UPDATE OR DELETE ON audit_events
            FOR EACH ROW
            EXECUTE FUNCTION prevent_audit_event_mutation();
    """)

    # Add comment to table
    op.execute("""
        COMMENT ON TABLE audit_events IS
        'Immutable T2 governance event log (GAP-166). Captures policy enforcement, budget checks, capability toggles, and state transitions. SOC2 compliance evidence.';
    """)

    # Create check constraint for event_category
    op.create_check_constraint(
        "ck_audit_events_category",
        "audit_events",
        "event_category IN ('governance', 'security', 'lifecycle', 'execution', 'configuration')",
    )

    # Create check constraint for severity
    op.create_check_constraint(
        "ck_audit_events_severity",
        "audit_events",
        "severity IN ('debug', 'info', 'warn', 'error', 'critical')",
    )

    # Create check constraint for actor_type
    op.create_check_constraint(
        "ck_audit_events_actor_type",
        "audit_events",
        "actor_type IN ('human', 'machine', 'system')",
    )

    # Create check constraint for outcome
    op.create_check_constraint(
        "ck_audit_events_outcome",
        "audit_events",
        "outcome IN ('success', 'failure', 'blocked', 'skipped', 'pending')",
    )


def downgrade() -> None:
    # Drop constraints
    op.drop_constraint("ck_audit_events_outcome", "audit_events", type_="check")
    op.drop_constraint("ck_audit_events_actor_type", "audit_events", type_="check")
    op.drop_constraint("ck_audit_events_severity", "audit_events", type_="check")
    op.drop_constraint("ck_audit_events_category", "audit_events", type_="check")

    # Drop the immutability trigger
    op.execute("DROP TRIGGER IF EXISTS audit_events_immutable ON audit_events;")

    # Drop the trigger function
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_event_mutation();")

    # Drop indexes
    op.drop_index("ix_audit_events_occurred_at", table_name="audit_events")
    op.drop_index("ix_audit_events_outcome", table_name="audit_events")
    op.drop_index("ix_audit_events_category_severity", table_name="audit_events")
    op.drop_index("ix_audit_events_event_type", table_name="audit_events")
    op.drop_index("ix_audit_events_tenant_occurred", table_name="audit_events")

    # Drop the table
    op.drop_table("audit_events")
