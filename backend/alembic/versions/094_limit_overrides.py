# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: alembic upgrade
#   Execution: sync
# Role: Create limit_overrides table for temporary limit increases
# Reference: PIN-LIM-05

"""
094 — Limit Overrides Table

Creates the limit_overrides table for temporary limit increases.

Contract Rules:
- Overrides are tenant-scoped
- Maximum 5 active overrides per tenant (enforced by service)
- Maximum duration: 168 hours (1 week)
- One override per limit (no stacking)
- All overrides require justification

Lifecycle:
  PENDING → APPROVED → ACTIVE → EXPIRED
         ↘ REJECTED
  PENDING/APPROVED/ACTIVE → CANCELLED

Revision ID: 094_limit_overrides
Revises: 093_llm_run_records_and_system_records
Create Date: 2026-01-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "094_limit_overrides"
down_revision = "093_llm_run_records_system_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # limit_overrides table — Temporary limit increase requests
    # ==========================================================================
    op.create_table(
        "limit_overrides",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(64),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "limit_id",
            sa.String(64),
            sa.ForeignKey("limits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Override values
        sa.Column("original_value", sa.Numeric(20, 4), nullable=False),
        sa.Column("override_value", sa.Numeric(20, 4), nullable=False),
        # Status: PENDING, APPROVED, ACTIVE, EXPIRED, REJECTED, CANCELLED
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        # Lifecycle timestamps
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        # Actors
        sa.Column("requested_by", sa.String(128), nullable=False),
        sa.Column("approved_by", sa.String(128), nullable=True),
        sa.Column("cancelled_by", sa.String(128), nullable=True),
        # Justification (required)
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        # Audit trail
        sa.Column("audit_trail", JSONB, nullable=True),
    )

    # Indexes for common query patterns
    op.create_index(
        "idx_limit_overrides_tenant_status",
        "limit_overrides",
        ["tenant_id", "status"],
    )

    op.create_index(
        "idx_limit_overrides_limit_status",
        "limit_overrides",
        ["limit_id", "status"],
    )

    op.create_index(
        "idx_limit_overrides_expires_at",
        "limit_overrides",
        ["expires_at"],
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )

    # Unique constraint: One active/pending override per limit
    # Prevents stacking
    op.create_index(
        "idx_limit_overrides_no_stacking",
        "limit_overrides",
        ["limit_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'APPROVED', 'ACTIVE')"),
    )


def downgrade() -> None:
    op.drop_index("idx_limit_overrides_no_stacking", table_name="limit_overrides")
    op.drop_index("idx_limit_overrides_expires_at", table_name="limit_overrides")
    op.drop_index("idx_limit_overrides_limit_status", table_name="limit_overrides")
    op.drop_index("idx_limit_overrides_tenant_status", table_name="limit_overrides")
    op.drop_table("limit_overrides")
