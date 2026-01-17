# MIGRATION_CONTRACT:
#   parent: 099_policy_rules_rule_type
#   description: Add violation_kind column to policy.violations table
#   authority: neon

"""
Add violation_kind column to policy.violations

Adds semantic classification for policy violations:
- STANDARD: Normal violation record
- ANOMALY: Statistically anomalous violation (VIO-O4)
- DIVERGENCE: Simulation vs runtime divergence (VIO-O5)

This enables:
- VIO-O4: Anomaly detection panel via ?violation_kind=ANOMALY
- VIO-O5: Divergence audit panel via ?violation_kind=DIVERGENCE

Reference: PIN-411 Gap Closure, POLICIES_DOMAIN_AUDIT.md

Revision ID: 100_policy_violations_violation_kind
Revises: 099_policy_rules_rule_type
Create Date: 2026-01-17
"""

from alembic import op
import sqlalchemy as sa


revision = "100_policy_violations_violation_kind"
down_revision = "099_policy_rules_rule_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add violation_kind column to policy.violations."""

    # Add the violation_kind column with default 'STANDARD'
    op.add_column(
        "violations",
        sa.Column(
            "violation_kind",
            sa.String(16),
            nullable=False,
            server_default="STANDARD",
        ),
        schema="policy",
    )

    # Add check constraint for valid values
    op.execute(
        """
        ALTER TABLE policy.violations
        ADD CONSTRAINT ck_violations_violation_kind
        CHECK (violation_kind IN ('STANDARD', 'ANOMALY', 'DIVERGENCE'))
        """
    )

    # Create index for efficient filtering
    op.create_index(
        "ix_policy_violations_violation_kind",
        "violations",
        ["violation_kind"],
        schema="policy",
    )


def downgrade() -> None:
    """Remove violation_kind column and constraints."""

    # Drop index first
    op.drop_index(
        "ix_policy_violations_violation_kind",
        table_name="violations",
        schema="policy",
    )

    # Drop check constraint
    op.execute(
        """
        ALTER TABLE policy.violations
        DROP CONSTRAINT IF EXISTS ck_violations_violation_kind
        """
    )

    # Drop column
    op.drop_column("violations", "violation_kind", schema="policy")
