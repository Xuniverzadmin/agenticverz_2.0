# MIGRATION_CONTRACT:
#   parent: 098_policy_versions_is_current
#   description: Add rule_type column to policy_rules table
#   authority: neon

"""
Add rule_type column to policy_rules

Adds semantic classification for policy rules:
- SYSTEM: System-generated operational rules
- SAFETY: Safety constraint rules
- ETHICAL: Ethical guideline rules
- TEMPORAL: Time-bound rules (expiry, scheduling)

This enables:
- LIB-O2: Ethical guidelines panel via ?rule_type=ETHICAL
- LIB-O5: Temporal rules panel via ?rule_type=TEMPORAL

Reference: PIN-411 Gap Closure, POLICIES_DOMAIN_AUDIT.md

Revision ID: 099_policy_rules_rule_type
Revises: 098_policy_versions_is_current
Create Date: 2026-01-17
"""

from alembic import op
import sqlalchemy as sa


revision = "099_policy_rules_rule_type"
down_revision = "098_policy_versions_is_current"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add rule_type column to policy_rules."""

    # Add the rule_type column with default 'SYSTEM'
    op.add_column(
        "policy_rules",
        sa.Column(
            "rule_type",
            sa.String(16),
            nullable=False,
            server_default="SYSTEM",
        ),
    )

    # Add check constraint for valid values
    op.create_check_constraint(
        "ck_policy_rules_rule_type",
        "policy_rules",
        "rule_type IN ('SYSTEM', 'SAFETY', 'ETHICAL', 'TEMPORAL')",
    )

    # Create index for efficient filtering
    op.create_index(
        "ix_policy_rules_rule_type",
        "policy_rules",
        ["rule_type"],
    )


def downgrade() -> None:
    """Remove rule_type column and constraints."""

    # Drop index first
    op.drop_index("ix_policy_rules_rule_type", table_name="policy_rules")

    # Drop check constraint
    op.drop_constraint("ck_policy_rules_rule_type", "policy_rules", type_="check")

    # Drop column
    op.drop_column("policy_rules", "rule_type")
