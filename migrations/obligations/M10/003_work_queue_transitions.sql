-- M10: Work Queue Status Transitions
-- Purpose: Enforce valid state transitions for recovery candidates

-- Check current work_queue structure
-- Expected columns: id, candidate_id, status, priority, claimed_by, claimed_at, etc.

-- Function: Enforce valid status transitions
CREATE OR REPLACE FUNCTION m10_recovery.enforce_work_queue_transition()
RETURNS trigger AS $$
BEGIN
    -- Valid transitions:
    -- PENDING -> CLAIMED (worker claims it)
    -- PENDING -> CANCELLED (manual cancellation)
    -- CLAIMED -> COMPLETED (success)
    -- CLAIMED -> FAILED (failure)
    -- CLAIMED -> PENDING (release/timeout)
    -- FAILED -> PENDING (retry)
    -- COMPLETED is terminal
    -- CANCELLED is terminal

    IF OLD.status = 'COMPLETED' THEN
        RAISE EXCEPTION 'work_queue: Cannot transition from COMPLETED. Terminal state.';
    END IF;

    IF OLD.status = 'CANCELLED' THEN
        RAISE EXCEPTION 'work_queue: Cannot transition from CANCELLED. Terminal state.';
    END IF;

    IF OLD.status = 'PENDING' AND NEW.status NOT IN ('CLAIMED', 'CANCELLED') THEN
        RAISE EXCEPTION 'work_queue: PENDING can only transition to CLAIMED or CANCELLED, got: %', NEW.status;
    END IF;

    IF OLD.status = 'CLAIMED' AND NEW.status NOT IN ('COMPLETED', 'FAILED', 'PENDING') THEN
        RAISE EXCEPTION 'work_queue: CLAIMED can only transition to COMPLETED, FAILED, or PENDING, got: %', NEW.status;
    END IF;

    IF OLD.status = 'FAILED' AND NEW.status NOT IN ('PENDING', 'CANCELLED') THEN
        RAISE EXCEPTION 'work_queue: FAILED can only transition to PENDING (retry) or CANCELLED, got: %', NEW.status;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Enforce status transitions (only if status column exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'm10_recovery'
        AND table_name = 'work_queue'
        AND column_name = 'status'
    ) THEN
        -- Drop if exists to make idempotent
        DROP TRIGGER IF EXISTS trg_work_queue_transition ON m10_recovery.work_queue;

        CREATE TRIGGER trg_work_queue_transition
        BEFORE UPDATE OF status ON m10_recovery.work_queue
        FOR EACH ROW
        WHEN (OLD.status IS DISTINCT FROM NEW.status)
        EXECUTE FUNCTION m10_recovery.enforce_work_queue_transition();

        COMMENT ON TRIGGER trg_work_queue_transition ON m10_recovery.work_queue IS
            'Enforce valid status transitions for recovery queue';
    END IF;
END
$$;

-- Function: Update timestamp on work_queue changes
CREATE OR REPLACE FUNCTION m10_recovery.update_work_queue_timestamp()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update timestamp (if column exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'm10_recovery'
        AND table_name = 'work_queue'
        AND column_name = 'updated_at'
    ) THEN
        DROP TRIGGER IF EXISTS trg_work_queue_updated ON m10_recovery.work_queue;

        CREATE TRIGGER trg_work_queue_updated
        BEFORE UPDATE ON m10_recovery.work_queue
        FOR EACH ROW
        EXECUTE FUNCTION m10_recovery.update_work_queue_timestamp();
    END IF;
END
$$;
