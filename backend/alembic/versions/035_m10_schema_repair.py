"""M10 Schema Repair - Fix Neon parent branch drift

Revision ID: 035_m10_schema_repair
Revises: 034_fix_outbox_constraint
Create Date: 2025-12-15

This migration repairs schema drift discovered in the Neon parent branch:

1. claim_outbox_events function signature mismatch:
   - Some environments have (integer, unknown) signature
   - Code expects (text, integer) from migration 022
   - Tests call it with (integer, text) positionally

   Fix: Drop and recreate with correct signature + add overload for positional calls

2. dead_letter_archive missing columns:
   - Tests expect: stream_msg_id, stream_name
   - Migration 022 has: dl_msg_id (no stream_name)

   Fix: Add missing columns with IF NOT EXISTS

This migration is fully idempotent and safe to run on any state.
"""
from alembic import op
from sqlalchemy import text


revision = '035_m10_schema_repair'
down_revision = '034_fix_outbox_constraint'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # ==========================================================================
    # STEP 1: Ensure m10_recovery schema exists
    # ==========================================================================
    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS m10_recovery;
    """))

    # ==========================================================================
    # STEP 2: Add missing columns to dead_letter_archive
    # ==========================================================================
    conn.execute(text("""
        DO $$
        BEGIN
            -- Add stream_msg_id column if missing
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'm10_recovery'
                AND table_name = 'dead_letter_archive'
                AND column_name = 'stream_msg_id'
            ) THEN
                ALTER TABLE m10_recovery.dead_letter_archive
                ADD COLUMN stream_msg_id TEXT;

                -- Backfill from dl_msg_id if it exists
                UPDATE m10_recovery.dead_letter_archive
                SET stream_msg_id = dl_msg_id
                WHERE stream_msg_id IS NULL AND dl_msg_id IS NOT NULL;

                RAISE NOTICE 'Added stream_msg_id column to dead_letter_archive';
            END IF;

            -- Add stream_name column if missing
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'm10_recovery'
                AND table_name = 'dead_letter_archive'
                AND column_name = 'stream_name'
            ) THEN
                ALTER TABLE m10_recovery.dead_letter_archive
                ADD COLUMN stream_name TEXT;

                RAISE NOTICE 'Added stream_name column to dead_letter_archive';
            END IF;
        END $$;
    """))

    # Create index on stream_msg_id if it doesn't exist
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_dla_stream_msg_id
        ON m10_recovery.dead_letter_archive(stream_msg_id)
        WHERE stream_msg_id IS NOT NULL;
    """))

    # ==========================================================================
    # STEP 3: Drop and recreate claim_outbox_events with correct signature
    # ==========================================================================
    # Drop all overloads first
    conn.execute(text("""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            -- Find and drop all versions of claim_outbox_events
            FOR r IN (
                SELECT pg_get_functiondef(p.oid) as funcdef,
                       pg_catalog.pg_get_function_identity_arguments(p.oid) as args
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'm10_recovery'
                AND p.proname = 'claim_outbox_events'
            ) LOOP
                EXECUTE format('DROP FUNCTION IF EXISTS m10_recovery.claim_outbox_events(%s)', r.args);
                RAISE NOTICE 'Dropped claim_outbox_events(%)', r.args;
            END LOOP;
        END $$;
    """))

    # Create the canonical version (matches migration 022 and worker code)
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION m10_recovery.claim_outbox_events(
            p_processor_id TEXT,
            p_batch_size INTEGER DEFAULT 10
        )
        RETURNS TABLE(
            event_id BIGINT,
            aggregate_type TEXT,
            aggregate_id TEXT,
            event_type TEXT,
            payload JSONB,
            retry_count INTEGER
        ) AS $$
        BEGIN
            RETURN QUERY
            WITH claimed AS (
                SELECT o.id
                FROM m10_recovery.outbox o
                WHERE o.processed_at IS NULL
                  AND (o.next_retry_at IS NULL OR o.next_retry_at <= now())
                ORDER BY o.created_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT p_batch_size
            )
            SELECT o.id, o.aggregate_type, o.aggregate_id, o.event_type, o.payload, o.retry_count
            FROM m10_recovery.outbox o
            INNER JOIN claimed c ON o.id = c.id;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.claim_outbox_events(TEXT, INTEGER) IS
            'Claim batch of outbox events for processing (canonical signature)';
    """))

    # Create overload for tests that call with (integer, text) positionally
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION m10_recovery.claim_outbox_events(
            p_batch_size INTEGER,
            p_processor_id TEXT
        )
        RETURNS TABLE(
            event_id BIGINT,
            aggregate_type TEXT,
            aggregate_id TEXT,
            event_type TEXT,
            payload JSONB,
            retry_count INTEGER
        ) AS $$
        BEGIN
            -- Delegate to canonical signature
            RETURN QUERY
            SELECT * FROM m10_recovery.claim_outbox_events(p_processor_id, p_batch_size);
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.claim_outbox_events(INTEGER, TEXT) IS
            'Claim batch of outbox events - overload for positional (batch, processor) calls';
    """))

    # ==========================================================================
    # STEP 4: Drop and recreate complete_outbox_event with correct signature
    # ==========================================================================
    # Drop all overloads first (same pattern as claim_outbox_events)
    conn.execute(text("""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            -- Find and drop all versions of complete_outbox_event
            FOR r IN (
                SELECT pg_catalog.pg_get_function_identity_arguments(p.oid) as args
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'm10_recovery'
                AND p.proname = 'complete_outbox_event'
            ) LOOP
                EXECUTE format('DROP FUNCTION IF EXISTS m10_recovery.complete_outbox_event(%s)', r.args);
                RAISE NOTICE 'Dropped complete_outbox_event(%)', r.args;
            END LOOP;
        END $$;
    """))

    conn.execute(text("""
        CREATE OR REPLACE FUNCTION m10_recovery.complete_outbox_event(
            p_event_id BIGINT,
            p_success BOOLEAN,
            p_error TEXT DEFAULT NULL,
            p_processor_id TEXT DEFAULT NULL,
            p_retry_delay_seconds INTEGER DEFAULT 60
        )
        RETURNS BOOLEAN AS $$
        BEGIN
            IF p_success THEN
                UPDATE m10_recovery.outbox
                SET processed_at = now(),
                    processed_by = COALESCE(p_processor_id, 'unknown')
                WHERE id = p_event_id;
            ELSE
                UPDATE m10_recovery.outbox
                SET last_error = p_error,
                    retry_count = retry_count + 1,
                    next_retry_at = now() + (p_retry_delay_seconds || ' seconds')::INTERVAL
                WHERE id = p_event_id;
            END IF;

            RETURN FOUND;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.complete_outbox_event IS
            'Mark outbox event as processed or schedule retry';
    """))

    # ==========================================================================
    # STEP 5: Add process_after column if missing (for retry scheduling)
    # ==========================================================================
    conn.execute(text("""
        DO $$
        BEGIN
            -- Add process_after column to outbox if missing
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'm10_recovery'
                AND table_name = 'outbox'
                AND column_name = 'process_after'
            ) THEN
                ALTER TABLE m10_recovery.outbox
                ADD COLUMN process_after TIMESTAMPTZ DEFAULT now();

                RAISE NOTICE 'Added process_after column to outbox';
            END IF;
        END $$;
    """))

    # ==========================================================================
    # STEP 6: Verify schema state (post-migration validation)
    # ==========================================================================
    conn.execute(text("""
        DO $$
        DECLARE
            v_count INTEGER;
        BEGIN
            -- Verify claim_outbox_events exists with both signatures
            SELECT COUNT(*) INTO v_count
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'm10_recovery'
            AND p.proname = 'claim_outbox_events';

            IF v_count < 2 THEN
                RAISE WARNING 'Expected 2 claim_outbox_events overloads, found %', v_count;
            ELSE
                RAISE NOTICE 'Schema repair complete: % function overloads created', v_count;
            END IF;

            -- Verify dead_letter_archive has stream_msg_id
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'm10_recovery'
                AND table_name = 'dead_letter_archive'
                AND column_name = 'stream_msg_id'
            ) THEN
                RAISE NOTICE 'dead_letter_archive.stream_msg_id column verified';
            ELSE
                RAISE WARNING 'dead_letter_archive.stream_msg_id column missing!';
            END IF;
        END $$;
    """))


def downgrade():
    conn = op.get_bind()

    # Remove the integer,text overload (keep the canonical text,integer version)
    conn.execute(text("""
        DROP FUNCTION IF EXISTS m10_recovery.claim_outbox_events(INTEGER, TEXT);
    """))

    # Note: We don't remove stream_msg_id or stream_name columns on downgrade
    # as they may contain data and are backward compatible
