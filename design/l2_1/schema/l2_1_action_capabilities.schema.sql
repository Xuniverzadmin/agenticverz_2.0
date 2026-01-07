-- =============================================================================
-- L2.1 ACTION CAPABILITIES TABLE
-- =============================================================================
-- Purpose: Separates READ/DOWNLOAD from WRITE/ACTIVATE actions.
-- Hard governance: L2.1 = READ/DOWNLOAD only. WRITE/ACTIVATE = GC_L only.
--
-- INVARIANT: No action may violate layer routing.
-- INVARIANT: L2.1 surfaces NEVER have WRITE or ACTIVATE capabilities.
--
-- Status: CANONICAL
-- Created: 2026-01-07
-- =============================================================================

-- -----------------------------------------------------------------------------
-- ENUM DEFINITIONS
-- -----------------------------------------------------------------------------

-- Action types (what the UI can DO with data)
CREATE TYPE l2_1_action_type AS ENUM (
    'read',       -- Display data (always allowed in L2.1)
    'download',   -- Export data (allowed in L2.1)
    'write',      -- Modify data (NEVER in L2.1 - GC_L only)
    'activate'    -- Trigger execution (NEVER in L2.1 - GC_L only)
);

-- Layer routing (where actions are processed)
CREATE TYPE l2_1_layer_route AS ENUM (
    'L1_UI',      -- Presentation only (skin)
    'L2_1',       -- Epistemic orchestration (READ/DOWNLOAD only)
    'GC_L'        -- Governance-confirmed layer (WRITE/ACTIVATE)
);

-- Confirmation requirements for GC_L actions
CREATE TYPE l2_1_confirmation_type AS ENUM (
    'none',                    -- No confirmation (READ/DOWNLOAD)
    'single_click',            -- Single confirmation dialog
    'double_confirm',          -- Confirm twice (destructive actions)
    'human_approval_required'  -- Requires async human approval
);

-- -----------------------------------------------------------------------------
-- MAIN TABLE: l2_1_action_capabilities
-- -----------------------------------------------------------------------------

CREATE TABLE l2_1_action_capabilities (
    -- =========================================================================
    -- IDENTITY
    -- =========================================================================

    -- Unique action capability ID
    capability_id           TEXT PRIMARY KEY,

    -- Surface this action belongs to
    surface_id              TEXT NOT NULL REFERENCES l2_1_surface_registry(surface_id),

    -- =========================================================================
    -- ACTION DEFINITION
    -- =========================================================================

    -- What type of action is this?
    action_type             l2_1_action_type NOT NULL,

    -- Human-readable action name (e.g., "View Incident", "Download Report")
    action_name             TEXT NOT NULL,

    -- Human-readable description
    action_description      TEXT,

    -- =========================================================================
    -- LAYER ROUTING (CONSTITUTIONAL)
    -- =========================================================================

    -- Which layer handles this action?
    layer_route             l2_1_layer_route NOT NULL,

    -- =========================================================================
    -- CONFIRMATION REQUIREMENTS (GC_L only)
    -- =========================================================================

    -- What confirmation is required?
    confirmation_type       l2_1_confirmation_type NOT NULL DEFAULT 'none',

    -- Confirmation dialog message (for GC_L actions)
    confirmation_message    TEXT,

    -- =========================================================================
    -- GOVERNANCE CONSTRAINTS
    -- =========================================================================

    -- Is this action enabled?
    is_enabled              BOOLEAN NOT NULL DEFAULT true,

    -- Display order within surface
    display_order           INTEGER NOT NULL DEFAULT 0,

    -- =========================================================================
    -- AUDIT METADATA
    -- =========================================================================

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- =========================================================================
    -- CONSTRAINTS (CONSTITUTIONAL)
    -- =========================================================================

    -- L2.1 surfaces can ONLY have READ or DOWNLOAD actions
    -- WRITE and ACTIVATE must route to GC_L
    CONSTRAINT chk_l2_1_read_only CHECK (
        NOT (layer_route = 'L2_1' AND action_type IN ('write', 'activate'))
    ),

    -- L1_UI can only have READ actions (display only)
    CONSTRAINT chk_l1_ui_read_only CHECK (
        NOT (layer_route = 'L1_UI' AND action_type != 'read')
    ),

    -- WRITE and ACTIVATE actions MUST have confirmation
    CONSTRAINT chk_gc_l_requires_confirmation CHECK (
        NOT (action_type IN ('write', 'activate') AND confirmation_type = 'none')
    ),

    -- GC_L actions MUST have confirmation message
    CONSTRAINT chk_gc_l_requires_message CHECK (
        NOT (layer_route = 'GC_L' AND confirmation_message IS NULL)
    ),

    -- Unique action per surface
    CONSTRAINT uq_surface_action UNIQUE (surface_id, action_name)
);

-- -----------------------------------------------------------------------------
-- INDEXES
-- -----------------------------------------------------------------------------

CREATE INDEX idx_action_surface ON l2_1_action_capabilities(surface_id);
CREATE INDEX idx_action_type ON l2_1_action_capabilities(action_type);
CREATE INDEX idx_action_layer ON l2_1_action_capabilities(layer_route);
CREATE INDEX idx_action_enabled ON l2_1_action_capabilities(is_enabled) WHERE is_enabled = true;

-- -----------------------------------------------------------------------------
-- TRIGGERS
-- -----------------------------------------------------------------------------

-- Update timestamp on modification
CREATE OR REPLACE FUNCTION update_action_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_action_timestamp
    BEFORE UPDATE ON l2_1_action_capabilities
    FOR EACH ROW
    EXECUTE FUNCTION update_action_timestamp();

-- -----------------------------------------------------------------------------
-- GOVERNANCE VIEW: Show all actions with layer routing
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW v_l2_1_action_governance AS
SELECT
    ac.capability_id,
    ac.surface_id,
    sr.domain,
    sr.subdomain,
    sr.topic,
    ac.action_type,
    ac.action_name,
    ac.layer_route,
    ac.confirmation_type,
    ac.confirmation_message,
    ac.is_enabled,
    CASE
        WHEN ac.action_type IN ('read', 'download') THEN 'ALLOWED_IN_L2_1'
        WHEN ac.action_type IN ('write', 'activate') THEN 'GC_L_ONLY'
    END AS governance_status
FROM l2_1_action_capabilities ac
JOIN l2_1_surface_registry sr ON ac.surface_id = sr.surface_id
ORDER BY sr.domain, sr.subdomain, sr.topic, ac.display_order;

-- -----------------------------------------------------------------------------
-- VALIDATION FUNCTION: Check all actions comply
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_l2_1_action_governance()
RETURNS TABLE (
    violation_id INTEGER,
    capability_id TEXT,
    surface_id TEXT,
    action_type l2_1_action_type,
    layer_route l2_1_layer_route,
    violation_type TEXT,
    violation_message TEXT
) AS $$
DECLARE
    v_id INTEGER := 0;
BEGIN
    -- Check for WRITE/ACTIVATE actions routed to L2_1
    FOR capability_id, surface_id, action_type, layer_route IN
        SELECT ac.capability_id, ac.surface_id, ac.action_type, ac.layer_route
        FROM l2_1_action_capabilities ac
        WHERE ac.layer_route = 'L2_1' AND ac.action_type IN ('write', 'activate')
    LOOP
        v_id := v_id + 1;
        violation_type := 'L2_1_WRITE_VIOLATION';
        violation_message := 'L2.1 cannot have WRITE or ACTIVATE actions';
        RETURN NEXT;
    END LOOP;

    -- Check for GC_L actions without confirmation
    FOR capability_id, surface_id, action_type, layer_route IN
        SELECT ac.capability_id, ac.surface_id, ac.action_type, ac.layer_route
        FROM l2_1_action_capabilities ac
        WHERE ac.layer_route = 'GC_L' AND ac.confirmation_type = 'none'
    LOOP
        v_id := v_id + 1;
        violation_type := 'GC_L_NO_CONFIRMATION';
        violation_message := 'GC_L actions require confirmation';
        RETURN NEXT;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- COMMENTS
-- -----------------------------------------------------------------------------

COMMENT ON TABLE l2_1_action_capabilities IS
    'L2.1 Action Capabilities - Separates READ/DOWNLOAD from WRITE/ACTIVATE. Constitutional layer routing.';

COMMENT ON COLUMN l2_1_action_capabilities.action_type IS
    'READ/DOWNLOAD allowed in L2.1. WRITE/ACTIVATE requires GC_L.';

COMMENT ON COLUMN l2_1_action_capabilities.layer_route IS
    'CONSTITUTIONAL: L2_1 for read-only, GC_L for mutations. L1_UI for display only.';

COMMENT ON COLUMN l2_1_action_capabilities.confirmation_type IS
    'GC_L actions MUST have confirmation. Human safety requirement.';

COMMENT ON CONSTRAINT chk_l2_1_read_only ON l2_1_action_capabilities IS
    'CONSTITUTIONAL: L2.1 is presentation-only. No writes. No activations.';

COMMENT ON CONSTRAINT chk_gc_l_requires_confirmation ON l2_1_action_capabilities IS
    'CONSTITUTIONAL: All mutations require human confirmation.';

