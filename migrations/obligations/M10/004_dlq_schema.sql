-- M10: Dead Letter Queue Schema (STEP 3)
-- Purpose: Formal DLQ as part of M10 obligation
-- Pattern: Append-only, immutable, part of the contract

-- Create DLQ schema
CREATE SCHEMA IF NOT EXISTS m10_dlq;

COMMENT ON SCHEMA m10_dlq IS 'M10: Dead Letter Queue - Failed messages that exhausted retries';

-- Dead letter archive table (immutable)
CREATE TABLE IF NOT EXISTS m10_dlq.dead_letter (
    id BIGSERIAL PRIMARY KEY,

    -- Reference to original outbox event
    outbox_id BIGINT NOT NULL,

    -- Processing context
    processor_id TEXT NOT NULL,
    error TEXT NOT NULL,
    failure_count INTEGER NOT NULL CHECK (failure_count >= 1),

    -- Original event data (snapshot at time of failure)
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    original_created_at TIMESTAMPTZ NOT NULL,

    -- DLQ metadata
    archived_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Ensure we don't archive the same outbox event twice
    UNIQUE (outbox_id)
);

-- Index for querying by failure type
CREATE INDEX IF NOT EXISTS idx_dlq_error ON m10_dlq.dead_letter(error);
CREATE INDEX IF NOT EXISTS idx_dlq_archived ON m10_dlq.dead_letter(archived_at DESC);
CREATE INDEX IF NOT EXISTS idx_dlq_aggregate ON m10_dlq.dead_letter(aggregate_type, aggregate_id);

COMMENT ON TABLE m10_dlq.dead_letter IS
    'Immutable archive of failed outbox events. Append-only.';
COMMENT ON COLUMN m10_dlq.dead_letter.outbox_id IS
    'Reference to m10_recovery.outbox.id';
COMMENT ON COLUMN m10_dlq.dead_letter.processor_id IS
    'ID of the processor that gave up on this event';
COMMENT ON COLUMN m10_dlq.dead_letter.failure_count IS
    'Number of retry attempts before giving up';

-- Immutability: Dead letters are append-only, never modified
CREATE OR REPLACE FUNCTION m10_dlq.prevent_update()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'm10_dlq.dead_letter is immutable. Cannot modify archived events.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_dlq_immutable ON m10_dlq.dead_letter;

CREATE TRIGGER trg_dlq_immutable
BEFORE UPDATE OR DELETE ON m10_dlq.dead_letter
FOR EACH ROW
EXECUTE FUNCTION m10_dlq.prevent_update();

COMMENT ON TRIGGER trg_dlq_immutable ON m10_dlq.dead_letter IS
    'Dead letter archive is immutable. Append-only.';
