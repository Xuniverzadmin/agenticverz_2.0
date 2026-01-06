"""021_m10_durable_queue_fallback - DB fallback queue, unique indexes, upsert support

Revision ID: 021_m10_durable_queue_fallback
Revises: 020_m10_concurrent_indexes
Create Date: 2025-12-09

M10 Durability Enhancements:
- Adds work_queue table for Redis fallback (write-ahead guarantee)
- Adds unique index on (failure_match_id, error_signature) for upsert
- Adds matview_refresh_log for freshness monitoring
- Safe, additive migration - does not alter existing constraints
"""

from sqlalchemy import text

from alembic import op

# revision identifiers
revision = "021_m10_durable_queue_fallback"
down_revision = "020_m10_concurrent_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ==========================================================================
    # 1. Create m10_recovery.work_queue for Redis fallback
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS m10_recovery.work_queue (
            id SERIAL PRIMARY KEY,
            candidate_id INTEGER NOT NULL,
            idempotency_key UUID,
            method TEXT NOT NULL DEFAULT 'db_fallback',
            priority INTEGER DEFAULT 0,
            queued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            claimed_at TIMESTAMPTZ,
            claimed_by TEXT,
            processed_at TIMESTAMPTZ,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        -- Partial unique index to prevent duplicate pending work (same candidate)
        CREATE UNIQUE INDEX IF NOT EXISTS uq_work_queue_candidate_pending
            ON m10_recovery.work_queue(candidate_id)
            WHERE processed_at IS NULL;

        -- Index for worker polling (unclaimed items)
        CREATE INDEX IF NOT EXISTS idx_wq_pending_priority
            ON m10_recovery.work_queue(priority DESC, queued_at ASC)
            WHERE processed_at IS NULL AND claimed_at IS NULL;

        -- Index for claimed but not processed (stalled detection)
        CREATE INDEX IF NOT EXISTS idx_wq_claimed_stalled
            ON m10_recovery.work_queue(claimed_at)
            WHERE processed_at IS NULL AND claimed_at IS NOT NULL;

        COMMENT ON TABLE m10_recovery.work_queue IS
            'Fallback queue when Redis unavailable. Worker polls this if stream is empty.';
        COMMENT ON COLUMN m10_recovery.work_queue.method IS
            'Enqueue method: redis_stream, db_fallback, retry';
    """
        )
    )

    # ==========================================================================
    # 2. Add unique index for upsert on recovery_candidates
    # ==========================================================================
    # Note: failure_match_id is already UNIQUE in 017, but we add error_signature
    # composite for cases where same failure has different signatures
    conn.execute(
        text(
            """
        -- Unique index for upsert: (failure_match_id, error_signature)
        -- Allows ON CONFLICT to work correctly
        CREATE UNIQUE INDEX IF NOT EXISTS uq_rc_fmid_sig
            ON public.recovery_candidates(failure_match_id, error_signature)
            WHERE error_signature IS NOT NULL;

        COMMENT ON INDEX public.uq_rc_fmid_sig IS
            'Unique composite for upsert deduplication by failure + signature';
    """
        )
    )

    # ==========================================================================
    # 3. Create matview_refresh_log for freshness monitoring
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS m10_recovery.matview_refresh_log (
            id SERIAL PRIMARY KEY,
            view_name TEXT NOT NULL,
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,
            duration_ms INTEGER,
            rows_affected INTEGER,
            success BOOLEAN DEFAULT FALSE,
            error_message TEXT
        );

        -- Partial unique index: only one refresh can be running per view
        CREATE UNIQUE INDEX IF NOT EXISTS uq_refresh_log_running
            ON m10_recovery.matview_refresh_log(view_name)
            WHERE completed_at IS NULL;

        -- Index for freshness queries
        CREATE INDEX IF NOT EXISTS idx_mrl_view_completed
            ON m10_recovery.matview_refresh_log(view_name, completed_at DESC);

        COMMENT ON TABLE m10_recovery.matview_refresh_log IS
            'Tracks materialized view refresh operations for freshness monitoring';
    """
        )
    )

    # ==========================================================================
    # 4. Create function for tracked matview refresh
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.refresh_mv_tracked(
            p_view_name TEXT DEFAULT 'mv_top_pending'
        )
        RETURNS TABLE(success BOOLEAN, duration_ms INTEGER, error TEXT) AS $$
        DECLARE
            v_log_id INTEGER;
            v_start TIMESTAMPTZ;
            v_duration INTEGER;
            v_error TEXT;
        BEGIN
            v_start := clock_timestamp();

            -- Insert start record
            INSERT INTO m10_recovery.matview_refresh_log (view_name, started_at)
            VALUES (p_view_name, v_start)
            RETURNING id INTO v_log_id;

            BEGIN
                -- Perform refresh
                IF p_view_name = 'mv_top_pending' THEN
                    REFRESH MATERIALIZED VIEW CONCURRENTLY m10_recovery.mv_top_pending;
                END IF;

                v_duration := EXTRACT(EPOCH FROM (clock_timestamp() - v_start)) * 1000;

                -- Update success
                UPDATE m10_recovery.matview_refresh_log
                SET completed_at = clock_timestamp(),
                    duration_ms = v_duration,
                    success = TRUE
                WHERE id = v_log_id;

                RETURN QUERY SELECT TRUE, v_duration, NULL::TEXT;

            EXCEPTION WHEN OTHERS THEN
                v_error := SQLERRM;
                v_duration := EXTRACT(EPOCH FROM (clock_timestamp() - v_start)) * 1000;

                UPDATE m10_recovery.matview_refresh_log
                SET completed_at = clock_timestamp(),
                    duration_ms = v_duration,
                    success = FALSE,
                    error_message = v_error
                WHERE id = v_log_id;

                RETURN QUERY SELECT FALSE, v_duration, v_error;
            END;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.refresh_mv_tracked IS
            'Refresh matview with logging for freshness monitoring';
    """
        )
    )

    # ==========================================================================
    # 5. Create view for matview freshness status
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE VIEW m10_recovery.matview_freshness AS
        SELECT
            view_name,
            MAX(completed_at) AS last_refresh,
            EXTRACT(EPOCH FROM (now() - MAX(completed_at))) AS age_seconds,
            (SELECT success FROM m10_recovery.matview_refresh_log mrl2
             WHERE mrl2.view_name = mrl.view_name
             ORDER BY completed_at DESC LIMIT 1) AS last_success,
            (SELECT duration_ms FROM m10_recovery.matview_refresh_log mrl3
             WHERE mrl3.view_name = mrl.view_name
             ORDER BY completed_at DESC LIMIT 1) AS last_duration_ms
        FROM m10_recovery.matview_refresh_log mrl
        WHERE completed_at IS NOT NULL
        GROUP BY view_name;

        COMMENT ON VIEW m10_recovery.matview_freshness IS
            'Current freshness status of tracked materialized views';
    """
        )
    )

    # ==========================================================================
    # 6. Create function for DB queue enqueue (fallback)
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.enqueue_work(
            p_candidate_id INTEGER,
            p_idempotency_key UUID DEFAULT NULL,
            p_priority INTEGER DEFAULT 0,
            p_method TEXT DEFAULT 'db_fallback'
        )
        RETURNS INTEGER AS $$
        DECLARE
            v_id INTEGER;
        BEGIN
            INSERT INTO m10_recovery.work_queue (
                candidate_id, idempotency_key, priority, method
            ) VALUES (
                p_candidate_id, p_idempotency_key, p_priority, p_method
            )
            ON CONFLICT ON CONSTRAINT uq_work_queue_candidate_pending
            DO UPDATE SET
                priority = GREATEST(m10_recovery.work_queue.priority, EXCLUDED.priority),
                retry_count = m10_recovery.work_queue.retry_count + 1
            RETURNING id INTO v_id;

            RETURN v_id;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.enqueue_work IS
            'Enqueue work item with upsert semantics for Redis fallback';
    """
        )
    )

    # ==========================================================================
    # 7. Create function for worker claim (FOR UPDATE SKIP LOCKED)
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.claim_work(
            p_worker_id TEXT,
            p_batch_size INTEGER DEFAULT 10
        )
        RETURNS TABLE(
            work_id INTEGER,
            candidate_id INTEGER,
            idempotency_key UUID,
            priority INTEGER,
            retry_count INTEGER
        ) AS $$
        BEGIN
            RETURN QUERY
            WITH claimed AS (
                SELECT w.id
                FROM m10_recovery.work_queue w
                WHERE w.processed_at IS NULL
                  AND w.claimed_at IS NULL
                ORDER BY w.priority DESC, w.queued_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT p_batch_size
            )
            UPDATE m10_recovery.work_queue wq
            SET claimed_at = now(),
                claimed_by = p_worker_id
            FROM claimed
            WHERE wq.id = claimed.id
            RETURNING wq.id, wq.candidate_id, wq.idempotency_key, wq.priority, wq.retry_count;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.claim_work IS
            'Claim work items with FOR UPDATE SKIP LOCKED for safe concurrency';
    """
        )
    )

    # ==========================================================================
    # 8. Create function to mark work complete
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.complete_work(
            p_work_id INTEGER,
            p_success BOOLEAN DEFAULT TRUE,
            p_error TEXT DEFAULT NULL
        )
        RETURNS BOOLEAN AS $$
        BEGIN
            IF p_success THEN
                UPDATE m10_recovery.work_queue
                SET processed_at = now()
                WHERE id = p_work_id;
            ELSE
                UPDATE m10_recovery.work_queue
                SET claimed_at = NULL,
                    claimed_by = NULL,
                    error_message = p_error,
                    retry_count = retry_count + 1
                WHERE id = p_work_id;
            END IF;

            RETURN FOUND;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.complete_work IS
            'Mark work item as completed or release for retry';
    """
        )
    )

    # ==========================================================================
    # 9. Create function to release stalled work
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.release_stalled_work(
            p_stalled_seconds INTEGER DEFAULT 300
        )
        RETURNS INTEGER AS $$
        DECLARE
            v_count INTEGER;
        BEGIN
            WITH stalled AS (
                UPDATE m10_recovery.work_queue
                SET claimed_at = NULL,
                    claimed_by = NULL,
                    error_message = 'Released: worker stalled'
                WHERE processed_at IS NULL
                  AND claimed_at IS NOT NULL
                  AND claimed_at < now() - (p_stalled_seconds || ' seconds')::INTERVAL
                RETURNING id
            )
            SELECT COUNT(*) INTO v_count FROM stalled;

            RETURN v_count;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.release_stalled_work IS
            'Release work items claimed by stalled workers';
    """
        )
    )

    # ==========================================================================
    # 10. Grants (safe - handles missing roles)
    # ==========================================================================
    conn.execute(
        text(
            """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nova') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON m10_recovery.work_queue TO nova;
                GRANT SELECT, INSERT ON m10_recovery.matview_refresh_log TO nova;
                GRANT SELECT ON m10_recovery.matview_freshness TO nova;
                GRANT EXECUTE ON FUNCTION m10_recovery.enqueue_work TO nova;
                GRANT EXECUTE ON FUNCTION m10_recovery.claim_work TO nova;
                GRANT EXECUTE ON FUNCTION m10_recovery.complete_work TO nova;
                GRANT EXECUTE ON FUNCTION m10_recovery.release_stalled_work TO nova;
                GRANT EXECUTE ON FUNCTION m10_recovery.refresh_mv_tracked TO nova;
                GRANT USAGE ON SEQUENCE m10_recovery.work_queue_id_seq TO nova;
                GRANT USAGE ON SEQUENCE m10_recovery.matview_refresh_log_id_seq TO nova;
                RAISE NOTICE 'Granted permissions to nova role';
            END IF;

            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mobiverz_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON m10_recovery.work_queue TO mobiverz_app;
                GRANT SELECT, INSERT ON m10_recovery.matview_refresh_log TO mobiverz_app;
                GRANT SELECT ON m10_recovery.matview_freshness TO mobiverz_app;
                GRANT EXECUTE ON FUNCTION m10_recovery.enqueue_work TO mobiverz_app;
                GRANT EXECUTE ON FUNCTION m10_recovery.claim_work TO mobiverz_app;
                GRANT EXECUTE ON FUNCTION m10_recovery.complete_work TO mobiverz_app;
                GRANT EXECUTE ON FUNCTION m10_recovery.release_stalled_work TO mobiverz_app;
                GRANT EXECUTE ON FUNCTION m10_recovery.refresh_mv_tracked TO mobiverz_app;
                GRANT USAGE ON SEQUENCE m10_recovery.work_queue_id_seq TO mobiverz_app;
                GRANT USAGE ON SEQUENCE m10_recovery.matview_refresh_log_id_seq TO mobiverz_app;
                RAISE NOTICE 'Granted permissions to mobiverz_app role';
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Grant failed (non-fatal): %', SQLERRM;
        END$$;
    """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Drop functions
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.release_stalled_work;"))
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.complete_work;"))
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.claim_work;"))
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.enqueue_work;"))
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.refresh_mv_tracked;"))

    # Drop view
    conn.execute(text("DROP VIEW IF EXISTS m10_recovery.matview_freshness;"))

    # Drop tables
    conn.execute(text("DROP TABLE IF EXISTS m10_recovery.matview_refresh_log;"))
    conn.execute(text("DROP TABLE IF EXISTS m10_recovery.work_queue;"))

    # Drop index
    conn.execute(text("DROP INDEX IF EXISTS public.uq_rc_fmid_sig;"))
