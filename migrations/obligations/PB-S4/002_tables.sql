-- PB-S4: Tables
-- Policy and policy version tables

-- Base policy definition
CREATE TABLE pb_s4.policy (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    policy_type TEXT NOT NULL CHECK (policy_type IN ('BUDGET', 'RATE_LIMIT', 'APPROVAL', 'SAFETY', 'CUSTOM')),
    scope TEXT NOT NULL CHECK (scope IN ('TENANT', 'PROJECT', 'WORKFLOW', 'GLOBAL')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Policy versions (immutable)
CREATE TABLE pb_s4.policy_version (
    id BIGSERIAL PRIMARY KEY,
    policy_id UUID NOT NULL REFERENCES pb_s4.policy(id),
    version INTEGER NOT NULL CHECK (version >= 1),

    -- Policy definition (immutable once created)
    definition JSONB NOT NULL,

    -- Provenance
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Activation status
    is_active BOOLEAN NOT NULL DEFAULT false,
    activated_at TIMESTAMPTZ,
    activated_by TEXT,

    -- Each policy can only have one version N
    UNIQUE(policy_id, version)
);

-- Index for finding active policy version
CREATE INDEX idx_policy_version_active
ON pb_s4.policy_version(policy_id, is_active)
WHERE is_active = true;

-- Index for version history
CREATE INDEX idx_policy_version_history
ON pb_s4.policy_version(policy_id, version DESC);

COMMENT ON TABLE pb_s4.policy IS
    'Policy definitions. Name is unique.';
COMMENT ON TABLE pb_s4.policy_version IS
    'Immutable policy versions. New version = new row.';
COMMENT ON COLUMN pb_s4.policy_version.definition IS
    'Policy rules as JSONB. Immutable after creation.';
COMMENT ON COLUMN pb_s4.policy_version.is_active IS
    'Only one version per policy can be active';
