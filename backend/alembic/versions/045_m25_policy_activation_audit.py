"""M25 Policy Activation Audit Table

Revision ID: 045_m25_policy_activation_audit
Revises: 044_m25_graduation_hardening
Create Date: 2025-12-23

HYGIENE #3: Every ACTIVE policy must have an audit record for:
- Rollback capability
- Blame tracking
- Trust verification
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "045_m25_policy_audit"
down_revision = "044_m25_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create policy_activation_audit table."""
    op.create_table(
        "policy_activation_audit",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("policy_id", sa.String(64), nullable=False),
        sa.Column("source_pattern_id", sa.String(64), nullable=False),
        sa.Column("source_recovery_id", sa.String(64), nullable=True),
        sa.Column("confidence_at_activation", sa.Float(), nullable=False),
        sa.Column("confidence_version", sa.String(32), nullable=False),
        sa.Column("approval_path", sa.String(128), nullable=False),
        sa.Column("loop_trace_id", sa.String(64), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("policy_id"),
    )

    # Index for querying by tenant and activation time
    op.create_index(
        "ix_policy_activation_audit_tenant_activated",
        "policy_activation_audit",
        ["tenant_id", "activated_at"],
    )

    # Index for querying by pattern (to find all policies from a pattern)
    op.create_index(
        "ix_policy_activation_audit_pattern",
        "policy_activation_audit",
        ["source_pattern_id"],
    )


def downgrade() -> None:
    """Drop policy_activation_audit table."""
    op.drop_index("ix_policy_activation_audit_pattern", "policy_activation_audit")
    op.drop_index("ix_policy_activation_audit_tenant_activated", "policy_activation_audit")
    op.drop_table("policy_activation_audit")
