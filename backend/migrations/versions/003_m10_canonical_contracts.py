# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Canonicalize M10 function contracts (ONE signature per function)
# Callers: alembic
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-276 REDO #1, REDO #2

"""Canonicalize M10 Function Contracts

REDO #1: ONE function signature per operation - drop all overloads
REDO #2: ONE retry authority field - use process_after only

This migration enforces contract authority:
- Production code signatures are canonical
- Tests must conform to production, not vice versa
- No function overloading to satisfy different callers

Canonical Signatures (from app/worker/outbox_processor.py):
- claim_outbox_events(processor_id TEXT, batch_size INTEGER)
- complete_outbox_event(event_id, processor_id, success, error)

Single Retry Field:
- process_after is the authority for retry scheduling
- next_retry_at is dropped from all update logic

Revision ID: 003_m10_canonical_contracts
Revises: 002_m10_recovery_outbox
Create Date: 2026-01-02
"""

from alembic import op

revision = "003_m10_canonical_contracts"
down_revision = "002_m10_recovery_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Canonicalize M10 function contracts."""

    # =========================================================================
    # STEP 1: Drop ALL existing claim_outbox_events overloads
    # =========================================================================
    op.execute(
        """
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (
                SELECT pg_catalog.pg_get_function_identity_arguments(p.oid) as args
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'm10_recovery'
                AND p.proname = 'claim_outbox_events'
            ) LOOP
                EXECUTE format('DROP FUNCTION IF EXISTS m10_recovery.claim_outbox_events(%s) CASCADE', r.args);
                RAISE NOTICE 'Dropped claim_outbox_events(%)', r.args;
            END LOOP;
        END $$;
        """
    )

    # =========================================================================
    # STEP 2: Create CANONICAL claim_outbox_events (production signature)
    # Signature: (processor_id TEXT, batch_size INTEGER)
    # Source: app/worker/outbox_processor.py line 187
    # Return types match actual outbox table schema (BIGINT id, TEXT strings)
    # =========================================================================
    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.claim_outbox_events(
            p_processor_id TEXT,
            p_batch_size INTEGER DEFAULT 10
        )
        RETURNS TABLE(
            id BIGINT,
            aggregate_type TEXT,
            aggregate_id TEXT,
            event_type TEXT,
            payload JSONB,
            retry_count INT
        ) AS $$
        BEGIN
            RETURN QUERY
            WITH claimed AS (
                SELECT o.id
                FROM m10_recovery.outbox o
                WHERE o.processed_at IS NULL
                  AND (o.process_after IS NULL OR o.process_after <= now())
                  AND (o.claimed_at IS NULL OR o.claimed_at < now() - INTERVAL '5 minutes')
                ORDER BY o.created_at
                LIMIT p_batch_size
                FOR UPDATE SKIP LOCKED
            )
            UPDATE m10_recovery.outbox o
            SET claimed_at = now(),
                claimed_by = p_processor_id,
                updated_at = now()
            FROM claimed c
            WHERE o.id = c.id
            RETURNING o.id, o.aggregate_type, o.aggregate_id, o.event_type, o.payload, o.retry_count;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.claim_outbox_events(TEXT, INTEGER) IS
            'CANONICAL: Claim batch of outbox events (processor_id, batch_size). Production signature.';
        """
    )

    # =========================================================================
    # STEP 3: Drop ALL existing complete_outbox_event overloads
    # =========================================================================
    op.execute(
        """
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (
                SELECT pg_catalog.pg_get_function_identity_arguments(p.oid) as args
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'm10_recovery'
                AND p.proname = 'complete_outbox_event'
            ) LOOP
                EXECUTE format('DROP FUNCTION IF EXISTS m10_recovery.complete_outbox_event(%s) CASCADE', r.args);
                RAISE NOTICE 'Dropped complete_outbox_event(%)', r.args;
            END LOOP;
        END $$;
        """
    )

    # =========================================================================
    # STEP 4: Create CANONICAL complete_outbox_event (production signature)
    # Signature: (event_id, processor_id, success, error)
    # Source: app/worker/outbox_processor.py line 356
    # REDO #2: Uses process_after ONLY (no next_retry_at)
    # Event ID type matches actual outbox table schema (BIGINT)
    # =========================================================================
    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.complete_outbox_event(
            p_event_id BIGINT,
            p_processor_id TEXT,
            p_success BOOLEAN,
            p_error TEXT DEFAULT NULL
        ) RETURNS VOID AS $$
        BEGIN
            IF p_success THEN
                UPDATE m10_recovery.outbox
                SET processed_at = now(),
                    updated_at = now()
                WHERE id = p_event_id;
            ELSE
                -- REDO #2: Single retry authority field (process_after)
                -- Exponential backoff: 2^retry_count seconds, capped at 10 retries
                UPDATE m10_recovery.outbox
                SET retry_count = retry_count + 1,
                    process_after = now() + (POWER(2, LEAST(retry_count, 10)) || ' seconds')::INTERVAL,
                    claimed_at = NULL,
                    claimed_by = NULL,
                    updated_at = now()
                WHERE id = p_event_id;
            END IF;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.complete_outbox_event(UUID, TEXT, BOOLEAN, TEXT) IS
            'CANONICAL: Complete outbox event (event_id, processor_id, success, error). Production signature. Uses process_after only.';
        """
    )

    # =========================================================================
    # STEP 5: Verify no overloads exist
    # =========================================================================
    op.execute(
        """
        DO $$
        DECLARE
            v_claim_count INTEGER;
            v_complete_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO v_claim_count
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'm10_recovery'
            AND p.proname = 'claim_outbox_events';

            SELECT COUNT(*) INTO v_complete_count
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'm10_recovery'
            AND p.proname = 'complete_outbox_event';

            IF v_claim_count != 1 THEN
                RAISE EXCEPTION 'CONTRACT VIOLATION: claim_outbox_events has % signatures, expected 1', v_claim_count;
            END IF;

            IF v_complete_count != 1 THEN
                RAISE EXCEPTION 'CONTRACT VIOLATION: complete_outbox_event has % signatures, expected 1', v_complete_count;
            END IF;

            RAISE NOTICE 'CONTRACT VERIFIED: claim_outbox_events=%, complete_outbox_event=%', v_claim_count, v_complete_count;
        END $$;
        """
    )


def downgrade() -> None:
    """Restore original signatures from 002_m10_recovery_outbox."""

    # Drop canonical functions (correct types)
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.claim_outbox_events(TEXT, INTEGER) CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.complete_outbox_event(BIGINT, TEXT, BOOLEAN, TEXT) CASCADE")

    # Restore original from 002 (batch_size, processor_name order)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.claim_outbox_events(
            p_batch_size INT,
            p_processor_name VARCHAR
        ) RETURNS TABLE (
            id UUID,
            aggregate_type VARCHAR,
            aggregate_id UUID,
            event_type VARCHAR,
            payload JSONB,
            retry_count INT
        ) AS $$
        BEGIN
            RETURN QUERY
            WITH claimed AS (
                SELECT o.id
                FROM m10_recovery.outbox o
                WHERE o.processed_at IS NULL
                  AND (o.process_after IS NULL OR o.process_after <= now())
                  AND (o.claimed_at IS NULL OR o.claimed_at < now() - INTERVAL '5 minutes')
                ORDER BY o.created_at
                LIMIT p_batch_size
                FOR UPDATE SKIP LOCKED
            )
            UPDATE m10_recovery.outbox o
            SET claimed_at = now(),
                claimed_by = p_processor_name,
                updated_at = now()
            FROM claimed c
            WHERE o.id = c.id
            RETURNING o.id, o.aggregate_type, o.aggregate_id, o.event_type, o.payload, o.retry_count;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.complete_outbox_event(
            p_event_id UUID,
            p_success BOOLEAN,
            p_error_msg VARCHAR DEFAULT NULL,
            p_processor_name VARCHAR DEFAULT NULL
        ) RETURNS VOID AS $$
        BEGIN
            IF p_success THEN
                UPDATE m10_recovery.outbox
                SET processed_at = now(),
                    updated_at = now()
                WHERE id = p_event_id;
            ELSE
                UPDATE m10_recovery.outbox
                SET retry_count = retry_count + 1,
                    process_after = now() + (POWER(2, LEAST(retry_count, 10)) || ' seconds')::INTERVAL,
                    claimed_at = NULL,
                    claimed_by = NULL,
                    updated_at = now()
                WHERE id = p_event_id;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
