-- =============================================================================
-- L2.1 SURFACE REGISTRY TABLE
-- =============================================================================
-- Purpose: This table IS the L2 Constitution in data form.
-- Defines WHAT EXISTS, WHERE IT LIVES, and HOW DEEP IT CAN GO.
-- Nothing about execution.
--
-- INVARIANT: If it's not in this table, it DOES NOT EXIST in L2.1.
--
-- Status: CANONICAL
-- Created: 2026-01-07
-- =============================================================================

-- -----------------------------------------------------------------------------
-- ENUM DEFINITIONS
-- -----------------------------------------------------------------------------

-- Surface status lifecycle
CREATE TYPE l2_1_surface_status AS ENUM (
    'draft',      -- Under development, not yet validated
    'validated',  -- Reviewed and approved, ready for use
    'frozen'      -- Constitutional lock, changes require amendment
);

-- Authority level (L2.1 is ALWAYS 'NONE')
-- This is a CHECK constraint, not an enum, to make violation explicit
-- CREATE TYPE l2_1_authority AS ENUM ('NONE');

-- -----------------------------------------------------------------------------
-- MAIN TABLE: l2_1_surface_registry
-- -----------------------------------------------------------------------------
-- This table IS the L2 constitution in data form.

CREATE TABLE l2_1_surface_registry (
    -- =========================================================================
    -- IDENTITY (Primary Key = Surface ID)
    -- =========================================================================

    -- Surface ID is the canonical trace key
    -- Format: DOMAIN.SUBDOMAIN.TOPIC (e.g., OVERVIEW.SYSTEM_HEALTH.PROTECTION_STATUS)
    surface_id              TEXT PRIMARY KEY,

    -- =========================================================================
    -- DOMAIN BINDING (Must match L1 Constitution)
    -- =========================================================================

    -- Domain must be one of the 5 frozen L1 domains
    domain                  TEXT NOT NULL CHECK (
        domain IN ('Overview', 'Activity', 'Incidents', 'Policies', 'Logs')
    ),

    -- Subdomain within the domain
    subdomain               TEXT NOT NULL,

    -- Specific topic within subdomain
    topic                   TEXT NOT NULL,

    -- Display order within subdomain
    topic_order             INTEGER NOT NULL,

    -- =========================================================================
    -- EPISTEMIC DEPTH AVAILABILITY (O1-O5)
    -- =========================================================================
    -- Defines which epistemic orders are available for this surface.
    -- O1 = Snapshot (always available)
    -- O2 = Presence (list)
    -- O3 = Explanation (detail)
    -- O4 = Context (impact)
    -- O5 = Proof (terminal, immutable)

    o1_enabled              BOOLEAN NOT NULL DEFAULT true,   -- Snapshot always available
    o2_enabled              BOOLEAN NOT NULL DEFAULT false,  -- Presence list
    o3_enabled              BOOLEAN NOT NULL DEFAULT false,  -- Detail explanation
    o4_enabled              BOOLEAN NOT NULL DEFAULT false,  -- Context/impact
    o5_enabled              BOOLEAN NOT NULL DEFAULT false,  -- Proof (terminal)

    -- =========================================================================
    -- INTERPRETER DEPENDENCY
    -- =========================================================================
    -- Surfaces at O3+ typically require Phase-2 interpreter projection

    requires_interpreter    BOOLEAN NOT NULL,  -- Needs Phase-2 interpreter
    requires_ir_hash        BOOLEAN NOT NULL,  -- Needs interpreter result hash

    -- =========================================================================
    -- GOVERNANCE CONSTRAINTS
    -- =========================================================================

    -- Authority level: MUST be 'NONE' for all L2.1 surfaces
    -- This is a constitutional constraint, not a choice
    authority_level         TEXT NOT NULL DEFAULT 'NONE' CHECK (
        authority_level = 'NONE'
    ),

    -- Replay support: Can this surface be replayed from historical data?
    replay_supported        BOOLEAN NOT NULL,

    -- Immutable history: Once recorded, can history be modified?
    -- Should be TRUE for all L2.1 surfaces
    immutable_history       BOOLEAN NOT NULL DEFAULT true,

    -- =========================================================================
    -- STATUS & METADATA
    -- =========================================================================

    status                  l2_1_surface_status NOT NULL DEFAULT 'draft',
    notes                   TEXT,

    -- Timestamps
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- =========================================================================
    -- CONSTRAINTS
    -- =========================================================================

    -- Ensure surface_id format matches DOMAIN.SUBDOMAIN.TOPIC
    CONSTRAINT chk_surface_id_format CHECK (
        surface_id ~ '^[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*$'
    ),

    -- O5 requires O3 and O4 to be enabled (proof requires context)
    CONSTRAINT chk_o5_requires_depth CHECK (
        NOT o5_enabled OR (o3_enabled AND o4_enabled)
    ),

    -- O4 requires O3 to be enabled (context requires explanation)
    CONSTRAINT chk_o4_requires_o3 CHECK (
        NOT o4_enabled OR o3_enabled
    ),

    -- O3+ requires interpreter
    CONSTRAINT chk_interpreter_for_depth CHECK (
        NOT (o3_enabled OR o4_enabled OR o5_enabled) OR requires_interpreter
    ),

    -- ir_hash required if interpreter required
    CONSTRAINT chk_ir_hash_with_interpreter CHECK (
        NOT requires_interpreter OR requires_ir_hash
    )
);

-- -----------------------------------------------------------------------------
-- INDEXES
-- -----------------------------------------------------------------------------

CREATE INDEX idx_surface_domain ON l2_1_surface_registry(domain);
CREATE INDEX idx_surface_subdomain ON l2_1_surface_registry(domain, subdomain);
CREATE INDEX idx_surface_status ON l2_1_surface_registry(status);
CREATE INDEX idx_surface_depth ON l2_1_surface_registry(o3_enabled, o4_enabled, o5_enabled);

-- -----------------------------------------------------------------------------
-- TRIGGERS
-- -----------------------------------------------------------------------------

-- Prevent modification of frozen surfaces
CREATE OR REPLACE FUNCTION check_surface_frozen()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'frozen' AND TG_OP = 'UPDATE' THEN
        -- Only allow status changes (for deprecation)
        IF NEW.surface_id != OLD.surface_id
           OR NEW.domain != OLD.domain
           OR NEW.subdomain != OLD.subdomain
           OR NEW.topic != OLD.topic
           OR NEW.authority_level != OLD.authority_level THEN
            RAISE EXCEPTION 'Cannot modify frozen surface: %', OLD.surface_id;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' AND OLD.status = 'frozen' THEN
        RAISE EXCEPTION 'Cannot delete frozen surface: %', OLD.surface_id;
    END IF;

    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_surface_frozen
    BEFORE UPDATE OR DELETE ON l2_1_surface_registry
    FOR EACH ROW
    EXECUTE FUNCTION check_surface_frozen();

-- -----------------------------------------------------------------------------
-- COMMENTS
-- -----------------------------------------------------------------------------

COMMENT ON TABLE l2_1_surface_registry IS
    'L2.1 Surface Registry - THE L2 CONSTITUTION IN DATA FORM. If not in this table, it does not exist.';

COMMENT ON COLUMN l2_1_surface_registry.surface_id IS
    'Canonical trace key. Format: DOMAIN.SUBDOMAIN.TOPIC. Primary key.';

COMMENT ON COLUMN l2_1_surface_registry.authority_level IS
    'GOVERNANCE: Must ALWAYS be NONE. L2.1 has no authority. Constitutional constraint.';

COMMENT ON COLUMN l2_1_surface_registry.o5_enabled IS
    'Proof level (terminal). Once enabled, content at O5 is immutable.';

COMMENT ON COLUMN l2_1_surface_registry.requires_interpreter IS
    'True if surface requires Phase-2 interpreter projection for O3+ depth.';
