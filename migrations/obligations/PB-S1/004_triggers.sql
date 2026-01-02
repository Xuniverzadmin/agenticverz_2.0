-- PB-S1: Immutability Triggers
-- CRITICAL: These triggers enforce the truth-grade guarantee
-- Retry history is APPEND-ONLY. No updates. No deletes.

-- Function to prevent any update
CREATE OR REPLACE FUNCTION pb_s1.prevent_retry_update()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'pb_s1.retry_state is immutable - UPDATE not allowed. Create new attempt instead.';
END;
$$ LANGUAGE plpgsql;

-- Function to prevent any delete
CREATE OR REPLACE FUNCTION pb_s1.prevent_retry_delete()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'pb_s1.retry_state is immutable - DELETE not allowed. History must be preserved.';
END;
$$ LANGUAGE plpgsql;

-- Trigger: Block all updates
CREATE TRIGGER trg_retry_state_no_update
BEFORE UPDATE ON pb_s1.retry_state
FOR EACH ROW
EXECUTE FUNCTION pb_s1.prevent_retry_update();

-- Trigger: Block all deletes
CREATE TRIGGER trg_retry_state_no_delete
BEFORE DELETE ON pb_s1.retry_state
FOR EACH ROW
EXECUTE FUNCTION pb_s1.prevent_retry_delete();

COMMENT ON TRIGGER trg_retry_state_no_update ON pb_s1.retry_state IS
    'Immutability guarantee: no updates allowed';
COMMENT ON TRIGGER trg_retry_state_no_delete ON pb_s1.retry_state IS
    'Immutability guarantee: no deletes allowed';
