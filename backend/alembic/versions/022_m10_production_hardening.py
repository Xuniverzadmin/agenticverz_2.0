"""022_m10_production_hardening - Leader election, replay log, DL archive, outbox

Revision ID: 022_m10_production_hardening
Revises: 021_m10_durable_queue_fallback
Create Date: 2025-12-09

M10 Production Hardening:
- Adds distributed_locks table for leader election (reconcile, matview refresh)
- Adds replay_log table for durable idempotency (DB-backed replay tracking)
- Adds dead_letter_archive table for DL archival before trimming
- Adds outbox table for transactional external side-effects
- Adds reclaim_attempts_gc table for tracking TTL cleanup
"""
from sqlalchemy import text

from alembic import op

# revision identifiers
revision = "022_m10_production_hardening"
down_revision = "021_m10_durable_queue_fallback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ==========================================================================
    # 1. Create distributed_locks table for leader election
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS m10_recovery.distributed_locks (
            lock_name TEXT PRIMARY KEY,
            holder_id TEXT NOT NULL,
            acquired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ NOT NULL,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        -- Index for cleanup of expired locks
        CREATE INDEX IF NOT EXISTS idx_dl_expires
            ON m10_recovery.distributed_locks(expires_at);

        COMMENT ON TABLE m10_recovery.distributed_locks IS
            'Distributed locks for leader election (reconcile, matview refresh jobs)';
        COMMENT ON COLUMN m10_recovery.distributed_locks.lock_name IS
            'Unique lock identifier (e.g., m10:reconcile, m10:matview:mv_top_pending)';
        COMMENT ON COLUMN m10_recovery.distributed_locks.holder_id IS
            'Identifier of the lock holder (hostname:pid or UUID)';
        COMMENT ON COLUMN m10_recovery.distributed_locks.expires_at IS
            'Lock expiration time - must be refreshed before this';
    """
        )
    )

    # ==========================================================================
    # 2. Create replay_log table for durable idempotency
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS m10_recovery.replay_log (
            id BIGSERIAL PRIMARY KEY,
            original_msg_id TEXT NOT NULL,
            dl_msg_id TEXT,  -- Nullable: may be called for initial replay before DL
            candidate_id INTEGER,
            idempotency_key UUID,
            new_msg_id TEXT,
            replayed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            replayed_by TEXT,
            status TEXT NOT NULL DEFAULT 'replayed',
            error_message TEXT,

            -- Unique constraint ensures idempotency at DB level
            CONSTRAINT uq_replay_original UNIQUE (original_msg_id)
        );

        -- Index for lookups
        CREATE INDEX IF NOT EXISTS idx_replay_dl_msg
            ON m10_recovery.replay_log(dl_msg_id);
        CREATE INDEX IF NOT EXISTS idx_replay_candidate
            ON m10_recovery.replay_log(candidate_id)
            WHERE candidate_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_replay_created
            ON m10_recovery.replay_log(replayed_at DESC);

        COMMENT ON TABLE m10_recovery.replay_log IS
            'Durable log of dead-letter replays for idempotency (survives Redis restarts)';
        COMMENT ON COLUMN m10_recovery.replay_log.original_msg_id IS
            'Original stream message ID that was dead-lettered';
        COMMENT ON COLUMN m10_recovery.replay_log.dl_msg_id IS
            'Dead-letter stream message ID';
        COMMENT ON COLUMN m10_recovery.replay_log.new_msg_id IS
            'New message ID after replay (if successful)';
    """
        )
    )

    # ==========================================================================
    # 3. Create dead_letter_archive table
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS m10_recovery.dead_letter_archive (
            id BIGSERIAL PRIMARY KEY,
            dl_msg_id TEXT,  -- Nullable: may be called for initial replay before DL
            original_msg_id TEXT,
            candidate_id INTEGER,
            failure_match_id UUID,
            payload JSONB NOT NULL,
            reason TEXT,
            reclaim_count INTEGER DEFAULT 0,
            dead_lettered_at TIMESTAMPTZ,
            archived_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            archived_by TEXT DEFAULT 'system',

            -- Unique constraint to prevent duplicate archives
            CONSTRAINT uq_dla_dl_msg UNIQUE (dl_msg_id)
        );

        -- Indexes for analysis
        CREATE INDEX IF NOT EXISTS idx_dla_archived
            ON m10_recovery.dead_letter_archive(archived_at DESC);
        CREATE INDEX IF NOT EXISTS idx_dla_candidate
            ON m10_recovery.dead_letter_archive(candidate_id)
            WHERE candidate_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_dla_failure
            ON m10_recovery.dead_letter_archive(failure_match_id)
            WHERE failure_match_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_dla_reason
            ON m10_recovery.dead_letter_archive(reason);

        COMMENT ON TABLE m10_recovery.dead_letter_archive IS
            'Archive of dead-letter messages before trimming from Redis stream';
        COMMENT ON COLUMN m10_recovery.dead_letter_archive.payload IS
            'Full message payload as JSON for debugging';
    """
        )
    )

    # ==========================================================================
    # 4. Create outbox table for transactional side-effects
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS m10_recovery.outbox (
            id BIGSERIAL PRIMARY KEY,
            aggregate_type TEXT NOT NULL,
            aggregate_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            processed_at TIMESTAMPTZ,
            processed_by TEXT,
            retry_count INTEGER DEFAULT 0,
            last_error TEXT,
            next_retry_at TIMESTAMPTZ
        );

        -- Partial unique index for polling unprocessed events
        CREATE UNIQUE INDEX IF NOT EXISTS uq_outbox_pending
            ON m10_recovery.outbox(aggregate_type, aggregate_id, event_type)
            WHERE processed_at IS NULL;

        -- Index for outbox processor polling
        CREATE INDEX IF NOT EXISTS idx_outbox_pending
            ON m10_recovery.outbox(created_at ASC)
            WHERE processed_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_outbox_retry
            ON m10_recovery.outbox(next_retry_at ASC)
            WHERE processed_at IS NULL AND next_retry_at IS NOT NULL;

        COMMENT ON TABLE m10_recovery.outbox IS
            'Transactional outbox for external side-effects (notifications, HTTP calls)';
        COMMENT ON COLUMN m10_recovery.outbox.aggregate_type IS
            'Type of aggregate (e.g., recovery_candidate, worker_execution)';
        COMMENT ON COLUMN m10_recovery.outbox.event_type IS
            'Event type (e.g., notify_ops, send_email, webhook_call)';
    """
        )
    )

    # ==========================================================================
    # 5. Create function for acquiring distributed lock
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.acquire_lock(
            p_lock_name TEXT,
            p_holder_id TEXT,
            p_ttl_seconds INTEGER DEFAULT 600
        )
        RETURNS BOOLEAN AS $$
        DECLARE
            v_row_count INTEGER := 0;
        BEGIN
            -- Try to insert new lock or update expired lock
            INSERT INTO m10_recovery.distributed_locks (
                lock_name, holder_id, acquired_at, expires_at
            ) VALUES (
                p_lock_name,
                p_holder_id,
                now(),
                now() + (p_ttl_seconds || ' seconds')::INTERVAL
            )
            ON CONFLICT (lock_name) DO UPDATE
            SET holder_id = EXCLUDED.holder_id,
                acquired_at = EXCLUDED.acquired_at,
                expires_at = EXCLUDED.expires_at
            WHERE
                -- Only acquire if expired or same holder
                m10_recovery.distributed_locks.expires_at < now()
                OR m10_recovery.distributed_locks.holder_id = EXCLUDED.holder_id;

            GET DIAGNOSTICS v_row_count = ROW_COUNT;
            RETURN v_row_count > 0;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.acquire_lock IS
            'Acquire distributed lock with TTL. Returns TRUE if acquired.';
    """
        )
    )

    # ==========================================================================
    # 6. Create function for releasing distributed lock
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.release_lock(
            p_lock_name TEXT,
            p_holder_id TEXT
        )
        RETURNS BOOLEAN AS $$
        DECLARE
            v_row_count INTEGER := 0;
        BEGIN
            DELETE FROM m10_recovery.distributed_locks
            WHERE lock_name = p_lock_name
              AND holder_id = p_holder_id;

            GET DIAGNOSTICS v_row_count = ROW_COUNT;
            RETURN v_row_count > 0;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.release_lock IS
            'Release distributed lock. Only holder can release.';
    """
        )
    )

    # ==========================================================================
    # 7. Create function for extending lock TTL
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.extend_lock(
            p_lock_name TEXT,
            p_holder_id TEXT,
            p_ttl_seconds INTEGER DEFAULT 600
        )
        RETURNS BOOLEAN AS $$
        DECLARE
            v_row_count INTEGER := 0;
        BEGIN
            UPDATE m10_recovery.distributed_locks
            SET expires_at = now() + (p_ttl_seconds || ' seconds')::INTERVAL
            WHERE lock_name = p_lock_name
              AND holder_id = p_holder_id;

            GET DIAGNOSTICS v_row_count = ROW_COUNT;
            RETURN v_row_count > 0;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.extend_lock IS
            'Extend lock TTL. Only holder can extend.';
    """
        )
    )

    # ==========================================================================
    # 8. Create function for recording replay (idempotent)
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.record_replay(
            p_original_msg_id TEXT,
            p_dl_msg_id TEXT,
            p_candidate_id INTEGER DEFAULT NULL,
            p_idempotency_key UUID DEFAULT NULL,
            p_new_msg_id TEXT DEFAULT NULL,
            p_replayed_by TEXT DEFAULT 'system'
        )
        RETURNS TABLE(already_replayed BOOLEAN, replay_id BIGINT) AS $$
        DECLARE
            v_id BIGINT;
            v_existing BIGINT;
        BEGIN
            -- Check if already replayed
            SELECT id INTO v_existing
            FROM m10_recovery.replay_log
            WHERE original_msg_id = p_original_msg_id;

            IF v_existing IS NOT NULL THEN
                RETURN QUERY SELECT TRUE, v_existing;
                RETURN;
            END IF;

            -- Insert new replay record
            INSERT INTO m10_recovery.replay_log (
                original_msg_id, dl_msg_id, candidate_id,
                idempotency_key, new_msg_id, replayed_by
            ) VALUES (
                p_original_msg_id, p_dl_msg_id, p_candidate_id,
                p_idempotency_key, p_new_msg_id, p_replayed_by
            )
            ON CONFLICT (original_msg_id) DO NOTHING
            RETURNING id INTO v_id;

            -- If insert succeeded, return new ID
            IF v_id IS NOT NULL THEN
                RETURN QUERY SELECT FALSE, v_id;
            ELSE
                -- Race condition - another process inserted
                SELECT id INTO v_id
                FROM m10_recovery.replay_log
                WHERE original_msg_id = p_original_msg_id;
                RETURN QUERY SELECT TRUE, v_id;
            END IF;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.record_replay IS
            'Record replay with ON CONFLICT for idempotency. Returns (already_replayed, id).';
    """
        )
    )

    # ==========================================================================
    # 9. Create function for archiving DL messages
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.archive_dead_letter(
            p_dl_msg_id TEXT,
            p_original_msg_id TEXT,
            p_candidate_id INTEGER,
            p_failure_match_id UUID,
            p_payload JSONB,
            p_reason TEXT DEFAULT NULL,
            p_reclaim_count INTEGER DEFAULT 0,
            p_dead_lettered_at TIMESTAMPTZ DEFAULT NULL,
            p_archived_by TEXT DEFAULT 'system'
        )
        RETURNS BIGINT AS $$
        DECLARE
            v_id BIGINT;
        BEGIN
            INSERT INTO m10_recovery.dead_letter_archive (
                dl_msg_id, original_msg_id, candidate_id, failure_match_id,
                payload, reason, reclaim_count, dead_lettered_at, archived_by
            ) VALUES (
                p_dl_msg_id, p_original_msg_id, p_candidate_id, p_failure_match_id,
                p_payload, p_reason, p_reclaim_count,
                COALESCE(p_dead_lettered_at, now()), p_archived_by
            )
            ON CONFLICT (dl_msg_id) DO UPDATE
            SET archived_at = now()  -- Update timestamp if re-archived
            RETURNING id INTO v_id;

            RETURN v_id;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.archive_dead_letter IS
            'Archive a dead-letter message before trimming from Redis stream';
    """
        )
    )

    # ==========================================================================
    # 10. Create function for publishing to outbox
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.publish_outbox(
            p_aggregate_type TEXT,
            p_aggregate_id TEXT,
            p_event_type TEXT,
            p_payload JSONB
        )
        RETURNS BIGINT AS $$
        DECLARE
            v_id BIGINT;
        BEGIN
            INSERT INTO m10_recovery.outbox (
                aggregate_type, aggregate_id, event_type, payload
            ) VALUES (
                p_aggregate_type, p_aggregate_id, p_event_type, p_payload
            )
            ON CONFLICT ON CONSTRAINT uq_outbox_pending DO UPDATE
            SET payload = EXCLUDED.payload,
                retry_count = m10_recovery.outbox.retry_count + 1
            RETURNING id INTO v_id;

            RETURN v_id;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.publish_outbox IS
            'Publish event to outbox for external delivery';
    """
        )
    )

    # ==========================================================================
    # 11. Create function to claim outbox events
    # ==========================================================================
    conn.execute(
        text(
            """
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

        COMMENT ON FUNCTION m10_recovery.claim_outbox_events IS
            'Claim batch of outbox events for processing';
    """
        )
    )

    # ==========================================================================
    # 12. Create function to mark outbox event processed/failed
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.complete_outbox_event(
            p_event_id BIGINT,
            p_processor_id TEXT,
            p_success BOOLEAN,
            p_error TEXT DEFAULT NULL,
            p_retry_delay_seconds INTEGER DEFAULT 60
        )
        RETURNS BOOLEAN AS $$
        BEGIN
            IF p_success THEN
                UPDATE m10_recovery.outbox
                SET processed_at = now(),
                    processed_by = p_processor_id
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
    """
        )
    )

    # ==========================================================================
    # 13. Create function to cleanup expired locks
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.cleanup_expired_locks()
        RETURNS INTEGER AS $$
        DECLARE
            v_count INTEGER;
        BEGIN
            WITH deleted AS (
                DELETE FROM m10_recovery.distributed_locks
                WHERE expires_at < now()
                RETURNING lock_name
            )
            SELECT COUNT(*) INTO v_count FROM deleted;

            RETURN v_count;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.cleanup_expired_locks IS
            'Remove expired distributed locks';
    """
        )
    )

    # ==========================================================================
    # 14. Grants
    # ==========================================================================
    conn.execute(
        text(
            """
        DO $$
        DECLARE
            v_role TEXT;
        BEGIN
            FOREACH v_role IN ARRAY ARRAY['nova', 'mobiverz_app', 'neondb_owner']
            LOOP
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = v_role) THEN
                    -- Tables
                    EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON m10_recovery.distributed_locks TO %I', v_role);
                    EXECUTE format('GRANT SELECT, INSERT, UPDATE ON m10_recovery.replay_log TO %I', v_role);
                    EXECUTE format('GRANT SELECT, INSERT ON m10_recovery.dead_letter_archive TO %I', v_role);
                    EXECUTE format('GRANT SELECT, INSERT, UPDATE ON m10_recovery.outbox TO %I', v_role);

                    -- Sequences
                    EXECUTE format('GRANT USAGE ON SEQUENCE m10_recovery.replay_log_id_seq TO %I', v_role);
                    EXECUTE format('GRANT USAGE ON SEQUENCE m10_recovery.dead_letter_archive_id_seq TO %I', v_role);
                    EXECUTE format('GRANT USAGE ON SEQUENCE m10_recovery.outbox_id_seq TO %I', v_role);

                    -- Functions
                    EXECUTE format('GRANT EXECUTE ON FUNCTION m10_recovery.acquire_lock TO %I', v_role);
                    EXECUTE format('GRANT EXECUTE ON FUNCTION m10_recovery.release_lock TO %I', v_role);
                    EXECUTE format('GRANT EXECUTE ON FUNCTION m10_recovery.extend_lock TO %I', v_role);
                    EXECUTE format('GRANT EXECUTE ON FUNCTION m10_recovery.record_replay TO %I', v_role);
                    EXECUTE format('GRANT EXECUTE ON FUNCTION m10_recovery.archive_dead_letter TO %I', v_role);
                    EXECUTE format('GRANT EXECUTE ON FUNCTION m10_recovery.publish_outbox TO %I', v_role);
                    EXECUTE format('GRANT EXECUTE ON FUNCTION m10_recovery.claim_outbox_events TO %I', v_role);
                    EXECUTE format('GRANT EXECUTE ON FUNCTION m10_recovery.complete_outbox_event TO %I', v_role);
                    EXECUTE format('GRANT EXECUTE ON FUNCTION m10_recovery.cleanup_expired_locks TO %I', v_role);

                    RAISE NOTICE 'Granted permissions to % role', v_role;
                END IF;
            END LOOP;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Grant failed (non-fatal): %', SQLERRM;
        END$$;
    """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Drop functions
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.cleanup_expired_locks;"))
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.complete_outbox_event;"))
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.claim_outbox_events;"))
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.publish_outbox;"))
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.archive_dead_letter;"))
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.record_replay;"))
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.extend_lock;"))
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.release_lock;"))
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.acquire_lock;"))

    # Drop tables
    conn.execute(text("DROP TABLE IF EXISTS m10_recovery.outbox;"))
    conn.execute(text("DROP TABLE IF EXISTS m10_recovery.dead_letter_archive;"))
    conn.execute(text("DROP TABLE IF EXISTS m10_recovery.replay_log;"))
    conn.execute(text("DROP TABLE IF EXISTS m10_recovery.distributed_locks;"))
