-- PB-S1: Additional Constraints
-- These constraints enforce retry semantics beyond basic CHECK constraints

-- Constraint: attempt_no must be monotonically increasing per entity
-- (enforced via UNIQUE constraint in table definition)

-- Constraint: error must be present for FAILED status
ALTER TABLE pb_s1.retry_state
ADD CONSTRAINT chk_error_on_failure CHECK (
    (status = 'FAILED' AND error IS NOT NULL) OR
    (status != 'FAILED')
);

-- Constraint: process_after must be in the future for PENDING
-- (soft constraint - not enforced, as clock skew can occur)

COMMENT ON CONSTRAINT chk_error_on_failure ON pb_s1.retry_state IS
    'FAILED status requires error message';
