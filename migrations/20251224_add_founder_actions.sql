-- migrations/20251224_add_founder_actions.sql
-- M29 Category 6: Founder Action Paths
-- Immutable audit records for founder actions on tenants, API keys, and incidents
BEGIN;

-- NOTE: tenants table may not exist yet - throttle_factor column will be added
-- when tenants table is created. For now, we just create the founder_actions table.

-- Founder Actions table - immutable audit trail
CREATE TABLE IF NOT EXISTS founder_actions (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,

  -- Action type
  action_type TEXT NOT NULL CHECK (action_type IN (
    'FREEZE_TENANT',
    'THROTTLE_TENANT',
    'FREEZE_API_KEY',
    'OVERRIDE_INCIDENT',
    'UNFREEZE_TENANT',
    'UNTHROTTLE_TENANT',
    'UNFREEZE_API_KEY'
  )),

  -- Target
  target_type TEXT NOT NULL CHECK (target_type IN ('TENANT', 'API_KEY', 'INCIDENT')),
  target_id TEXT NOT NULL,
  target_name TEXT,

  -- Reason (required for audit)
  reason_code TEXT NOT NULL CHECK (reason_code IN (
    'COST_ANOMALY',
    'POLICY_VIOLATION',
    'RETRY_LOOP',
    'ABUSE_SUSPECTED',
    'FALSE_POSITIVE',
    'OTHER'
  )),
  reason_note TEXT CHECK (LENGTH(reason_note) <= 500),

  -- Source incident (if action was triggered from incident view)
  source_incident_id TEXT,

  -- Founder who took action (required)
  founder_id TEXT NOT NULL,
  founder_email TEXT NOT NULL,
  mfa_verified BOOLEAN NOT NULL DEFAULT false,

  -- Timestamps
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  reversed_at TIMESTAMPTZ,
  reversed_by_action_id TEXT REFERENCES founder_actions(id),

  -- Status tracking
  is_active BOOLEAN NOT NULL DEFAULT true,
  is_reversible BOOLEAN NOT NULL DEFAULT true
);

-- Indexes for founder_actions
CREATE INDEX IF NOT EXISTS idx_founder_actions_target
  ON founder_actions (target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_founder_actions_founder
  ON founder_actions (founder_id);
CREATE INDEX IF NOT EXISTS idx_founder_actions_applied_at
  ON founder_actions (applied_at DESC);
CREATE INDEX IF NOT EXISTS idx_founder_actions_active
  ON founder_actions (is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_founder_actions_source_incident
  ON founder_actions (source_incident_id) WHERE source_incident_id IS NOT NULL;

-- Composite index for rate limiting check
CREATE INDEX IF NOT EXISTS idx_founder_actions_rate_limit
  ON founder_actions (founder_id, applied_at DESC);

-- Add comments for documentation
COMMENT ON TABLE founder_actions IS 'M29 Category 6: Immutable audit trail for founder actions on tenants, API keys, and incidents';
COMMENT ON COLUMN founder_actions.action_type IS 'Type of action: FREEZE_TENANT, THROTTLE_TENANT, FREEZE_API_KEY, OVERRIDE_INCIDENT, and reversals';
COMMENT ON COLUMN founder_actions.is_reversible IS 'Whether action can be reversed (OVERRIDE_INCIDENT = false)';
COMMENT ON COLUMN founder_actions.mfa_verified IS 'MFA is required for all founder actions';

-- =============================================================================
-- IMMUTABILITY ENFORCEMENT (Append-Only)
-- =============================================================================

-- Create function to reject updates (only reversed_at and reversed_by can be updated)
CREATE OR REPLACE FUNCTION reject_founder_action_update()
RETURNS TRIGGER AS $$
BEGIN
  -- Allow updating reversed_at and reversed_by_action_id (for reversal flow)
  IF OLD.reversed_at IS NULL AND NEW.reversed_at IS NOT NULL THEN
    -- This is a reversal update - allowed
    IF OLD.is_active = true AND NEW.is_active = false THEN
      RETURN NEW;
    END IF;
  END IF;

  -- All other updates are rejected
  RAISE EXCEPTION 'founder_actions table is append-only. Only reversal updates allowed.';
END;
$$ LANGUAGE plpgsql;

-- Create function to reject deletes
CREATE OR REPLACE FUNCTION reject_founder_action_delete()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'founder_actions table is append-only. DELETE not allowed.';
END;
$$ LANGUAGE plpgsql;

-- Create triggers
DROP TRIGGER IF EXISTS founder_actions_no_update ON founder_actions;
DROP TRIGGER IF EXISTS founder_actions_no_delete ON founder_actions;

CREATE TRIGGER founder_actions_no_update
  BEFORE UPDATE ON founder_actions
  FOR EACH ROW
  EXECUTE FUNCTION reject_founder_action_update();

CREATE TRIGGER founder_actions_no_delete
  BEFORE DELETE ON founder_actions
  FOR EACH ROW
  EXECUTE FUNCTION reject_founder_action_delete();

COMMIT;
