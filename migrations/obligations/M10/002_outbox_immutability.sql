-- M10: Outbox Immutability (STEP 1)
-- Purpose: Freeze outbox events after completion
-- Pattern: Same as PB-S1 - immutable after terminal state

-- Function: Prevent mutation of completed outbox events
CREATE OR REPLACE FUNCTION m10_recovery.prevent_outbox_mutation()
RETURNS trigger AS $$
BEGIN
    -- Once processed, the row is immutable
    IF OLD.processed_at IS NOT NULL THEN
        RAISE EXCEPTION 'm10_recovery.outbox: Event is immutable once processed. processed_at = %', OLD.processed_at;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Block updates/deletes on processed events
DROP TRIGGER IF EXISTS trg_outbox_immutable_after_done ON m10_recovery.outbox;

CREATE TRIGGER trg_outbox_immutable_after_done
BEFORE UPDATE OR DELETE ON m10_recovery.outbox
FOR EACH ROW
EXECUTE FUNCTION m10_recovery.prevent_outbox_mutation();

COMMENT ON TRIGGER trg_outbox_immutable_after_done ON m10_recovery.outbox IS
    'Outbox events are immutable once processed_at is set (PB-S1 aligned)';
