"""
C4 Coordination Audit Persistence.

Adds coordination_audit_records table for C5 learning observability.
Does NOT change C4 coordination behavior.

Reference: C4_COORDINATION_AUDIT_SCHEMA.md, PIN-232
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "063_c4_coordination_audit"
down_revision = "062_c5_learning_suggestions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create coordination_audit_records table
    op.create_table(
        "coordination_audit_records",
        sa.Column(
            "audit_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Envelope identification
        sa.Column("envelope_id", sa.String(100), nullable=False),
        sa.Column("envelope_class", sa.String(20), nullable=False),
        # Decision outcome
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        # Timing
        sa.Column(
            "decision_timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Conflict context (nullable)
        sa.Column("conflicting_envelope_id", sa.String(100), nullable=True),
        sa.Column("preempting_envelope_id", sa.String(100), nullable=True),
        # State snapshot
        sa.Column(
            "active_envelopes_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        # Multi-tenancy (optional)
        sa.Column("tenant_id", sa.String(100), nullable=True),
        # Constraints
        sa.CheckConstraint(
            "envelope_class IN ('SAFETY', 'RELIABILITY', 'COST', 'PERFORMANCE')",
            name="audit_envelope_class_valid",
        ),
        sa.CheckConstraint(
            "decision IN ('APPLIED', 'REJECTED', 'PREEMPTED')",
            name="audit_decision_valid",
        ),
    )

    # 2. Create indexes
    op.create_index(
        "ix_coord_audit_envelope_id",
        "coordination_audit_records",
        ["envelope_id"],
    )
    op.create_index(
        "ix_coord_audit_timestamp",
        "coordination_audit_records",
        ["decision_timestamp"],
    )
    op.create_index(
        "ix_coord_audit_class",
        "coordination_audit_records",
        ["envelope_class"],
    )
    op.create_index(
        "ix_coord_audit_decision",
        "coordination_audit_records",
        ["decision"],
    )
    op.create_index(
        "ix_coord_audit_tenant",
        "coordination_audit_records",
        ["tenant_id"],
    )

    # 3. Create immutability trigger
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_coordination_audit_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'coordination_audit_records are immutable. Updates forbidden.';
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER coordination_audit_immutable
            BEFORE UPDATE ON coordination_audit_records
            FOR EACH ROW
            EXECUTE FUNCTION prevent_coordination_audit_mutation();
    """
    )


def downgrade() -> None:
    # 1. Drop trigger first
    op.execute("DROP TRIGGER IF EXISTS coordination_audit_immutable ON coordination_audit_records;")
    op.execute("DROP FUNCTION IF EXISTS prevent_coordination_audit_mutation();")

    # 2. Drop indexes
    op.drop_index("ix_coord_audit_tenant", table_name="coordination_audit_records")
    op.drop_index("ix_coord_audit_decision", table_name="coordination_audit_records")
    op.drop_index("ix_coord_audit_class", table_name="coordination_audit_records")
    op.drop_index("ix_coord_audit_timestamp", table_name="coordination_audit_records")
    op.drop_index("ix_coord_audit_envelope_id", table_name="coordination_audit_records")

    # 3. Drop table
    op.drop_table("coordination_audit_records")
