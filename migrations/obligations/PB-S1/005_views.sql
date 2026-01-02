-- PB-S1: Views
-- Convenience views for querying retry state

-- View: Current retry status per entity (latest attempt)
CREATE OR REPLACE VIEW pb_s1.current_retry_status AS
SELECT DISTINCT ON (entity_type, entity_id)
    entity_type,
    entity_id,
    attempt_no AS current_attempt,
    status AS current_status,
    error AS last_error,
    process_after,
    created_at
FROM pb_s1.retry_state
ORDER BY entity_type, entity_id, attempt_no DESC;

COMMENT ON VIEW pb_s1.current_retry_status IS
    'Current retry status per entity (most recent attempt)';

-- View: Pending retries ready for processing
CREATE OR REPLACE VIEW pb_s1.pending_retries AS
SELECT
    id,
    entity_type,
    entity_id,
    attempt_no,
    process_after,
    created_at
FROM pb_s1.retry_state
WHERE status = 'PENDING'
  AND process_after <= now()
ORDER BY process_after ASC;

COMMENT ON VIEW pb_s1.pending_retries IS
    'Retries that are ready for processing (past process_after time)';

-- View: Retry history per entity
CREATE OR REPLACE VIEW pb_s1.retry_history AS
SELECT
    entity_type,
    entity_id,
    attempt_no,
    status,
    error,
    process_after,
    created_at,
    CASE
        WHEN status = 'SUCCESS' THEN 'Completed successfully'
        WHEN status = 'FAILED' THEN 'Terminal failure: ' || COALESCE(error, 'unknown')
        WHEN status = 'PENDING' THEN 'Awaiting retry at ' || process_after::text
    END AS summary
FROM pb_s1.retry_state
ORDER BY entity_type, entity_id, attempt_no ASC;

COMMENT ON VIEW pb_s1.retry_history IS
    'Full retry history per entity with human-readable summary';
