# MIGRATION_CONTRACT:
#   parent: 096_incidents_domain_model
#   description: Lessons learned table for policy domain intelligence
#   authority: neon

"""
Lessons Learned Table

Creates the lessons_learned table to store learning signals from:
- HIGH/CRITICAL failures (existing)
- MEDIUM/LOW failures (new)
- Near-threshold events (new)
- Critical success events (new)

This table is the memory substrate for the LessonsLearnedEngine (L4).
Lessons can be converted to draft policy proposals via human action.

Reference: POLICIES_DOMAIN_AUDIT.md Section 11, PIN-411

Revision ID: 097_lessons_learned_table
Revises: 096_incidents_domain_model
Create Date: 2026-01-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "097_lessons_learned_table"
down_revision = "096_incidents_domain_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create lesson_type enum
    lesson_type_enum = postgresql.ENUM(
        'failure',
        'near_threshold',
        'critical_success',
        name='lesson_type_enum',
        create_type=False
    )
    lesson_type_enum.create(op.get_bind(), checkfirst=True)

    # Create lesson_status enum
    lesson_status_enum = postgresql.ENUM(
        'pending',
        'converted_to_draft',
        'deferred',
        'dismissed',
        name='lesson_status_enum',
        create_type=False
    )
    lesson_status_enum.create(op.get_bind(), checkfirst=True)

    # Create lessons_learned table
    op.create_table(
        'lessons_learned',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),

        # Lesson classification
        sa.Column('lesson_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=True),  # HIGH, MEDIUM, LOW, or NULL for success

        # Source event linkage
        sa.Column('source_event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_event_type', sa.String(50), nullable=False),  # 'run', 'incident'
        sa.Column('source_run_id', postgresql.UUID(as_uuid=True), nullable=True),  # Direct link to run

        # Lesson content
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('proposed_action', sa.Text, nullable=True),
        sa.Column('detected_pattern', postgresql.JSONB, nullable=True),  # Pattern metadata

        # Status tracking
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('draft_proposal_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deferred_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dismissed_by', sa.String(255), nullable=True),
        sa.Column('dismissed_reason', sa.Text, nullable=True),

        # SDSR synthetic tracking
        sa.Column('is_synthetic', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('synthetic_scenario_id', sa.String(255), nullable=True),

        # CHECK constraints for enum discipline (do not rely on code alone)
        sa.CheckConstraint(
            "lesson_type IN ('failure', 'near_threshold', 'critical_success')",
            name='ck_lessons_learned_lesson_type'
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'converted_to_draft', 'deferred', 'dismissed')",
            name='ck_lessons_learned_status'
        ),
        sa.CheckConstraint(
            "severity IS NULL OR severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'NONE')",
            name='ck_lessons_learned_severity'
        ),
        # Tenant isolation: prevent duplicate lessons per event
        sa.UniqueConstraint(
            'tenant_id', 'source_event_id', 'lesson_type',
            name='uq_lessons_learned_tenant_event_type'
        ),
    )

    # Create indexes for common queries
    op.create_index(
        'ix_lessons_learned_tenant_status',
        'lessons_learned',
        ['tenant_id', 'status']
    )
    op.create_index(
        'ix_lessons_learned_lesson_type',
        'lessons_learned',
        ['lesson_type']
    )
    op.create_index(
        'ix_lessons_learned_source_event',
        'lessons_learned',
        ['source_event_id', 'source_event_type']
    )
    op.create_index(
        'ix_lessons_learned_created_at',
        'lessons_learned',
        ['created_at']
    )
    op.create_index(
        'ix_lessons_learned_draft_proposal_id',
        'lessons_learned',
        ['draft_proposal_id'],
        postgresql_where=sa.text('draft_proposal_id IS NOT NULL')
    )

    # Add foreign key to policy_proposals if table exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'policy_proposals') THEN
                ALTER TABLE lessons_learned
                ADD CONSTRAINT fk_lessons_learned_draft_proposal
                FOREIGN KEY (draft_proposal_id) REFERENCES policy_proposals(id)
                ON DELETE SET NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.drop_table('lessons_learned')

    # Drop enums if they exist and are not used elsewhere
    op.execute("DROP TYPE IF EXISTS lesson_type_enum")
    op.execute("DROP TYPE IF EXISTS lesson_status_enum")
