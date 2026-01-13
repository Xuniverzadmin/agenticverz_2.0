# Layer: L6 — Platform Substrate
# Product: ai-console
# Temporal:
#   Trigger: alembic upgrade
#   Execution: sync
# Role: Create decisions and audit_ledger tables for Overview + Logs domains
# Reference: PIN-413 Domain Design — Overview & Logs

"""
091 — Decisions and Audit Ledger Tables

Creates core primitives for Overview and Logs domains:
- decisions: Decision queue for actionable items (Overview backbone)
- audit_ledger: Immutable governance action log (Logs backbone)

Contract Rules:
- decisions tracks PENDING items requiring human/system action
- audit_ledger is APPEND-ONLY (no UPDATE, no DELETE)
- Both are tenant-isolated
- Both support the canonical event/decision types

Revision ID: 091_decisions_audit_ledger
Revises: 090_limit_integrity
Create Date: 2026-01-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "091_decisions_audit_ledger"
down_revision = "090_limit_integrity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # 1. decisions table — Overview backbone
    # ==========================================================================
    op.create_table(
        "decisions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(64),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Decision classification
        sa.Column("decision_type", sa.String(32), nullable=False),
        # POLICY_APPROVAL | INCIDENT_ACK | LIMIT_OVERRIDE | EMERGENCY_ACTION
        sa.Column("entity_type", sa.String(32), nullable=False),
        # POLICY_PROPOSAL | INCIDENT | LIMIT | SYSTEM
        sa.Column("entity_id", sa.String(64), nullable=False),
        # Decision state
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        # PENDING | APPROVED | REJECTED | ACKED | AUTO_RESOLVED
        sa.Column("priority", sa.String(16), nullable=False, server_default="MEDIUM"),
        # CRITICAL | HIGH | MEDIUM | LOW
        # Metadata
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("requested_by", sa.String(64), nullable=True),
        sa.Column("source_domain", sa.String(32), nullable=False),
        # INCIDENT | POLICY | LIMIT | SYSTEM
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(64), nullable=True),
    )

    # decisions indexes
    op.create_index(
        "idx_decisions_tenant_status",
        "decisions",
        ["tenant_id", "status"],
        postgresql_where=sa.text("status = 'PENDING'"),
    )
    op.create_index(
        "idx_decisions_tenant_priority",
        "decisions",
        ["tenant_id", "priority", "created_at"],
    )
    op.create_index(
        "idx_decisions_entity",
        "decisions",
        ["entity_type", "entity_id"],
    )
    op.create_index(
        "idx_decisions_source_domain",
        "decisions",
        ["tenant_id", "source_domain"],
    )

    # Unique constraint: one PENDING decision per entity (partial unique index)
    op.execute(
        """
        CREATE UNIQUE INDEX uq_decisions_pending_entity
        ON decisions (entity_type, entity_id)
        WHERE status = 'PENDING';
        """
    )

    # ==========================================================================
    # 2. audit_ledger table — Logs backbone (APPEND-ONLY)
    # ==========================================================================
    op.create_table(
        "audit_ledger",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(64),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Event classification
        sa.Column("event_type", sa.String(64), nullable=False),
        # Canonical events only (enforced by application)
        sa.Column("entity_type", sa.String(32), nullable=False),
        # POLICY_RULE | POLICY_PROPOSAL | LIMIT | INCIDENT | DECISION
        sa.Column("entity_id", sa.String(64), nullable=False),
        # Actor information
        sa.Column("actor_type", sa.String(16), nullable=False),
        # HUMAN | SYSTEM | AGENT
        sa.Column("actor_id", sa.String(64), nullable=True),
        # Reason / justification
        sa.Column("action_reason", sa.Text, nullable=True),
        # State snapshots (for MODIFY events)
        sa.Column("before_state", JSONB, nullable=True),
        sa.Column("after_state", JSONB, nullable=True),
        # Timestamp (immutable once written)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # audit_ledger indexes
    op.create_index(
        "idx_audit_ledger_tenant_created",
        "audit_ledger",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "idx_audit_ledger_event_type",
        "audit_ledger",
        ["tenant_id", "event_type"],
    )
    op.create_index(
        "idx_audit_ledger_entity",
        "audit_ledger",
        ["entity_type", "entity_id"],
    )
    op.create_index(
        "idx_audit_ledger_actor",
        "audit_ledger",
        ["tenant_id", "actor_type", "actor_id"],
    )

    # ==========================================================================
    # 3. Immutability trigger for audit_ledger (NO UPDATE, NO DELETE)
    # ==========================================================================
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_ledger_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'audit_ledger is immutable: UPDATE not allowed';
            ELSIF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'audit_ledger is immutable: DELETE not allowed';
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_audit_ledger_immutable
        BEFORE UPDATE OR DELETE ON audit_ledger
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_ledger_mutation();
        """
    )

    # ==========================================================================
    # 4. Check constraints for valid enum values
    # ==========================================================================
    op.create_check_constraint(
        "ck_decisions_status",
        "decisions",
        "status IN ('PENDING', 'APPROVED', 'REJECTED', 'ACKED', 'AUTO_RESOLVED')",
    )
    op.create_check_constraint(
        "ck_decisions_priority",
        "decisions",
        "priority IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')",
    )
    op.create_check_constraint(
        "ck_decisions_decision_type",
        "decisions",
        "decision_type IN ('POLICY_APPROVAL', 'INCIDENT_ACK', 'LIMIT_OVERRIDE', 'EMERGENCY_ACTION')",
    )
    op.create_check_constraint(
        "ck_decisions_source_domain",
        "decisions",
        "source_domain IN ('INCIDENT', 'POLICY', 'LIMIT', 'SYSTEM')",
    )
    op.create_check_constraint(
        "ck_audit_ledger_actor_type",
        "audit_ledger",
        "actor_type IN ('HUMAN', 'SYSTEM', 'AGENT')",
    )


def downgrade() -> None:
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS trg_audit_ledger_immutable ON audit_ledger")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_ledger_mutation()")

    # Drop check constraints
    op.drop_constraint("ck_audit_ledger_actor_type", "audit_ledger", type_="check")
    op.drop_constraint("ck_decisions_source_domain", "decisions", type_="check")
    op.drop_constraint("ck_decisions_decision_type", "decisions", type_="check")
    op.drop_constraint("ck_decisions_priority", "decisions", type_="check")
    op.drop_constraint("ck_decisions_status", "decisions", type_="check")

    # Drop partial unique index
    op.execute("DROP INDEX IF EXISTS uq_decisions_pending_entity")

    # Drop indexes
    op.drop_index("idx_audit_ledger_actor", table_name="audit_ledger")
    op.drop_index("idx_audit_ledger_entity", table_name="audit_ledger")
    op.drop_index("idx_audit_ledger_event_type", table_name="audit_ledger")
    op.drop_index("idx_audit_ledger_tenant_created", table_name="audit_ledger")

    op.drop_index("idx_decisions_source_domain", table_name="decisions")
    op.drop_index("idx_decisions_entity", table_name="decisions")
    op.drop_index("idx_decisions_tenant_priority", table_name="decisions")
    op.drop_index("idx_decisions_tenant_status", table_name="decisions")

    # Drop tables
    op.drop_table("audit_ledger")
    op.drop_table("decisions")
