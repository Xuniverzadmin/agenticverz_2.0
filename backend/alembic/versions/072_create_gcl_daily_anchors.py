# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Create GCL Daily Anchors table per PIN-343
# Reference: PIN-343 Section 3.4, PIN-345

"""Create GCL Daily Anchors table for chain anchoring

Revision ID: 072_create_gcl_daily_anchors
Revises: 071_create_signal_feedback
Create Date: 2026-01-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '072_create_gcl_daily_anchors'
down_revision = '071_create_signal_feedback'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create GCL Daily Anchors table per PIN-343 Section 3.4:
    - Externally provable daily root hash
    - Immutable once written
    - One anchor per tenant per day
    """

    # =========================================================================
    # Table: gcl_daily_anchors
    # Purpose: Store daily root hash for external verification
    # Reference: PIN-343 Section 3.4
    # =========================================================================
    op.create_table(
        'gcl_daily_anchors',
        sa.Column('anchor_id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('anchor_date', sa.Date(), nullable=False),
        sa.Column('event_count', sa.Integer(), nullable=False),
        sa.Column('first_event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('first_event_hash', sa.Text(), nullable=True),
        sa.Column('last_event_hash', sa.Text(), nullable=True),
        sa.Column('root_hash', sa.Text(), nullable=False),
        sa.Column('algorithm', sa.Text(), nullable=False),  # ROLLING_SHA256 | MERKLE_SHA256 | EMPTY_DAY_MARKER
        sa.Column('computed_at', sa.TIMESTAMP(), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('exported_to', postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        # Verification metadata
        sa.Column('verification_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_verified_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('last_verified_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Primary key
        sa.PrimaryKeyConstraint('anchor_id'),

        # One anchor per tenant per day
        sa.UniqueConstraint('tenant_id', 'anchor_date',
                            name='uq_gcl_anchors_tenant_date'),

        # Constraints per PIN-343 Section 3.6
        sa.CheckConstraint(
            "algorithm IN ('ROLLING_SHA256', 'MERKLE_SHA256', 'EMPTY_DAY_MARKER')",
            name='ck_gcl_anchors_valid_algorithm'
        ),
        sa.CheckConstraint(
            "event_count >= 0",
            name='ck_gcl_anchors_positive_count'
        ),
    )

    # Indexes
    op.create_index('idx_gcl_anchors_tenant', 'gcl_daily_anchors',
                    ['tenant_id', 'anchor_date'])
    op.create_index('idx_gcl_anchors_date', 'gcl_daily_anchors',
                    ['anchor_date'])
    op.create_index('idx_gcl_anchors_hash', 'gcl_daily_anchors',
                    ['root_hash'])

    # =========================================================================
    # Immutability Enforcement per PIN-343 Section 3.4
    # ABSOLUTE: No UPDATE, No DELETE
    # Only verification_count and last_verified_* may be updated
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION enforce_anchor_immutability()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Allow only verification metadata updates
            IF TG_OP = 'UPDATE' THEN
                IF OLD.root_hash != NEW.root_hash OR
                   OLD.event_count != NEW.event_count OR
                   OLD.first_event_id IS DISTINCT FROM NEW.first_event_id OR
                   OLD.last_event_id IS DISTINCT FROM NEW.last_event_id OR
                   OLD.first_event_hash IS DISTINCT FROM NEW.first_event_hash OR
                   OLD.last_event_hash IS DISTINCT FROM NEW.last_event_hash OR
                   OLD.algorithm != NEW.algorithm OR
                   OLD.anchor_date != NEW.anchor_date OR
                   OLD.tenant_id != NEW.tenant_id THEN
                    RAISE EXCEPTION 'GCL-ANCHOR-IMMUTABLE-001: Anchor core data is immutable. Only verification metadata may be updated. Reference: PIN-343 Section 3.4';
                END IF;
            END IF;

            -- DELETE is always forbidden
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'GCL-ANCHOR-IMMUTABLE-002: Anchors cannot be deleted. Reference: PIN-343 Section 3.4';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER gcl_anchor_immutable
        BEFORE UPDATE OR DELETE ON gcl_daily_anchors
        FOR EACH ROW EXECUTE FUNCTION enforce_anchor_immutability();
    """)

    # =========================================================================
    # Table: gcl_anchor_verifications
    # Purpose: Log all verification attempts for audit
    # Reference: PIN-343 Section 3.7
    # =========================================================================
    op.create_table(
        'gcl_anchor_verifications',
        sa.Column('verification_id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('anchor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('verified_at', sa.TIMESTAMP(), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('result', sa.Text(), nullable=False),  # VALID | CHAIN_BROKEN | ROOT_MISMATCH
        sa.Column('computed_root', sa.Text(), nullable=True),
        sa.Column('expected_root', sa.Text(), nullable=False),
        sa.Column('events_checked', sa.Integer(), nullable=False),
        sa.Column('details', postgresql.JSONB(), nullable=True),

        # Primary key
        sa.PrimaryKeyConstraint('verification_id'),

        # Foreign key
        sa.ForeignKeyConstraint(['anchor_id'], ['gcl_daily_anchors.anchor_id'],
                                name='fk_verification_anchor'),

        # Constraints
        sa.CheckConstraint(
            "result IN ('VALID', 'CHAIN_BROKEN', 'ROOT_MISMATCH')",
            name='ck_verification_valid_result'
        ),
    )

    # Indexes
    op.create_index('idx_anchor_verifications_anchor', 'gcl_anchor_verifications',
                    ['anchor_id', 'verified_at'])
    op.create_index('idx_anchor_verifications_tenant', 'gcl_anchor_verifications',
                    ['tenant_id', 'verified_at'])

    # =========================================================================
    # Trigger: Update anchor verification count on successful verification
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION update_anchor_verification_count()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE gcl_daily_anchors
            SET verification_count = verification_count + 1,
                last_verified_at = NEW.verified_at,
                last_verified_by = NEW.verified_by
            WHERE anchor_id = NEW.anchor_id;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER anchor_verification_count
        AFTER INSERT ON gcl_anchor_verifications
        FOR EACH ROW
        WHEN (NEW.result = 'VALID')
        EXECUTE FUNCTION update_anchor_verification_count();
    """)


def downgrade() -> None:
    """Remove GCL Daily Anchors tables"""

    # Drop trigger and function for verification count
    op.execute("DROP TRIGGER IF EXISTS anchor_verification_count ON gcl_anchor_verifications;")
    op.execute("DROP FUNCTION IF EXISTS update_anchor_verification_count();")

    # Drop indexes
    op.drop_index('idx_anchor_verifications_tenant', 'gcl_anchor_verifications')
    op.drop_index('idx_anchor_verifications_anchor', 'gcl_anchor_verifications')

    # Drop verifications table
    op.drop_table('gcl_anchor_verifications')

    # Drop immutability trigger and function
    op.execute("DROP TRIGGER IF EXISTS gcl_anchor_immutable ON gcl_daily_anchors;")
    op.execute("DROP FUNCTION IF EXISTS enforce_anchor_immutability();")

    # Drop indexes
    op.drop_index('idx_gcl_anchors_hash', 'gcl_daily_anchors')
    op.drop_index('idx_gcl_anchors_date', 'gcl_daily_anchors')
    op.drop_index('idx_gcl_anchors_tenant', 'gcl_daily_anchors')

    # Drop main table
    op.drop_table('gcl_daily_anchors')
