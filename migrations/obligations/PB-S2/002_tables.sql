-- PB-S2: Tables
-- Crash recovery state - tracks workflow progress for resumption

CREATE TABLE pb_s2.crash_recovery (
    -- Workflow being tracked
    workflow_id UUID PRIMARY KEY,

    -- Last successfully completed step
    last_success_step TEXT NOT NULL,

    -- Cursor for resumption (step-specific state)
    recovery_cursor JSONB NOT NULL,

    -- Recovery status
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'RECOVERING', 'DONE')),

    -- When the worker claimed this for recovery
    claimed_at TIMESTAMPTZ,
    claimed_by TEXT,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for finding workflows needing recovery
CREATE INDEX idx_crash_recovery_active
ON pb_s2.crash_recovery(status, updated_at)
WHERE status IN ('ACTIVE', 'RECOVERING');

-- Index for finding stale claims
CREATE INDEX idx_crash_recovery_claimed
ON pb_s2.crash_recovery(claimed_at)
WHERE status = 'RECOVERING' AND claimed_at IS NOT NULL;

COMMENT ON TABLE pb_s2.crash_recovery IS
    'Tracks workflow progress for crash recovery. Not retries - resumption.';
COMMENT ON COLUMN pb_s2.crash_recovery.workflow_id IS
    'UUID of the workflow being tracked';
COMMENT ON COLUMN pb_s2.crash_recovery.last_success_step IS
    'Name of the last successfully completed step';
COMMENT ON COLUMN pb_s2.crash_recovery.recovery_cursor IS
    'Step-specific state needed to resume (inputs, partial outputs)';
COMMENT ON COLUMN pb_s2.crash_recovery.status IS
    'ACTIVE=in progress, RECOVERING=being resumed, DONE=completed';
COMMENT ON COLUMN pb_s2.crash_recovery.claimed_at IS
    'When a recovery worker claimed this workflow';
COMMENT ON COLUMN pb_s2.crash_recovery.claimed_by IS
    'ID of the worker that claimed this recovery';
