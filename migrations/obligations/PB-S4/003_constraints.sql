-- PB-S4: Constraints
-- Semantic constraints for policy versioning

-- Constraint: Only one active version per policy
-- (partial unique index - more efficient than trigger)
CREATE UNIQUE INDEX uq_policy_one_active
ON pb_s4.policy_version(policy_id)
WHERE is_active = true;

-- Constraint: Active version must have activation info
ALTER TABLE pb_s4.policy_version
ADD CONSTRAINT chk_active_has_activation CHECK (
    NOT (is_active = true AND (activated_at IS NULL OR activated_by IS NULL))
);

-- Constraint: Inactive version should not have activation info
-- (relaxed - we keep activation history even after deactivation)

COMMENT ON INDEX uq_policy_one_active IS
    'Only one active version per policy (partial unique index)';
COMMENT ON CONSTRAINT chk_active_has_activation ON pb_s4.policy_version IS
    'Active versions must have activation timestamp and actor';
