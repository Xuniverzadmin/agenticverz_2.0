# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Add SDSR scenario traceability to prevention_records
# Reference: PIN-373 (SDSR Policy Domain Integration)

"""Add synthetic_scenario_id to prevention_records

Revision ID: 077_prevention_records_sdsr
Revises: 076_policy_rules_sdsr
Create Date: 2026-01-09

prevention_records is the canonical Policy Evaluation Output (PEO).
All policy evaluations—synthetic or real—MUST be written here.

This migration adds scenario traceability for SDSR cleanup and replay.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '077_prevention_records_sdsr'
down_revision = '076_policy_rules_sdsr'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add synthetic_scenario_id for SDSR traceability
    op.add_column('prevention_records', sa.Column('synthetic_scenario_id', sa.String(64), nullable=True))

    # Index for SDSR queries and cleanup
    op.create_index(
        'ix_prevention_records_scenario',
        'prevention_records',
        ['synthetic_scenario_id'],
        postgresql_where=sa.text('synthetic_scenario_id IS NOT NULL')
    )


def downgrade() -> None:
    op.drop_index('ix_prevention_records_scenario', table_name='prevention_records')
    op.drop_column('prevention_records', 'synthetic_scenario_id')
