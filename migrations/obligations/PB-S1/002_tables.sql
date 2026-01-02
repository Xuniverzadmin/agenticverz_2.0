-- PB-S1: Tables
-- Retry state table - append-only, immutable history

CREATE TABLE pb_s1.retry_state (
    id BIGSERIAL PRIMARY KEY,

    -- What entity is being retried
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,

    -- Attempt tracking
    attempt_no INTEGER NOT NULL CHECK (attempt_no >= 1),

    -- Status (terminal states are immutable)
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'SUCCESS', 'FAILED')),

    -- Error details (only for FAILED)
    error TEXT,

    -- When to process this attempt
    process_after TIMESTAMPTZ NOT NULL,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Each entity can only have one attempt per number
    UNIQUE(entity_type, entity_id, attempt_no)
);

-- Index for pending retries lookup
CREATE INDEX idx_retry_state_pending
ON pb_s1.retry_state(process_after)
WHERE status = 'PENDING';

-- Index for entity history lookup
CREATE INDEX idx_retry_state_entity
ON pb_s1.retry_state(entity_type, entity_id, attempt_no);

COMMENT ON TABLE pb_s1.retry_state IS 'Immutable retry attempt history. Append-only.';
COMMENT ON COLUMN pb_s1.retry_state.entity_type IS 'Type of entity being retried (run, workflow, task)';
COMMENT ON COLUMN pb_s1.retry_state.entity_id IS 'ID of the entity being retried';
COMMENT ON COLUMN pb_s1.retry_state.attempt_no IS 'Attempt number (1-based, monotonically increasing)';
COMMENT ON COLUMN pb_s1.retry_state.status IS 'PENDING=scheduled, SUCCESS=completed, FAILED=terminal failure';
COMMENT ON COLUMN pb_s1.retry_state.process_after IS 'When this retry should be processed (for backoff)';
