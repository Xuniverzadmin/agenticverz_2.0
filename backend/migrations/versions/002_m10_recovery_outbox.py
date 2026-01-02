# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: M10 Recovery & Outbox Infrastructure
# Callers: alembic
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-276 M10 State B

"""Create M10 Recovery & Outbox Infrastructure

Phase A1: M10 Infrastructure Canonicalization

This migration creates the complete M10 infrastructure:
- m10_recovery schema
- Distributed locks (leader election)
- Transactional outbox (exactly-once delivery)
- Replay log (idempotency)
- Dead letter archive
- Work queue (DB fallback)
- Recovery candidates
- Materialized view tracking
- Retention configuration

Revision ID: 002_m10_recovery_outbox
Revises: 001_contracts_decision_records
Create Date: 2026-01-02

INVARIANT: If code assumes it, schema must enforce it.
"""

from alembic import op

# revision identifiers
revision = "002_m10_recovery_outbox"
down_revision = "001_contracts_decision_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create M10 recovery & outbox infrastructure."""

    # =========================================================================
    # SCHEMA CREATION
    # =========================================================================
    op.execute("CREATE SCHEMA IF NOT EXISTS m10_recovery")

    # =========================================================================
    # 1. DISTRIBUTED LOCKS (Leader Election)
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS m10_recovery.distributed_locks (
            lock_name VARCHAR(255) PRIMARY KEY,
            holder_id VARCHAR(255) NOT NULL,
            acquired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ NOT NULL
        )
        """
    )

    # Lock management functions
    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.acquire_lock(
            p_lock_name VARCHAR,
            p_holder_id VARCHAR,
            p_ttl_seconds INT DEFAULT 30
        ) RETURNS BOOLEAN AS $$
        DECLARE
            v_acquired BOOLEAN := FALSE;
        BEGIN
            -- Try to insert new lock
            INSERT INTO m10_recovery.distributed_locks (lock_name, holder_id, expires_at)
            VALUES (p_lock_name, p_holder_id, now() + (p_ttl_seconds || ' seconds')::INTERVAL)
            ON CONFLICT (lock_name) DO UPDATE
                SET holder_id = EXCLUDED.holder_id,
                    acquired_at = now(),
                    expires_at = EXCLUDED.expires_at
                WHERE m10_recovery.distributed_locks.expires_at < now()
                   OR m10_recovery.distributed_locks.holder_id = p_holder_id;

            -- Check if we got the lock
            SELECT holder_id = p_holder_id INTO v_acquired
            FROM m10_recovery.distributed_locks
            WHERE lock_name = p_lock_name;

            RETURN COALESCE(v_acquired, FALSE);
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.release_lock(
            p_lock_name VARCHAR,
            p_holder_id VARCHAR
        ) RETURNS BOOLEAN AS $$
        DECLARE
            v_released BOOLEAN;
        BEGIN
            DELETE FROM m10_recovery.distributed_locks
            WHERE lock_name = p_lock_name AND holder_id = p_holder_id;

            GET DIAGNOSTICS v_released = ROW_COUNT;
            RETURN v_released > 0;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.extend_lock(
            p_lock_name VARCHAR,
            p_holder_id VARCHAR,
            p_ttl_seconds INT DEFAULT 30
        ) RETURNS BOOLEAN AS $$
        DECLARE
            v_extended BOOLEAN;
        BEGIN
            UPDATE m10_recovery.distributed_locks
            SET expires_at = now() + (p_ttl_seconds || ' seconds')::INTERVAL
            WHERE lock_name = p_lock_name AND holder_id = p_holder_id;

            GET DIAGNOSTICS v_extended = ROW_COUNT;
            RETURN v_extended > 0;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.cleanup_expired_locks()
        RETURNS INT AS $$
        DECLARE
            v_count INT;
        BEGIN
            DELETE FROM m10_recovery.distributed_locks
            WHERE expires_at < now();

            GET DIAGNOSTICS v_count = ROW_COUNT;
            RETURN v_count;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # =========================================================================
    # 2. TRANSACTIONAL OUTBOX (Exactly-Once Delivery)
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS m10_recovery.outbox (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            aggregate_type VARCHAR(255) NOT NULL,
            aggregate_id UUID,
            event_type VARCHAR(255) NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            processed_at TIMESTAMPTZ,
            retry_count INT NOT NULL DEFAULT 0,
            process_after TIMESTAMPTZ,
            claimed_at TIMESTAMPTZ,
            claimed_by VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # Outbox indexes for efficient queries
    op.execute("CREATE INDEX IF NOT EXISTS idx_outbox_aggregate ON m10_recovery.outbox(aggregate_type, aggregate_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_outbox_processed ON m10_recovery.outbox(processed_at) WHERE processed_at IS NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_outbox_process_after ON m10_recovery.outbox(process_after) WHERE process_after IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_outbox_claimed ON m10_recovery.outbox(claimed_at) WHERE claimed_at IS NOT NULL"
    )

    # Outbox functions
    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.publish_outbox(
            p_aggregate_type VARCHAR,
            p_aggregate_id UUID,
            p_event_type VARCHAR,
            p_payload JSONB
        ) RETURNS UUID AS $$
        DECLARE
            v_id UUID;
        BEGIN
            INSERT INTO m10_recovery.outbox (aggregate_type, aggregate_id, event_type, payload)
            VALUES (p_aggregate_type, p_aggregate_id, p_event_type, p_payload)
            RETURNING id INTO v_id;

            RETURN v_id;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

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

    # =========================================================================
    # 3. REPLAY LOG (Idempotency)
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS m10_recovery.replay_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            original_msg_id VARCHAR(255) NOT NULL UNIQUE,
            dl_msg_id VARCHAR(255),
            new_msg_id VARCHAR(255),
            failure_match_id UUID,
            reason VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS idx_replay_log_original ON m10_recovery.replay_log(original_msg_id)")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.record_replay(
            p_original_msg_id VARCHAR,
            p_dl_msg_id VARCHAR DEFAULT NULL,
            p_failure_match_id UUID DEFAULT NULL,
            p_new_msg_id VARCHAR DEFAULT NULL,
            p_reason VARCHAR DEFAULT NULL
        ) RETURNS TABLE (already_replayed BOOLEAN, replay_id UUID) AS $$
        DECLARE
            v_existing_id UUID;
            v_new_id UUID;
        BEGIN
            -- Check if already replayed
            SELECT id INTO v_existing_id
            FROM m10_recovery.replay_log
            WHERE original_msg_id = p_original_msg_id;

            IF v_existing_id IS NOT NULL THEN
                RETURN QUERY SELECT TRUE, v_existing_id;
                RETURN;
            END IF;

            -- Insert new replay record
            INSERT INTO m10_recovery.replay_log (original_msg_id, dl_msg_id, failure_match_id, new_msg_id, reason)
            VALUES (p_original_msg_id, p_dl_msg_id, p_failure_match_id, p_new_msg_id, p_reason)
            ON CONFLICT (original_msg_id) DO NOTHING
            RETURNING id INTO v_new_id;

            IF v_new_id IS NOT NULL THEN
                RETURN QUERY SELECT FALSE, v_new_id;
            ELSE
                -- Race condition: someone else inserted, get their ID
                SELECT id INTO v_existing_id
                FROM m10_recovery.replay_log
                WHERE original_msg_id = p_original_msg_id;

                RETURN QUERY SELECT TRUE, v_existing_id;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # =========================================================================
    # 4. DEAD LETTER ARCHIVE
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS m10_recovery.dead_letter_archive (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            dl_msg_id VARCHAR(255) NOT NULL UNIQUE,
            original_msg_id VARCHAR(255),
            candidate_id INT,
            failure_match_id UUID,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            reason VARCHAR(255) NOT NULL,
            reclaim_count INT NOT NULL DEFAULT 0,
            archived_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            archived_by VARCHAR(255)
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS idx_dead_letter_dl_msg ON m10_recovery.dead_letter_archive(dl_msg_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_dead_letter_reason ON m10_recovery.dead_letter_archive(reason)")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.archive_dead_letter(
            p_dl_msg_id VARCHAR,
            p_original_msg_id VARCHAR DEFAULT NULL,
            p_candidate_id INT DEFAULT NULL,
            p_failure_match_id UUID DEFAULT NULL,
            p_payload JSONB DEFAULT '{}'::jsonb,
            p_reason VARCHAR DEFAULT 'unknown',
            p_reclaim_count INT DEFAULT 0,
            p_archived_by VARCHAR DEFAULT NULL
        ) RETURNS UUID AS $$
        DECLARE
            v_id UUID;
        BEGIN
            INSERT INTO m10_recovery.dead_letter_archive (
                dl_msg_id, original_msg_id, candidate_id, failure_match_id,
                payload, reason, reclaim_count, archived_by
            )
            VALUES (
                p_dl_msg_id, p_original_msg_id, p_candidate_id, p_failure_match_id,
                p_payload, p_reason, p_reclaim_count, p_archived_by
            )
            ON CONFLICT (dl_msg_id) DO NOTHING
            RETURNING id INTO v_id;

            IF v_id IS NULL THEN
                SELECT id INTO v_id
                FROM m10_recovery.dead_letter_archive
                WHERE dl_msg_id = p_dl_msg_id;
            END IF;

            RETURN v_id;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # =========================================================================
    # 5. WORK QUEUE (DB Fallback)
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS m10_recovery.work_queue (
            id SERIAL PRIMARY KEY,
            candidate_id INT NOT NULL,
            method VARCHAR(64) NOT NULL DEFAULT 'db_fallback',
            priority FLOAT NOT NULL DEFAULT 1.0,
            claimed_at TIMESTAMPTZ,
            claimed_by VARCHAR(255),
            processed_at TIMESTAMPTZ,
            error_msg TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # Partial unique index for upsert support
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_work_queue_candidate_pending
        ON m10_recovery.work_queue(candidate_id)
        WHERE processed_at IS NULL
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_work_queue_candidate ON m10_recovery.work_queue(candidate_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_work_queue_processed ON m10_recovery.work_queue(processed_at) WHERE processed_at IS NULL"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_work_queue_claimed ON m10_recovery.work_queue(claimed_at)")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.enqueue_work(
            p_candidate_id INT,
            p_priority FLOAT DEFAULT 1.0,
            p_method VARCHAR DEFAULT 'db_fallback'
        ) RETURNS INT AS $$
        DECLARE
            v_id INT;
        BEGIN
            INSERT INTO m10_recovery.work_queue (candidate_id, priority, method)
            VALUES (p_candidate_id, p_priority, p_method)
            ON CONFLICT (candidate_id) WHERE processed_at IS NULL DO NOTHING
            RETURNING id INTO v_id;

            IF v_id IS NULL THEN
                SELECT id INTO v_id
                FROM m10_recovery.work_queue
                WHERE candidate_id = p_candidate_id AND processed_at IS NULL;
            END IF;

            RETURN v_id;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.claim_work(
            p_worker_name VARCHAR,
            p_batch_size INT DEFAULT 10
        ) RETURNS TABLE (
            id INT,
            candidate_id INT,
            priority FLOAT,
            method VARCHAR
        ) AS $$
        BEGIN
            RETURN QUERY
            WITH claimed AS (
                SELECT w.id
                FROM m10_recovery.work_queue w
                WHERE w.processed_at IS NULL
                  AND (w.claimed_at IS NULL OR w.claimed_at < now() - INTERVAL '5 minutes')
                ORDER BY w.priority DESC, w.created_at
                LIMIT p_batch_size
                FOR UPDATE SKIP LOCKED
            )
            UPDATE m10_recovery.work_queue w
            SET claimed_at = now(),
                claimed_by = p_worker_name
            FROM claimed c
            WHERE w.id = c.id
            RETURNING w.id, w.candidate_id, w.priority, w.method;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.complete_work(
            p_work_id INT,
            p_success BOOLEAN,
            p_error_msg VARCHAR DEFAULT NULL
        ) RETURNS VOID AS $$
        BEGIN
            IF p_success THEN
                UPDATE m10_recovery.work_queue
                SET processed_at = now()
                WHERE id = p_work_id;
            ELSE
                UPDATE m10_recovery.work_queue
                SET claimed_at = NULL,
                    claimed_by = NULL,
                    error_msg = p_error_msg
                WHERE id = p_work_id;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.release_stalled_work(
            p_stalled_threshold_seconds INT DEFAULT 300
        ) RETURNS INT AS $$
        DECLARE
            v_count INT;
        BEGIN
            UPDATE m10_recovery.work_queue
            SET claimed_at = NULL,
                claimed_by = NULL
            WHERE processed_at IS NULL
              AND claimed_at < now() - (p_stalled_threshold_seconds || ' seconds')::INTERVAL;

            GET DIAGNOSTICS v_count = ROW_COUNT;
            RETURN v_count;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # =========================================================================
    # 6. RECOVERY CANDIDATES (Public Schema)
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS recovery_candidates (
            id SERIAL PRIMARY KEY,
            failure_match_id UUID NOT NULL UNIQUE,
            suggestion VARCHAR(1024),
            confidence FLOAT NOT NULL DEFAULT 0.0,
            explain JSONB DEFAULT '{}'::jsonb,
            error_code VARCHAR(128),
            error_signature VARCHAR(128),
            source VARCHAR(64),
            created_by VARCHAR(64),
            occurrence_count INT NOT NULL DEFAULT 1,
            last_occurrence_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            execution_status VARCHAR(32) NOT NULL DEFAULT 'pending',
            decision VARCHAR(32) NOT NULL DEFAULT 'pending',
            idempotency_key UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS idx_recovery_candidates_error_code ON recovery_candidates(error_code)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_recovery_candidates_error_sig ON recovery_candidates(error_signature)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_recovery_candidates_status ON recovery_candidates(execution_status)")

    # =========================================================================
    # 7. MATERIALIZED VIEW TRACKING
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS m10_recovery.matview_refresh_log (
            id SERIAL PRIMARY KEY,
            view_name VARCHAR(255) NOT NULL,
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,
            success BOOLEAN,
            duration_ms INT,
            error TEXT
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS idx_matview_log_view ON m10_recovery.matview_refresh_log(view_name)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_matview_log_started ON m10_recovery.matview_refresh_log(started_at)")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.refresh_mv_tracked(
            p_view_name VARCHAR
        ) RETURNS TABLE (success BOOLEAN, duration_ms INT, error TEXT) AS $$
        DECLARE
            v_start TIMESTAMPTZ;
            v_duration INT;
            v_error TEXT;
            v_success BOOLEAN := TRUE;
            v_log_id INT;
        BEGIN
            v_start := clock_timestamp();

            -- Insert start record
            INSERT INTO m10_recovery.matview_refresh_log (view_name, started_at)
            VALUES (p_view_name, v_start)
            RETURNING id INTO v_log_id;

            BEGIN
                EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY %I', p_view_name);
            EXCEPTION WHEN OTHERS THEN
                v_success := FALSE;
                v_error := SQLERRM;
            END;

            v_duration := EXTRACT(MILLISECOND FROM (clock_timestamp() - v_start))::INT;

            -- Update log record
            UPDATE m10_recovery.matview_refresh_log
            SET completed_at = clock_timestamp(),
                success = v_success,
                duration_ms = v_duration,
                error = v_error
            WHERE id = v_log_id;

            RETURN QUERY SELECT v_success, v_duration, v_error;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Freshness view
    op.execute(
        """
        CREATE OR REPLACE VIEW m10_recovery.matview_freshness AS
        SELECT DISTINCT ON (view_name)
            view_name,
            EXTRACT(EPOCH FROM (now() - started_at))::INT AS age_seconds,
            success AS last_success,
            started_at AS last_refresh_at
        FROM m10_recovery.matview_refresh_log
        ORDER BY view_name, started_at DESC
        """
    )

    # =========================================================================
    # 8. RETENTION CONFIGURATION
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS m10_recovery.retention_jobs (
            id SERIAL PRIMARY KEY,
            name VARCHAR(128) NOT NULL UNIQUE,
            retention_days INT NOT NULL DEFAULT 30,
            last_run_at TIMESTAMPTZ,
            enabled BOOLEAN NOT NULL DEFAULT TRUE
        )
        """
    )

    # Seed default retention policies
    op.execute(
        """
        INSERT INTO m10_recovery.retention_jobs (name, retention_days)
        VALUES
            ('provenance_archive', 90),
            ('replay_log', 30),
            ('outbox', 7),
            ('dead_letter_archive', 90),
            ('matview_refresh_log', 14)
        ON CONFLICT (name) DO NOTHING
        """
    )


def downgrade() -> None:
    """Remove M10 recovery & outbox infrastructure."""

    # Drop in reverse order of dependencies
    op.execute("DROP TABLE IF EXISTS m10_recovery.retention_jobs CASCADE")
    op.execute("DROP VIEW IF EXISTS m10_recovery.matview_freshness CASCADE")
    op.execute("DROP TABLE IF EXISTS m10_recovery.matview_refresh_log CASCADE")
    op.execute("DROP TABLE IF EXISTS recovery_candidates CASCADE")
    op.execute("DROP TABLE IF EXISTS m10_recovery.work_queue CASCADE")
    op.execute("DROP TABLE IF EXISTS m10_recovery.dead_letter_archive CASCADE")
    op.execute("DROP TABLE IF EXISTS m10_recovery.replay_log CASCADE")
    op.execute("DROP TABLE IF EXISTS m10_recovery.outbox CASCADE")
    op.execute("DROP TABLE IF EXISTS m10_recovery.distributed_locks CASCADE")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.refresh_mv_tracked(VARCHAR) CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.release_stalled_work(INT) CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.complete_work(INT, BOOLEAN, VARCHAR) CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.claim_work(VARCHAR, INT) CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.enqueue_work(INT, FLOAT, VARCHAR) CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.archive_dead_letter CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.record_replay CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.complete_outbox_event CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.claim_outbox_events CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.publish_outbox CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.cleanup_expired_locks() CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.extend_lock CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.release_lock CASCADE")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.acquire_lock CASCADE")

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS m10_recovery CASCADE")
