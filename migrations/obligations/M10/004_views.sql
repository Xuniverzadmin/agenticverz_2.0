-- M10: Operational Views
-- Purpose: Visibility into recovery infrastructure state

-- View: Pending outbox events
CREATE OR REPLACE VIEW m10_recovery.pending_outbox AS
SELECT
    id,
    aggregate_type,
    aggregate_id,
    event_type,
    created_at,
    retry_count,
    last_error,
    process_after,
    EXTRACT(EPOCH FROM (now() - created_at)) / 60 AS minutes_waiting
FROM m10_recovery.outbox
WHERE processed_at IS NULL
ORDER BY process_after ASC, created_at ASC;

COMMENT ON VIEW m10_recovery.pending_outbox IS
    'Outbox events waiting to be processed';

-- View: Failed outbox events (retry candidates)
CREATE OR REPLACE VIEW m10_recovery.failed_outbox AS
SELECT
    id,
    aggregate_type,
    aggregate_id,
    event_type,
    created_at,
    retry_count,
    last_error,
    next_retry_at,
    EXTRACT(EPOCH FROM (now() - created_at)) / 3600 AS hours_since_created
FROM m10_recovery.outbox
WHERE processed_at IS NULL
  AND last_error IS NOT NULL
  AND retry_count > 0
ORDER BY retry_count DESC, created_at ASC;

COMMENT ON VIEW m10_recovery.failed_outbox IS
    'Outbox events that have failed and are pending retry';

-- View: Outbox processing stats
CREATE OR REPLACE VIEW m10_recovery.outbox_stats AS
SELECT
    CASE
        WHEN processed_at IS NOT NULL THEN 'PROCESSED'
        WHEN last_error IS NOT NULL THEN 'FAILED'
        ELSE 'PENDING'
    END AS status,
    COUNT(*) AS count,
    MIN(created_at) AS oldest,
    MAX(created_at) AS newest,
    AVG(retry_count) AS avg_retries
FROM m10_recovery.outbox
GROUP BY
    CASE
        WHEN processed_at IS NOT NULL THEN 'PROCESSED'
        WHEN last_error IS NOT NULL THEN 'FAILED'
        ELSE 'PENDING'
    END;

COMMENT ON VIEW m10_recovery.outbox_stats IS
    'Summary statistics for outbox processing';

-- View: Work queue summary (if status column exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'm10_recovery'
        AND table_name = 'work_queue'
        AND column_name = 'status'
    ) THEN
        EXECUTE '
            CREATE OR REPLACE VIEW m10_recovery.work_queue_summary AS
            SELECT
                status,
                COUNT(*) AS count,
                MIN(created_at) AS oldest,
                MAX(created_at) AS newest
            FROM m10_recovery.work_queue
            GROUP BY status
            ORDER BY status;
        ';

        COMMENT ON VIEW m10_recovery.work_queue_summary IS
            'Summary of work queue by status';
    END IF;
END
$$;

-- View: Dead letter summary (legacy archive)
CREATE OR REPLACE VIEW m10_recovery.dead_letter_summary AS
SELECT
    reason AS failure_reason,
    COUNT(*) AS count,
    MIN(archived_at) AS first_archived,
    MAX(archived_at) AS last_archived
FROM m10_recovery.dead_letter_archive
GROUP BY reason
ORDER BY count DESC;

COMMENT ON VIEW m10_recovery.dead_letter_summary IS
    'Summary of dead letter archive by reason';

-- View: M10 DLQ summary (formal dead letter queue)
CREATE OR REPLACE VIEW m10_dlq.dlq_summary AS
SELECT
    error AS failure_type,
    COUNT(*) AS count,
    AVG(failure_count) AS avg_retries,
    MIN(archived_at) AS first_archived,
    MAX(archived_at) AS last_archived
FROM m10_dlq.dead_letter
GROUP BY error
ORDER BY count DESC;

COMMENT ON VIEW m10_dlq.dlq_summary IS
    'Summary of formal DLQ by error type';

-- View: Recent DLQ entries
CREATE OR REPLACE VIEW m10_dlq.recent_dead_letters AS
SELECT
    id,
    outbox_id,
    aggregate_type,
    aggregate_id,
    event_type,
    error,
    failure_count,
    archived_at,
    EXTRACT(EPOCH FROM (now() - archived_at)) / 3600 AS hours_since_archived
FROM m10_dlq.dead_letter
ORDER BY archived_at DESC
LIMIT 100;

COMMENT ON VIEW m10_dlq.recent_dead_letters IS
    'Most recent 100 dead letter entries';

-- View: Stale claims (potential orphaned work)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'm10_recovery'
        AND table_name = 'work_queue'
        AND column_name = 'claimed_at'
    ) THEN
        EXECUTE '
            CREATE OR REPLACE VIEW m10_recovery.stale_claims AS
            SELECT
                id,
                candidate_id,
                claimed_by,
                claimed_at,
                EXTRACT(EPOCH FROM (now() - claimed_at)) / 60 AS minutes_since_claim
            FROM m10_recovery.work_queue
            WHERE claimed_at IS NOT NULL
              AND claimed_at < now() - INTERVAL ''10 minutes''
            ORDER BY claimed_at ASC;
        ';

        COMMENT ON VIEW m10_recovery.stale_claims IS
            'Work queue claims that may be stale (worker crashed)';
    END IF;
END
$$;
