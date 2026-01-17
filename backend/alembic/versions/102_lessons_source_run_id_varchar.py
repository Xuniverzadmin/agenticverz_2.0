# MIGRATION_CONTRACT:
#   parent: 101_lessons_source_event_id_varchar
#   description: Change lessons_learned.source_run_id from UUID to VARCHAR
#   authority: neon

"""
Change lessons_learned.source_run_id from UUID to VARCHAR

The source_run_id column needs to store various run ID formats:
- Run IDs: VARCHAR with prefix (e.g., "run-sdsr-e2e-004-case-b-...")

Changing to VARCHAR(255) allows storing any run ID format.

Reference: PIN-411, POLICIES_DOMAIN_AUDIT.md Section 11

Revision ID: 102_lessons_source_run_id_varchar
Revises: 101_lessons_source_event_id_varchar
Create Date: 2026-01-17
"""

from alembic import op
import sqlalchemy as sa


revision = "102_lessons_source_run_id_varchar"
down_revision = "101_lessons_source_event_id_varchar"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change source_run_id from UUID to VARCHAR(255)
    # This allows storing various run ID formats
    op.alter_column(
        "lessons_learned",
        "source_run_id",
        existing_type=sa.dialects.postgresql.UUID(),
        type_=sa.String(255),
        existing_nullable=True,
        postgresql_using="source_run_id::text",
    )


def downgrade() -> None:
    # WARNING: This may fail if non-UUID values exist
    op.alter_column(
        "lessons_learned",
        "source_run_id",
        existing_type=sa.String(255),
        type_=sa.dialects.postgresql.UUID(),
        existing_nullable=True,
        postgresql_using="source_run_id::uuid",
    )
