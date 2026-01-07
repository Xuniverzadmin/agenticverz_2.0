-- =============================================================================
-- L2.1 DOMAIN REGISTRY TABLE
-- =============================================================================
-- Schema ID: DSM_L2_1
-- Version: 1.0.0
-- Status: CANONICAL (tables define, MD explains)
-- Created: 2026-01-07
--
-- GOVERNANCE INTENT:
-- This table defines the complete set of L2.1 domains.
-- Domains MUST be a subset of the L1 Constitution.
-- No new domains may be added without L1 Constitution amendment.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- ENUM DEFINITIONS
-- -----------------------------------------------------------------------------

-- Domain status
CREATE TYPE l2_1_domain_status AS ENUM (
    'frozen',     -- Cannot be modified (default for v1 domains)
    'active',     -- In use, can be extended (subdomains/topics)
    'deprecated', -- Scheduled for removal
    'proposed'    -- Under review, not yet ratified
);

-- -----------------------------------------------------------------------------
-- MAIN TABLE: l2_1_domain_registry
-- -----------------------------------------------------------------------------

CREATE TABLE l2_1_domain_registry (
    -- =========================================================================
    -- IDENTITY
    -- =========================================================================

    -- Domain ID (primary key, human-readable)
    -- Must match L1 Constitution exactly
    domain_id VARCHAR(50) PRIMARY KEY,

    -- Human-readable domain name
    domain_name VARCHAR(100) NOT NULL,

    -- Core question this domain answers
    core_question TEXT NOT NULL,

    -- Status of this domain
    status l2_1_domain_status NOT NULL DEFAULT 'frozen',

    -- =========================================================================
    -- L1 CONSTITUTION BINDING
    -- =========================================================================

    -- Reference to L1 Constitution section
    l1_constitution_ref VARCHAR(100) NOT NULL,

    -- L1 Constitution version this domain aligns with
    l1_constitution_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',

    -- =========================================================================
    -- OBJECT FAMILY
    -- =========================================================================

    -- Object types that belong to this domain (JSONB array)
    object_family JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- =========================================================================
    -- FORBIDDEN CONTENT
    -- =========================================================================

    -- Content types that do NOT belong in this domain
    forbidden_content JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- =========================================================================
    -- GOVERNANCE
    -- =========================================================================

    -- Whether this domain is frozen (v1 domains are frozen)
    is_frozen BOOLEAN NOT NULL DEFAULT true,

    -- Amendment requires human ratification
    requires_ratification BOOLEAN NOT NULL DEFAULT true,

    -- =========================================================================
    -- METADATA
    -- =========================================================================

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    frozen_at TIMESTAMPTZ,
    frozen_by VARCHAR(100),

    -- Version for optimistic locking
    version INTEGER NOT NULL DEFAULT 1
);

-- -----------------------------------------------------------------------------
-- SUBDOMAIN TABLE: l2_1_subdomain_registry
-- -----------------------------------------------------------------------------

CREATE TABLE l2_1_subdomain_registry (
    -- Composite primary key
    domain_id VARCHAR(50) NOT NULL,
    subdomain_id VARCHAR(100) NOT NULL,

    PRIMARY KEY (domain_id, subdomain_id),

    -- Human-readable subdomain name
    subdomain_name VARCHAR(200) NOT NULL,

    -- Description of this subdomain
    description TEXT,

    -- Status
    status l2_1_domain_status NOT NULL DEFAULT 'active',

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Foreign key to domain
    CONSTRAINT fk_domain FOREIGN KEY (domain_id)
        REFERENCES l2_1_domain_registry(domain_id)
        ON DELETE RESTRICT
);

-- -----------------------------------------------------------------------------
-- TOPIC TABLE: l2_1_topic_registry
-- -----------------------------------------------------------------------------

CREATE TABLE l2_1_topic_registry (
    -- Composite primary key
    domain_id VARCHAR(50) NOT NULL,
    subdomain_id VARCHAR(100) NOT NULL,
    topic_id VARCHAR(100) NOT NULL,

    PRIMARY KEY (domain_id, subdomain_id, topic_id),

    -- Human-readable topic name
    topic_name VARCHAR(200) NOT NULL,

    -- Question this topic answers
    question TEXT NOT NULL,

    -- Status
    status l2_1_domain_status NOT NULL DEFAULT 'active',

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Foreign key to subdomain
    CONSTRAINT fk_subdomain FOREIGN KEY (domain_id, subdomain_id)
        REFERENCES l2_1_subdomain_registry(domain_id, subdomain_id)
        ON DELETE RESTRICT
);

-- -----------------------------------------------------------------------------
-- INDEXES
-- -----------------------------------------------------------------------------

CREATE INDEX idx_domain_status ON l2_1_domain_registry(status);
CREATE INDEX idx_domain_frozen ON l2_1_domain_registry(is_frozen);
CREATE INDEX idx_subdomain_domain ON l2_1_subdomain_registry(domain_id);
CREATE INDEX idx_topic_domain_subdomain ON l2_1_topic_registry(domain_id, subdomain_id);

-- -----------------------------------------------------------------------------
-- TRIGGERS
-- -----------------------------------------------------------------------------

-- Prevent modification of frozen domains
CREATE OR REPLACE FUNCTION check_domain_frozen()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.is_frozen = true AND TG_OP = 'UPDATE' THEN
        -- Allow only status changes for deprecation
        IF NEW.domain_id != OLD.domain_id
           OR NEW.domain_name != OLD.domain_name
           OR NEW.core_question != OLD.core_question
           OR NEW.l1_constitution_ref != OLD.l1_constitution_ref THEN
            RAISE EXCEPTION 'Cannot modify frozen domain: %', OLD.domain_id;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' AND OLD.is_frozen = true THEN
        RAISE EXCEPTION 'Cannot delete frozen domain: %', OLD.domain_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_domain_frozen
    BEFORE UPDATE OR DELETE ON l2_1_domain_registry
    FOR EACH ROW
    EXECUTE FUNCTION check_domain_frozen();

-- Update timestamp
CREATE OR REPLACE FUNCTION update_domain_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_domain_timestamp
    BEFORE UPDATE ON l2_1_domain_registry
    FOR EACH ROW
    EXECUTE FUNCTION update_domain_timestamp();

-- -----------------------------------------------------------------------------
-- GOVERNANCE COMMENTS
-- -----------------------------------------------------------------------------

COMMENT ON TABLE l2_1_domain_registry IS
    'L2.1 Domain Registry - FROZEN domains from L1 Constitution. No additions without amendment.';

COMMENT ON COLUMN l2_1_domain_registry.domain_id IS
    'Must match L1 Constitution exactly. Five frozen domains: overview, activity, incidents, policies, logs.';

COMMENT ON COLUMN l2_1_domain_registry.l1_constitution_ref IS
    'Reference to CUSTOMER_CONSOLE_V1_CONSTITUTION section. Required for traceability.';

COMMENT ON COLUMN l2_1_domain_registry.is_frozen IS
    'GOVERNANCE: v1 domains are frozen. Modification requires human ratification.';
