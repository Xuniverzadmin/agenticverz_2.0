"""Add SDSR columns to policy_rules table

Revision ID: 076_policy_rules_sdsr
Revises: 075_consolidate_incidents_table
Create Date: 2026-01-09

Reference: PIN-372 (SDSR Policy Domain Integration)

Extends policy_rules with SDSR metadata columns following the same pattern
as incidents table (PIN-370). No new tables created - canonical extension only.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '076_policy_rules_sdsr'
down_revision = '075_consolidate_incidents'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add SDSR columns to policy_rules (same pattern as incidents)
    op.add_column('policy_rules', sa.Column('is_synthetic', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('policy_rules', sa.Column('synthetic_scenario_id', sa.String(64), nullable=True))

    # Add index for SDSR queries
    op.create_index('ix_policy_rules_synthetic', 'policy_rules', ['is_synthetic'], postgresql_where=sa.text('is_synthetic = true'))


def downgrade() -> None:
    op.drop_index('ix_policy_rules_synthetic', table_name='policy_rules')
    op.drop_column('policy_rules', 'synthetic_scenario_id')
    op.drop_column('policy_rules', 'is_synthetic')
