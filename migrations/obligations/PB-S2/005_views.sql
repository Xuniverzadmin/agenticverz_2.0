-- PB-S2: Views
-- Convenience views for crash recovery operations

-- View: Workflows needing recovery (orphaned)
CREATE OR REPLACE VIEW pb_s2.orphaned_workflows AS
SELECT
    workflow_id,
    last_success_step,
    recovery_cursor,
    status,
    updated_at,
    EXTRACT(EPOCH FROM (now() - updated_at)) / 60 AS minutes_since_update
FROM pb_s2.crash_recovery
WHERE status = 'ACTIVE'
  AND updated_at < now() - INTERVAL '5 minutes'
ORDER BY updated_at ASC;

COMMENT ON VIEW pb_s2.orphaned_workflows IS
    'ACTIVE workflows with no recent updates (likely crashed)';

-- View: Stale recovery claims
CREATE OR REPLACE VIEW pb_s2.stale_claims AS
SELECT
    workflow_id,
    last_success_step,
    claimed_by,
    claimed_at,
    EXTRACT(EPOCH FROM (now() - claimed_at)) / 60 AS minutes_since_claim
FROM pb_s2.crash_recovery
WHERE status = 'RECOVERING'
  AND claimed_at < now() - INTERVAL '10 minutes'
ORDER BY claimed_at ASC;

COMMENT ON VIEW pb_s2.stale_claims IS
    'Recovery claims that may have stalled (claim worker crashed)';

-- View: Recovery statistics
CREATE OR REPLACE VIEW pb_s2.recovery_stats AS
SELECT
    status,
    COUNT(*) AS count,
    MIN(created_at) AS oldest,
    MAX(updated_at) AS most_recent
FROM pb_s2.crash_recovery
GROUP BY status;

COMMENT ON VIEW pb_s2.recovery_stats IS
    'Summary statistics for crash recovery state';
