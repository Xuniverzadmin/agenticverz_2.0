# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Create GC_L Audit Log with immutability enforcement per PIN-341
# Reference: PIN-341, PIN-342, PIN-343, PIN-345

"""Create GC_L Audit Log with immutability enforcement

Revision ID: 069_create_gcl_audit_log
Revises: 068_create_gcl_policy_library
Create Date: 2026-01-07
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision = "069_create_gcl_audit_log"
down_revision = "068_create_gcl_policy_library"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create GC_L Audit Log per PIN-341 Section 3:
    - Append-only immutable log
    - Hash chain for tamper evidence
    - Triggers to prevent UPDATE/DELETE
    """

    # =========================================================================
    # Table: gcl_audit_log
    # Purpose: Immutable audit trail for all GC_L interactions
    # Reference: PIN-341 Section 3.2, 3.3
    # =========================================================================
    op.create_table(
        "gcl_audit_log",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.TIMESTAMP(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_type", sa.Text(), nullable=False),  # HUMAN | SYSTEM_FACILITATION
        sa.Column("capability_id", sa.Text(), nullable=False),  # CAP-XXX
        sa.Column("intent", sa.Text(), nullable=False),  # CONFIGURE | ACTIVATE | PAUSE | DISABLE | SIMULATE
        sa.Column(
            "object_type", sa.Text(), nullable=False
        ),  # POLICY | INTEGRATION | SPEND_GUARD | KILLSWITCH | PREFERENCE
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("object_version", sa.Integer(), nullable=False),
        # Hash chain fields per PIN-342
        sa.Column("previous_state_hash", sa.Text(), nullable=True),  # NULL for creates
        sa.Column("new_state_hash", sa.Text(), nullable=False),
        sa.Column("chain_hash", sa.Text(), nullable=True),  # Running hash chain per PIN-343
        # Governance fields
        sa.Column("confirmation", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("evidence_refs", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        # Primary key
        sa.PrimaryKeyConstraint("event_id"),
        # Constraints per PIN-341
        sa.CheckConstraint("actor_type IN ('HUMAN', 'SYSTEM_FACILITATION')", name="ck_gcl_audit_valid_actor_type"),
        sa.CheckConstraint(
            "intent IN ('CONFIGURE', 'ACTIVATE', 'PAUSE', 'DISABLE', 'SIMULATE', 'MODE_CHANGE')",
            name="ck_gcl_audit_valid_intent",
        ),
        sa.CheckConstraint(
            "object_type IN ('POLICY', 'INTEGRATION', 'SPEND_GUARD', 'KILLSWITCH', 'PREFERENCE')",
            name="ck_gcl_audit_valid_object_type",
        ),
        sa.CheckConstraint("confirmation = true", name="ck_gcl_audit_requires_confirmation"),
    )

    # Indexes for replay queries per PIN-341 Section 3.2
    op.create_index("idx_gcl_audit_tenant_time", "gcl_audit_log", ["tenant_id", "timestamp"])
    op.create_index("idx_gcl_audit_actor", "gcl_audit_log", ["actor_id", "timestamp"])
    op.create_index("idx_gcl_audit_object", "gcl_audit_log", ["object_type", "object_id", "timestamp"])
    op.create_index("idx_gcl_audit_capability", "gcl_audit_log", ["capability_id", "timestamp"])
    op.create_index("idx_gcl_audit_intent", "gcl_audit_log", ["intent", "timestamp"])
    op.create_index(
        "idx_gcl_audit_chain",
        "gcl_audit_log",
        ["tenant_id", "chain_hash"],
        postgresql_where=sa.text("chain_hash IS NOT NULL"),
    )

    # =========================================================================
    # Immutability Enforcement per PIN-341 Section 3.3
    # ABSOLUTE: No UPDATE, No DELETE
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_gcl_audit_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'GCL-IMMUTABLE-001: GCL audit log is immutable - no UPDATE or DELETE allowed. Reference: PIN-341 Section 3.3';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER gcl_audit_immutable_update
        BEFORE UPDATE ON gcl_audit_log
        FOR EACH ROW EXECUTE FUNCTION prevent_gcl_audit_mutation();
    """)

    op.execute("""
        CREATE TRIGGER gcl_audit_immutable_delete
        BEFORE DELETE ON gcl_audit_log
        FOR EACH ROW EXECUTE FUNCTION prevent_gcl_audit_mutation();
    """)

    # =========================================================================
    # Table: gcl_replay_requests
    # Purpose: Track replay query requests (read-only audit)
    # Reference: PIN-341 Section 3.4
    # =========================================================================
    op.create_table(
        "gcl_replay_requests",
        sa.Column(
            "replay_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("time_range_start", sa.TIMESTAMP(), nullable=False),
        sa.Column("time_range_end", sa.TIMESTAMP(), nullable=False),
        sa.Column("filters", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("derived_view", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("events_returned", sa.Integer(), nullable=True),
        sa.Column("summary", postgresql.JSONB(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        # Primary key
        sa.PrimaryKeyConstraint("replay_id"),
    )

    # Indexes for replay requests
    op.create_index("idx_gcl_replay_tenant", "gcl_replay_requests", ["tenant_id", "requested_at"])
    op.create_index("idx_gcl_replay_actor", "gcl_replay_requests", ["requested_by", "requested_at"])


def downgrade() -> None:
    """Remove GC_L Audit Log tables"""

    # Drop indexes
    op.drop_index("idx_gcl_replay_actor", "gcl_replay_requests")
    op.drop_index("idx_gcl_replay_tenant", "gcl_replay_requests")

    # Drop replay requests table
    op.drop_table("gcl_replay_requests")

    # Drop triggers and function
    op.execute("DROP TRIGGER IF EXISTS gcl_audit_immutable_delete ON gcl_audit_log;")
    op.execute("DROP TRIGGER IF EXISTS gcl_audit_immutable_update ON gcl_audit_log;")
    op.execute("DROP FUNCTION IF EXISTS prevent_gcl_audit_mutation();")

    # Drop indexes
    op.drop_index("idx_gcl_audit_chain", "gcl_audit_log")
    op.drop_index("idx_gcl_audit_intent", "gcl_audit_log")
    op.drop_index("idx_gcl_audit_capability", "gcl_audit_log")
    op.drop_index("idx_gcl_audit_object", "gcl_audit_log")
    op.drop_index("idx_gcl_audit_actor", "gcl_audit_log")
    op.drop_index("idx_gcl_audit_tenant_time", "gcl_audit_log")

    # Drop main table
    op.drop_table("gcl_audit_log")
