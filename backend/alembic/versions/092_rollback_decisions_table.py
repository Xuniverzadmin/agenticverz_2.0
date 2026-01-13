# Layer: L6 — Platform Substrate
# Product: ai-console
# Temporal:
#   Trigger: alembic upgrade
#   Execution: sync
# Role: Rollback decisions table - architectural correction
# Reference: PIN-413 Correction — Overview must be projection-only

"""
092 — Rollback decisions table

Architectural correction: The `decisions` table violated frozen intent.

Overview must be a PURE PROJECTION LAYER, not a new source of truth.
Decisions are not first-class objects — they are derived visibility
over existing domain objects (incidents, proposals, limit_breaches).

This migration:
- REMOVES the `decisions` table
- KEEPS the `audit_ledger` table (correctly scoped to Logs domain)

Revision ID: 092_rollback_decisions
Revises: 091_decisions_audit_ledger
Create Date: 2026-01-13
"""

from alembic import op
import sqlalchemy as sa

revision = "092_rollback_decisions"
down_revision = "091_decisions_audit_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove decisions table - Overview must be projection-only."""

    # Drop check constraints
    op.drop_constraint("ck_decisions_source_domain", "decisions", type_="check")
    op.drop_constraint("ck_decisions_decision_type", "decisions", type_="check")
    op.drop_constraint("ck_decisions_priority", "decisions", type_="check")
    op.drop_constraint("ck_decisions_status", "decisions", type_="check")

    # Drop partial unique index
    op.execute("DROP INDEX IF EXISTS uq_decisions_pending_entity")

    # Drop indexes
    op.drop_index("idx_decisions_source_domain", table_name="decisions")
    op.drop_index("idx_decisions_entity", table_name="decisions")
    op.drop_index("idx_decisions_tenant_priority", table_name="decisions")
    op.drop_index("idx_decisions_tenant_status", table_name="decisions")

    # Drop table
    op.drop_table("decisions")


def downgrade() -> None:
    """Re-create decisions table (not recommended - violates architecture)."""

    op.create_table(
        "decisions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(64),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("decision_type", sa.String(32), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("priority", sa.String(16), nullable=False, server_default="MEDIUM"),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("requested_by", sa.String(64), nullable=True),
        sa.Column("source_domain", sa.String(32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(64), nullable=True),
    )

    op.create_index(
        "idx_decisions_tenant_status",
        "decisions",
        ["tenant_id", "status"],
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

    op.execute(
        """
        CREATE UNIQUE INDEX uq_decisions_pending_entity
        ON decisions (entity_type, entity_id)
        WHERE status = 'PENDING';
        """
    )

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
