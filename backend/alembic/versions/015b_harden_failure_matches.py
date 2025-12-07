"""Harden failure_matches table - idempotent fixes and tenant enforcement

Revision ID: 015b_harden_failure_matches
Revises: 015_failure_matches
Create Date: 2025-12-07

P0 hardening migration:
- Ensures context_json column exists (handles drift from context rename)
- Prepares tenant_id for future NOT NULL enforcement
- Adds missing indexes for performance
- Fully idempotent - safe to run multiple times
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = '015b_harden_failure_matches'
down_revision = '015_failure_matches'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === IDEMPOTENT COLUMN FIXES ===

    # Fix context vs context_json drift - handle both scenarios
    op.execute("""
        DO $$
        BEGIN
            -- If 'context' exists but 'context_json' doesn't, rename it
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'failure_matches' AND column_name = 'context'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'failure_matches' AND column_name = 'context_json'
            ) THEN
                ALTER TABLE failure_matches RENAME COLUMN context TO context_json;
                RAISE NOTICE 'Renamed context to context_json';
            END IF;

            -- If neither exists, add context_json
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'failure_matches' AND column_name = 'context_json'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'failure_matches' AND column_name = 'context'
            ) THEN
                ALTER TABLE failure_matches ADD COLUMN context_json JSONB DEFAULT '{}';
                RAISE NOTICE 'Added context_json column';
            END IF;
        END $$;
    """)

    # === TENANT ENFORCEMENT PREPARATION ===

    # Add comment indicating tenant_id will become required
    op.execute("""
        COMMENT ON COLUMN failure_matches.tenant_id IS
            'Tenant identifier - WILL become NOT NULL after backfill (M9.1)';
    """)

    # Add index for tenant queries (if not exists)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_fm_tenant_created
        ON failure_matches(tenant_id, created_at DESC)
        WHERE tenant_id IS NOT NULL;
    """)

    # === ADDITIONAL PERFORMANCE INDEXES ===

    # Composite index for recovery dashboard queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_fm_recovery_dashboard
        ON failure_matches(recovery_mode, recovery_attempted, recovery_succeeded)
        WHERE recovery_mode IS NOT NULL;
    """)

    # Index for high-miss-rate alerts (partial index on unmatched only, no time filter)
    # Note: Can't use now() in index predicate as it's not IMMUTABLE
    # Time filtering is done at query time instead
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_fm_recent_misses
        ON failure_matches(created_at DESC)
        WHERE catalog_entry_id IS NULL;
    """)

    # === AUDIT COLUMNS ===

    # Add recovered_at timestamp for recovery tracking
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'failure_matches' AND column_name = 'recovered_at'
            ) THEN
                ALTER TABLE failure_matches ADD COLUMN recovered_at TIMESTAMPTZ;
                RAISE NOTICE 'Added recovered_at column';
            END IF;
        END $$;
    """)

    # Add recovered_by for audit trail
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'failure_matches' AND column_name = 'recovered_by'
            ) THEN
                ALTER TABLE failure_matches ADD COLUMN recovered_by TEXT;
                COMMENT ON COLUMN failure_matches.recovered_by IS 'User/system that marked recovery';
                RAISE NOTICE 'Added recovered_by column';
            END IF;
        END $$;
    """)

    # Add recovery_notes for operator context
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'failure_matches' AND column_name = 'recovery_notes'
            ) THEN
                ALTER TABLE failure_matches ADD COLUMN recovery_notes TEXT;
                RAISE NOTICE 'Added recovery_notes column';
            END IF;
        END $$;
    """)

    # === UPDATE TRIGGER FOR updated_at ===
    op.execute("""
        CREATE OR REPLACE FUNCTION update_failure_matches_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trg_failure_matches_updated_at ON failure_matches;
        CREATE TRIGGER trg_failure_matches_updated_at
            BEFORE UPDATE ON failure_matches
            FOR EACH ROW
            EXECUTE FUNCTION update_failure_matches_updated_at();
    """)

    # === VALIDATION CHECK ===
    op.execute("""
        DO $$
        DECLARE
            col_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO col_count
            FROM information_schema.columns
            WHERE table_name = 'failure_matches';

            IF col_count < 19 THEN
                RAISE WARNING 'failure_matches has fewer columns than expected: %', col_count;
            ELSE
                RAISE NOTICE 'failure_matches validation passed: % columns', col_count;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Remove new columns (safe - they're optional)
    op.execute("""
        ALTER TABLE failure_matches DROP COLUMN IF EXISTS recovered_at;
        ALTER TABLE failure_matches DROP COLUMN IF EXISTS recovered_by;
        ALTER TABLE failure_matches DROP COLUMN IF EXISTS recovery_notes;
    """)

    # Remove new indexes
    op.execute("""
        DROP INDEX IF EXISTS idx_fm_tenant_created;
        DROP INDEX IF EXISTS idx_fm_recovery_dashboard;
        DROP INDEX IF EXISTS idx_fm_recent_misses;
    """)

    # Remove trigger
    op.execute("""
        DROP TRIGGER IF EXISTS trg_failure_matches_updated_at ON failure_matches;
        DROP FUNCTION IF EXISTS update_failure_matches_updated_at();
    """)
