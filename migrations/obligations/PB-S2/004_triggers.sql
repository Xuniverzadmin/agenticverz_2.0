-- PB-S2: Triggers
-- Audit and state transition enforcement

-- Function: Update timestamp on any change
CREATE OR REPLACE FUNCTION pb_s2.update_timestamp()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update updated_at
CREATE TRIGGER trg_crash_recovery_updated
BEFORE UPDATE ON pb_s2.crash_recovery
FOR EACH ROW
EXECUTE FUNCTION pb_s2.update_timestamp();

-- Function: Enforce valid state transitions
CREATE OR REPLACE FUNCTION pb_s2.enforce_status_transition()
RETURNS trigger AS $$
BEGIN
    -- Valid transitions:
    -- ACTIVE -> RECOVERING (claimed for recovery)
    -- ACTIVE -> DONE (completed normally)
    -- RECOVERING -> DONE (recovery completed)
    -- RECOVERING -> ACTIVE (recovery abandoned/failed)

    IF OLD.status = 'DONE' THEN
        RAISE EXCEPTION 'Cannot transition from DONE status. Workflow is terminal.';
    END IF;

    IF OLD.status = 'ACTIVE' AND NEW.status NOT IN ('RECOVERING', 'DONE') THEN
        RAISE EXCEPTION 'ACTIVE can only transition to RECOVERING or DONE, got: %', NEW.status;
    END IF;

    IF OLD.status = 'RECOVERING' AND NEW.status NOT IN ('DONE', 'ACTIVE') THEN
        RAISE EXCEPTION 'RECOVERING can only transition to DONE or ACTIVE, got: %', NEW.status;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Enforce status transitions
CREATE TRIGGER trg_crash_recovery_transition
BEFORE UPDATE OF status ON pb_s2.crash_recovery
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION pb_s2.enforce_status_transition();

-- Function: Clear claim on transition to ACTIVE
CREATE OR REPLACE FUNCTION pb_s2.clear_claim_on_active()
RETURNS trigger AS $$
BEGIN
    IF NEW.status = 'ACTIVE' AND OLD.status = 'RECOVERING' THEN
        NEW.claimed_at = NULL;
        NEW.claimed_by = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-clear claim when returning to ACTIVE
CREATE TRIGGER trg_crash_recovery_clear_claim
BEFORE UPDATE OF status ON pb_s2.crash_recovery
FOR EACH ROW
WHEN (NEW.status = 'ACTIVE')
EXECUTE FUNCTION pb_s2.clear_claim_on_active();

COMMENT ON TRIGGER trg_crash_recovery_updated ON pb_s2.crash_recovery IS
    'Auto-update updated_at timestamp';
COMMENT ON TRIGGER trg_crash_recovery_transition ON pb_s2.crash_recovery IS
    'Enforce valid status transitions';
COMMENT ON TRIGGER trg_crash_recovery_clear_claim ON pb_s2.crash_recovery IS
    'Clear claim info when returning to ACTIVE';
