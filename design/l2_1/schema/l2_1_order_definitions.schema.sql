-- =============================================================================
-- L2.1 ORDER DEFINITIONS TABLE
-- =============================================================================
-- Schema ID: OSD_L2_1
-- Version: 1.0.0
-- Status: CANONICAL (tables define, MD explains)
-- Created: 2026-01-07
--
-- GOVERNANCE INTENT:
-- This table defines the complete set of epistemic orders (O1-O5).
-- Orders are FROZEN. No new orders may be added.
-- Order shapes and constraints are canonical definitions.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- MAIN TABLE: l2_1_order_definitions
-- -----------------------------------------------------------------------------

CREATE TABLE l2_1_order_definitions (
    -- =========================================================================
    -- IDENTITY
    -- =========================================================================

    -- Order ID (O1, O2, O3, O4, O5)
    order_id VARCHAR(5) PRIMARY KEY
        CHECK (order_id IN ('O1', 'O2', 'O3', 'O4', 'O5')),

    -- Order name
    order_name VARCHAR(50) NOT NULL,

    -- Order meaning (short description)
    meaning TEXT NOT NULL,

    -- =========================================================================
    -- ORDER PROPERTIES
    -- =========================================================================

    -- Epistemic depth
    depth VARCHAR(20) NOT NULL
        CHECK (depth IN ('shallow', 'list', 'single', 'relational', 'terminal')),

    -- Whether this order can expand to deeper orders
    expandable BOOLEAN NOT NULL DEFAULT true,

    -- Whether content at this order is mutable
    mutable BOOLEAN NOT NULL DEFAULT false
        CHECK (mutable = false),  -- L2.1 is read-only

    -- Authority level (always NONE)
    authority VARCHAR(10) NOT NULL DEFAULT 'NONE'
        CHECK (authority = 'NONE'),

    -- Is this order terminal (O5 only)
    is_terminal BOOLEAN NOT NULL DEFAULT false,

    -- =========================================================================
    -- SHAPE DEFINITION
    -- =========================================================================

    -- Required fields for this order (JSONB)
    required_fields JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Optional fields for this order (JSONB)
    optional_fields JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- =========================================================================
    -- NAVIGATION RULES
    -- =========================================================================

    -- Which orders this can navigate to (JSONB array)
    navigates_to JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- =========================================================================
    -- CONSTRAINTS & PROHIBITIONS
    -- =========================================================================

    -- Hard prohibitions for this order (JSONB array)
    hard_prohibitions JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Validation rules (JSONB)
    validation_rules JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- =========================================================================
    -- GOVERNANCE
    -- =========================================================================

    -- Orders are frozen
    is_frozen BOOLEAN NOT NULL DEFAULT true
        CHECK (is_frozen = true),

    -- =========================================================================
    -- METADATA
    -- =========================================================================

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Version for reference
    version INTEGER NOT NULL DEFAULT 1
);

-- -----------------------------------------------------------------------------
-- ORDER TRANSITIONS TABLE
-- -----------------------------------------------------------------------------

CREATE TABLE l2_1_order_transitions (
    -- Source order
    from_order VARCHAR(5) NOT NULL,

    -- Target order
    to_order VARCHAR(5) NOT NULL,

    -- Is this transition valid?
    is_valid BOOLEAN NOT NULL DEFAULT true,

    -- Reason if invalid
    invalid_reason TEXT,

    PRIMARY KEY (from_order, to_order),

    -- Foreign keys
    CONSTRAINT fk_from_order FOREIGN KEY (from_order)
        REFERENCES l2_1_order_definitions(order_id),
    CONSTRAINT fk_to_order FOREIGN KEY (to_order)
        REFERENCES l2_1_order_definitions(order_id)
);

-- -----------------------------------------------------------------------------
-- TRIGGERS
-- -----------------------------------------------------------------------------

-- Prevent modification of frozen orders
CREATE OR REPLACE FUNCTION check_order_frozen()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Orders are frozen. Cannot modify order: %', OLD.order_id;
    END IF;

    -- Only allow initial seeding
    IF TG_OP = 'INSERT' THEN
        -- Check if table already has 5 rows
        IF (SELECT COUNT(*) FROM l2_1_order_definitions) >= 5 THEN
            RAISE EXCEPTION 'Cannot add new orders. O1-O5 are the complete set.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: This trigger should be enabled AFTER initial seeding
-- CREATE TRIGGER trg_check_order_frozen
--     BEFORE INSERT OR UPDATE OR DELETE ON l2_1_order_definitions
--     FOR EACH ROW
--     EXECUTE FUNCTION check_order_frozen();

-- -----------------------------------------------------------------------------
-- GOVERNANCE COMMENTS
-- -----------------------------------------------------------------------------

COMMENT ON TABLE l2_1_order_definitions IS
    'L2.1 Order Definitions - FROZEN O1-O5 epistemic orders. No additions allowed.';

COMMENT ON COLUMN l2_1_order_definitions.order_id IS
    'One of O1, O2, O3, O4, O5. No other values permitted.';

COMMENT ON COLUMN l2_1_order_definitions.is_terminal IS
    'Only O5 (Proof) is terminal. O5 has no further navigation.';

COMMENT ON COLUMN l2_1_order_definitions.mutable IS
    'GOVERNANCE: Must always be false. L2.1 is read-only.';

COMMENT ON COLUMN l2_1_order_definitions.authority IS
    'GOVERNANCE: Must always be NONE. L2.1 has no authority.';

COMMENT ON TABLE l2_1_order_transitions IS
    'Valid and invalid order transitions. Used for navigation validation.';
