# MIGRATION_CONTRACT:
#   parent: 097_lessons_learned_table
#   description: Add is_current flag to policy_versions table
#   authority: neon

"""
Add is_current flag to policy_versions

Adds the is_current boolean column to policy_versions table to track
which version is the currently active version for each policy.

This enables:
- DFT-O3: Quick lookup of current policy rules
- ACT-O4: Policy state snapshot includes current versions
- Policy evolution tracking via version history

Constraint: Only one version per proposal can have is_current=true.
This is enforced via a partial unique index.

Reference: PIN-411 Gap Closure

Revision ID: 098_policy_versions_is_current
Revises: 097_lessons_learned_table
Create Date: 2026-01-17
"""

from alembic import op
import sqlalchemy as sa


revision = "098_policy_versions_is_current"
down_revision = "097_lessons_learned_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add is_current column and index to policy_versions."""

    # Add the is_current column with default false
    op.add_column(
        "policy_versions",
        sa.Column(
            "is_current",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # Create index for quick lookup of current versions
    op.create_index(
        "ix_policy_versions_is_current",
        "policy_versions",
        ["is_current"],
        postgresql_where=sa.text("is_current = true"),
    )

    # Create partial unique index to ensure only one current version per proposal
    # This enforces the constraint at database level
    op.create_index(
        "ix_policy_versions_proposal_id_is_current_unique",
        "policy_versions",
        ["proposal_id"],
        unique=True,
        postgresql_where=sa.text("is_current = true"),
    )


def downgrade() -> None:
    """Remove is_current column and indexes."""

    # Drop the indexes first
    op.drop_index(
        "ix_policy_versions_proposal_id_is_current_unique",
        table_name="policy_versions",
    )
    op.drop_index(
        "ix_policy_versions_is_current",
        table_name="policy_versions",
    )

    # Drop the column
    op.drop_column("policy_versions", "is_current")
