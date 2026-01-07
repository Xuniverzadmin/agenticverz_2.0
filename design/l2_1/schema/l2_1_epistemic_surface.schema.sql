-- =============================================================================
-- L2.1 EPISTEMIC SURFACE TABLE
-- =============================================================================
-- Schema ID: ESM_L2_1
-- Version: 1.0.0
-- Status: CANONICAL (tables define, MD explains)
-- Created: 2026-01-07
--
-- GOVERNANCE INTENT:
-- This table is the single source of truth for all L2.1 epistemic surfaces.
-- MD documentation is reference-only and must not diverge from this schema.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- ENUM DEFINITIONS
-- -----------------------------------------------------------------------------

-- Authority level (L2.1 is ALWAYS 'none')
CREATE TYPE l2_1_authority AS ENUM ('none');

-- Visibility levels for UI intent
CREATE TYPE l2_1_visibility AS ENUM (
    'public',           -- Visible without authentication
    'authenticated',    -- Visible to any authenticated user in tenant
    'role_gated',       -- Visible only to users with specific role
    'permission_gated'  -- Visible only with specific permission
);

-- Epistemic orders (O1-O5, frozen)
CREATE TYPE l2_1_order AS ENUM ('O1', 'O2', 'O3', 'O4', 'O5');

-- Evaluation modes from Phase-2
CREATE TYPE l2_1_evaluation_mode AS ENUM (
    'strict',   -- All assertions verified
    'advisory', -- Best-effort, some assertions skipped
    'replay'    -- Replay mode, read-only
);

-- Surface status
CREATE TYPE l2_1_surface_status AS ENUM (
    'draft',      -- Under development
    'active',     -- In production use
    'deprecated', -- Scheduled for removal
    'frozen'      -- Cannot be modified
);

-- -----------------------------------------------------------------------------
-- MAIN TABLE: l2_1_epistemic_surface
-- -----------------------------------------------------------------------------

CREATE TABLE l2_1_epistemic_surface (
    -- =========================================================================
    -- IDENTITY
    -- =========================================================================

    -- Primary key (UUID for global uniqueness)
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Human-readable surface ID (TRACE KEY)
    -- Format: DOMAIN.SUBDOMAIN.TOPIC (e.g., OVERVIEW.SYSTEM_HEALTH.PROTECTION_STATUS)
    surface_id VARCHAR(255) NOT NULL UNIQUE,

    -- Schema version for this surface definition
    schema_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',

    -- Layer identifier (always L2_1)
    layer VARCHAR(10) NOT NULL DEFAULT 'L2_1'
        CHECK (layer = 'L2_1'),

    -- Status of this surface
    status l2_1_surface_status NOT NULL DEFAULT 'draft',

    -- =========================================================================
    -- AUTHORITY (GOVERNANCE CONSTRAINT: ALWAYS NONE)
    -- =========================================================================

    -- Authority level - MUST be 'none' for all L2.1 surfaces
    -- This is a hard constraint, not a default
    authority l2_1_authority NOT NULL DEFAULT 'none'
        CHECK (authority = 'none'),

    -- =========================================================================
    -- DOMAIN BINDING (from DSM-L2.1)
    -- =========================================================================

    -- Domain ID (must reference l2_1_domain_registry)
    domain_id VARCHAR(50) NOT NULL,

    -- Subdomain ID (optional subdivision within domain)
    subdomain_id VARCHAR(100),

    -- Topic ID (specific topic within subdomain)
    topic_id VARCHAR(100) NOT NULL,

    -- Question this surface answers
    topic_question TEXT NOT NULL,

    -- Reference to L1 Constitution section
    l1_constitution_ref VARCHAR(100),

    -- =========================================================================
    -- EPISTEMIC ORDERS (from OSD-L2.1)
    -- =========================================================================

    -- Which orders are enabled for this surface (JSONB array)
    enabled_orders l2_1_order[] NOT NULL DEFAULT ARRAY['O1']::l2_1_order[],

    -- Order-specific configurations (JSONB for flexibility)
    -- Structure matches OSD-L2.1 definitions
    order_config JSONB NOT NULL DEFAULT '{
        "O1": {"enabled": true, "shape": {}},
        "O2": {"enabled": false, "shape": {}},
        "O3": {"enabled": false, "shape": {}},
        "O4": {"enabled": false, "shape": {}},
        "O5": {"enabled": false, "shape": {}, "terminal": true, "immutable": true}
    }'::jsonb,

    -- =========================================================================
    -- INTERPRETER PROJECTION (from IPC-L2.1)
    -- =========================================================================

    -- Projection configuration
    projection JSONB NOT NULL DEFAULT '{
        "ir_hash": null,
        "fact_snapshot_id": null,
        "evaluation_mode": "strict",
        "confidence_vector": {},
        "enrichment_allowed": false
    }'::jsonb,

    -- GOVERNANCE CONSTRAINT: enrichment_allowed must be false
    CONSTRAINT chk_no_enrichment CHECK (
        (projection->>'enrichment_allowed')::boolean = false
        OR projection->>'enrichment_allowed' IS NULL
    ),

    -- =========================================================================
    -- FACILITATION (from FCL-L2.1)
    -- =========================================================================

    -- Facilitation signals (non-authoritative)
    facilitation JSONB NOT NULL DEFAULT '{
        "authority": "NONE",
        "recommendations": [],
        "warnings": [],
        "confidence_bands": {},
        "signal_metadata": {
            "authoritative": false,
            "actionable": false,
            "mutable": false
        }
    }'::jsonb,

    -- GOVERNANCE CONSTRAINT: facilitation must be non-authoritative
    CONSTRAINT chk_facilitation_non_auth CHECK (
        facilitation->'signal_metadata'->>'authoritative' = 'false'
    ),

    -- =========================================================================
    -- UI INTENT (from UIS-L2.1)
    -- =========================================================================

    -- UI intent configuration
    ui_intent JSONB NOT NULL DEFAULT '{
        "visibility": "authenticated",
        "consent_required": false,
        "irreversible": false,
        "replay_available": false,
        "affordances": {
            "expandable": false,
            "filterable": false,
            "sortable": false,
            "exportable": false,
            "linkable": false,
            "searchable": false,
            "paginated": false
        }
    }'::jsonb,

    -- =========================================================================
    -- SCOPE CONSTRAINTS
    -- =========================================================================

    -- Tenant isolation (MUST be true)
    tenant_isolation BOOLEAN NOT NULL DEFAULT true
        CHECK (tenant_isolation = true),

    -- Project bound (typically true for Customer Console)
    project_bound BOOLEAN NOT NULL DEFAULT true,

    -- Jurisdiction
    jurisdiction VARCHAR(20) NOT NULL DEFAULT 'customer'
        CHECK (jurisdiction IN ('customer', 'founder', 'ops')),

    -- Scope constraints (JSONB)
    scope_constraints JSONB NOT NULL DEFAULT '{
        "cross_tenant_aggregation": false,
        "cross_project_aggregation": false,
        "authority_delegation": false
    }'::jsonb,

    -- GOVERNANCE CONSTRAINT: no cross-tenant
    CONSTRAINT chk_no_cross_tenant CHECK (
        (scope_constraints->>'cross_tenant_aggregation')::boolean = false
    ),

    -- =========================================================================
    -- METADATA
    -- =========================================================================

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Version for optimistic locking
    version INTEGER NOT NULL DEFAULT 1,

    -- =========================================================================
    -- FOREIGN KEYS
    -- =========================================================================

    CONSTRAINT fk_domain FOREIGN KEY (domain_id)
        REFERENCES l2_1_domain_registry(domain_id)
        ON DELETE RESTRICT
);

-- -----------------------------------------------------------------------------
-- INDEXES
-- -----------------------------------------------------------------------------

-- Primary lookup by surface_id (trace key)
CREATE UNIQUE INDEX idx_surface_id ON l2_1_epistemic_surface(surface_id);

-- Domain-based queries
CREATE INDEX idx_domain ON l2_1_epistemic_surface(domain_id);
CREATE INDEX idx_domain_subdomain ON l2_1_epistemic_surface(domain_id, subdomain_id);
CREATE INDEX idx_domain_subdomain_topic ON l2_1_epistemic_surface(domain_id, subdomain_id, topic_id);

-- Status-based queries
CREATE INDEX idx_status ON l2_1_epistemic_surface(status);

-- Jurisdiction queries
CREATE INDEX idx_jurisdiction ON l2_1_epistemic_surface(jurisdiction);

-- -----------------------------------------------------------------------------
-- TRIGGERS
-- -----------------------------------------------------------------------------

-- Update timestamp on modification
CREATE OR REPLACE FUNCTION update_l2_1_epistemic_surface_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_timestamp
    BEFORE UPDATE ON l2_1_epistemic_surface
    FOR EACH ROW
    EXECUTE FUNCTION update_l2_1_epistemic_surface_timestamp();

-- -----------------------------------------------------------------------------
-- GOVERNANCE COMMENTS
-- -----------------------------------------------------------------------------

COMMENT ON TABLE l2_1_epistemic_surface IS
    'L2.1 Epistemic Surface Matrix - CANONICAL SOURCE OF TRUTH. MD docs are reference only.';

COMMENT ON COLUMN l2_1_epistemic_surface.surface_id IS
    'Human-readable trace key. Format: DOMAIN.SUBDOMAIN.TOPIC. Must be unique.';

COMMENT ON COLUMN l2_1_epistemic_surface.authority IS
    'GOVERNANCE: Must ALWAYS be "none". L2.1 has no authority.';

COMMENT ON COLUMN l2_1_epistemic_surface.tenant_isolation IS
    'GOVERNANCE: Must ALWAYS be true. No cross-tenant data in L2.1.';

COMMENT ON CONSTRAINT chk_no_enrichment ON l2_1_epistemic_surface IS
    'GOVERNANCE: IPC-L2.1 prohibits enrichment of Phase-2 data.';

COMMENT ON CONSTRAINT chk_facilitation_non_auth ON l2_1_epistemic_surface IS
    'GOVERNANCE: FCL-L2.1 requires all signals to be non-authoritative.';

COMMENT ON CONSTRAINT chk_no_cross_tenant ON l2_1_epistemic_surface IS
    'GOVERNANCE: GA-004 prohibits cross-tenant scope.';
