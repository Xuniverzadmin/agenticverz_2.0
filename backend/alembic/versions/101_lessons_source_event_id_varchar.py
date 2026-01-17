# MIGRATION_CONTRACT:
#   parent: 100_policy_violations_violation_kind
#   description: Change lessons_learned.source_event_id from UUID to VARCHAR
#   authority: neon

"""
Change lessons_learned.source_event_id from UUID to VARCHAR

The source_event_id column needs to store various event ID formats:
- Incident IDs: VARCHAR with prefix (e.g., "inc_cce063bb42b2403a")
- Run IDs: VARCHAR with prefix (e.g., "run-sdsr-12345")

Changing to VARCHAR(255) allows storing any event ID format.

Reference: PIN-411, POLICIES_DOMAIN_AUDIT.md Section 11

Revision ID: 101_lessons_source_event_id_varchar
Revises: 100_policy_violations_violation_kind
Create Date: 2026-01-17
"""

from alembic import op
import sqlalchemy as sa


revision = "101_lessons_source_event_id_varchar"
down_revision = "100_policy_violations_violation_kind"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change source_event_id from UUID to VARCHAR(255)
    # This allows storing various event ID formats
    op.alter_column(
        "lessons_learned",
        "source_event_id",
        existing_type=sa.dialects.postgresql.UUID(),
        type_=sa.String(255),
        existing_nullable=False,
        postgresql_using="source_event_id::text",
    )


def downgrade() -> None:
    # WARNING: This may fail if non-UUID values exist
    op.alter_column(
        "lessons_learned",
        "source_event_id",
        existing_type=sa.String(255),
        type_=sa.dialects.postgresql.UUID(),
        existing_nullable=False,
        postgresql_using="source_event_id::uuid",
    )
