-- PB-S2: Constraints
-- Semantic constraints for crash recovery state

-- Constraint: DONE status must have cleared recovery_cursor
-- (cursor is only needed during recovery, not after)
ALTER TABLE pb_s2.crash_recovery
ADD CONSTRAINT chk_done_no_cursor CHECK (
    NOT (status = 'DONE' AND recovery_cursor != '{}'::jsonb)
);

-- Constraint: RECOVERING must have claim info
ALTER TABLE pb_s2.crash_recovery
ADD CONSTRAINT chk_recovering_has_claim CHECK (
    NOT (status = 'RECOVERING' AND (claimed_at IS NULL OR claimed_by IS NULL))
);

-- Constraint: ACTIVE should not have claim info
ALTER TABLE pb_s2.crash_recovery
ADD CONSTRAINT chk_active_no_claim CHECK (
    NOT (status = 'ACTIVE' AND claimed_at IS NOT NULL)
);

COMMENT ON CONSTRAINT chk_done_no_cursor ON pb_s2.crash_recovery IS
    'DONE status must have empty recovery_cursor';
COMMENT ON CONSTRAINT chk_recovering_has_claim ON pb_s2.crash_recovery IS
    'RECOVERING status must have claim info';
COMMENT ON CONSTRAINT chk_active_no_claim ON pb_s2.crash_recovery IS
    'ACTIVE status should not have claim info';
