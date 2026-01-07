-- =============================================================================
-- L2.1 ORDER DEFINITIONS SEED DATA
-- =============================================================================
-- Status: FROZEN
-- Created: 2026-01-07
-- Source: OSD-L2.1 (Order Surface Definition)
--
-- GOVERNANCE:
-- Orders O1-O5 are FROZEN. No new orders may be added.
-- These definitions are canonical and must not be modified.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- ORDER O1: SNAPSHOT
-- -----------------------------------------------------------------------------
INSERT INTO l2_1_order_definitions (
    order_id,
    order_name,
    meaning,
    depth,
    expandable,
    mutable,
    authority,
    is_terminal,
    required_fields,
    optional_fields,
    navigates_to,
    hard_prohibitions,
    validation_rules,
    is_frozen
) VALUES (
    'O1',
    'Snapshot',
    'Summary, scannable, shallow, safe entry point',
    'shallow',
    false,  -- O1 does not expand inline
    false,
    'NONE',
    false,
    '[
        {"field": "id", "type": "string", "description": "Unique identifier"},
        {"field": "status", "type": "enum", "values": ["healthy", "degraded", "critical", "unknown"], "description": "Current status indicator"},
        {"field": "label", "type": "string", "description": "Human-readable name"},
        {"field": "timestamp", "type": "iso8601", "description": "Last updated time"}
    ]'::jsonb,
    '[
        {"field": "metric_value", "type": "number", "description": "Primary metric if applicable"},
        {"field": "trend", "type": "enum", "values": ["up", "down", "stable", "unknown"], "description": "Trend indicator"}
    ]'::jsonb,
    '["O2"]'::jsonb,
    '[
        "No nested objects",
        "No arrays longer than 5 items",
        "No raw IDs without labels",
        "No actions or buttons",
        "No expandable content inline"
    ]'::jsonb,
    '{"max_items": 5, "max_depth": 1}'::jsonb,
    true
);

-- -----------------------------------------------------------------------------
-- ORDER O2: PRESENCE
-- -----------------------------------------------------------------------------
INSERT INTO l2_1_order_definitions (
    order_id,
    order_name,
    meaning,
    depth,
    expandable,
    mutable,
    authority,
    is_terminal,
    required_fields,
    optional_fields,
    navigates_to,
    hard_prohibitions,
    validation_rules,
    is_frozen
) VALUES (
    'O2',
    'Presence',
    'List of instances - Show me instances',
    'list',
    true,  -- Can expand to O3
    false,
    'NONE',
    false,
    '[
        {"field": "items", "type": "array", "description": "List of instance summaries"},
        {"field": "total_count", "type": "integer", "description": "Total items for pagination"},
        {"field": "page", "type": "integer", "description": "Current page"}
    ]'::jsonb,
    '[
        {"field": "filters_applied", "type": "object", "description": "Active filter state"},
        {"field": "sort_order", "type": "string", "description": "Current sort"}
    ]'::jsonb,
    '["O3"]'::jsonb,
    '[
        "No inline O3 expansion",
        "No cross-tenant items",
        "No items without valid scope",
        "No actions that mutate"
    ]'::jsonb,
    '{"requires_pagination": true, "scope_bound": true}'::jsonb,
    true
);

-- -----------------------------------------------------------------------------
-- ORDER O3: EXPLANATION
-- -----------------------------------------------------------------------------
INSERT INTO l2_1_order_definitions (
    order_id,
    order_name,
    meaning,
    depth,
    expandable,
    mutable,
    authority,
    is_terminal,
    required_fields,
    optional_fields,
    navigates_to,
    hard_prohibitions,
    validation_rules,
    is_frozen
) VALUES (
    'O3',
    'Explanation',
    'Detail / Explanation - Explain this thing',
    'single',
    true,  -- Can expand to O4 or O5
    false,
    'NONE',
    false,
    '[
        {"field": "id", "type": "string", "description": "Instance identifier"},
        {"field": "label", "type": "string", "description": "Human-readable name"},
        {"field": "status", "type": "enum", "description": "Current status"},
        {"field": "created_at", "type": "iso8601", "description": "Creation timestamp"},
        {"field": "updated_at", "type": "iso8601", "description": "Last update timestamp"},
        {"field": "summary", "type": "string", "description": "Brief explanation"}
    ]'::jsonb,
    '[
        {"field": "details", "type": "object", "description": "Domain-specific detail fields"},
        {"field": "metadata", "type": "object", "description": "Additional metadata"},
        {"field": "related_count", "type": "integer", "description": "Count of related items (teaser for O4)"}
    ]'::jsonb,
    '["O4", "O5"]'::jsonb,
    '[
        "No inline lists (use counts, navigate to O4)",
        "No mutation actions",
        "No cross-instance comparison",
        "No speculative content"
    ]'::jsonb,
    '{"single_instance_only": true}'::jsonb,
    true
);

-- -----------------------------------------------------------------------------
-- ORDER O4: CONTEXT
-- -----------------------------------------------------------------------------
INSERT INTO l2_1_order_definitions (
    order_id,
    order_name,
    meaning,
    depth,
    expandable,
    mutable,
    authority,
    is_terminal,
    required_fields,
    optional_fields,
    navigates_to,
    hard_prohibitions,
    validation_rules,
    is_frozen
) VALUES (
    'O4',
    'Context',
    'Context / Impact - What else did this affect?',
    'relational',
    true,  -- Can expand to O5
    false,
    'NONE',
    false,
    '[
        {"field": "source_id", "type": "string", "description": "The instance being contextualized"},
        {"field": "source_label", "type": "string", "description": "Human-readable source name"},
        {"field": "relationships", "type": "array", "description": "List of related entities"}
    ]'::jsonb,
    '[
        {"field": "impact_summary", "type": "string", "description": "Brief impact statement"},
        {"field": "timeline", "type": "array", "description": "Chronological events"},
        {"field": "dependency_graph", "type": "object", "description": "Structured dependency info"}
    ]'::jsonb,
    '["O5"]'::jsonb,
    '[
        "No cross-tenant relationships",
        "No speculative relationships",
        "No inferred causation",
        "No recursive context expansion"
    ]'::jsonb,
    '{"max_relationships": 50, "bounded_context": true}'::jsonb,
    true
);

-- -----------------------------------------------------------------------------
-- ORDER O5: PROOF (TERMINAL)
-- -----------------------------------------------------------------------------
INSERT INTO l2_1_order_definitions (
    order_id,
    order_name,
    meaning,
    depth,
    expandable,
    mutable,
    authority,
    is_terminal,
    required_fields,
    optional_fields,
    navigates_to,
    hard_prohibitions,
    validation_rules,
    is_frozen
) VALUES (
    'O5',
    'Proof',
    'Raw records / Proof - Show me proof (TERMINAL)',
    'terminal',
    false,  -- O5 is terminal, no expansion
    false,
    'NONE',
    true,   -- TERMINAL ORDER
    '[
        {"field": "proof_id", "type": "string", "description": "Unique proof identifier"},
        {"field": "source_id", "type": "string", "description": "What this proves"},
        {"field": "proof_type", "type": "enum", "values": ["trace", "audit_log", "snapshot", "hash", "signature"], "description": "Type of proof"},
        {"field": "timestamp", "type": "iso8601", "description": "When proof was recorded"},
        {"field": "content", "type": "object", "description": "Raw proof content"},
        {"field": "integrity_hash", "type": "string", "description": "Hash for verification"}
    ]'::jsonb,
    '[
        {"field": "chain_ref", "type": "string", "description": "Reference to proof chain"},
        {"field": "verification_status", "type": "enum", "values": ["verified", "unverified", "failed"]}
    ]'::jsonb,
    '[]'::jsonb,  -- No navigation from O5
    '[
        "NO modification after creation (ABSOLUTE)",
        "NO interpretation or summarization",
        "NO expansion beyond raw content",
        "NO cross-reference that mutates",
        "NO navigation deeper than O5"
    ]'::jsonb,
    '{"immutable": true, "replay_faithful": true}'::jsonb,
    true
);

-- -----------------------------------------------------------------------------
-- ORDER TRANSITIONS
-- -----------------------------------------------------------------------------

-- Valid transitions
INSERT INTO l2_1_order_transitions (from_order, to_order, is_valid, invalid_reason) VALUES
    ('O1', 'O2', true, NULL),
    ('O2', 'O3', true, NULL),
    ('O3', 'O4', true, NULL),
    ('O3', 'O5', true, NULL),
    ('O4', 'O5', true, NULL);

-- Invalid transitions (explicit documentation)
INSERT INTO l2_1_order_transitions (from_order, to_order, is_valid, invalid_reason) VALUES
    ('O1', 'O3', false, 'Must go through O2'),
    ('O1', 'O4', false, 'Must go through O2, O3'),
    ('O1', 'O5', false, 'Must go through intermediate orders'),
    ('O2', 'O4', false, 'Must go through O3'),
    ('O2', 'O5', false, 'Must go through O3'),
    ('O5', 'O1', false, 'O5 is terminal'),
    ('O5', 'O2', false, 'O5 is terminal'),
    ('O5', 'O3', false, 'O5 is terminal'),
    ('O5', 'O4', false, 'O5 is terminal');

-- =============================================================================
-- VERIFICATION QUERY
-- =============================================================================
-- Run this to verify seed data:
--
-- SELECT
--     o.order_id,
--     o.order_name,
--     o.depth,
--     o.is_terminal,
--     o.expandable,
--     array_agg(t.to_order) FILTER (WHERE t.is_valid = true) as valid_transitions
-- FROM l2_1_order_definitions o
-- LEFT JOIN l2_1_order_transitions t ON o.order_id = t.from_order
-- GROUP BY o.order_id, o.order_name, o.depth, o.is_terminal, o.expandable
-- ORDER BY o.order_id;
--
-- Expected: 5 orders (O1-O5), O5 is terminal with no valid transitions
-- =============================================================================
