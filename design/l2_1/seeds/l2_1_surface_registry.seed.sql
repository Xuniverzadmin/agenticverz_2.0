-- =============================================================================
-- L2.1 SURFACE REGISTRY SEED DATA
-- =============================================================================
-- Purpose: Populate the L2 Constitution with all 15 surfaces.
-- Aligned with L1 Constitution: 5 domains, 8 subdomains, 15 topics.
--
-- Status: FROZEN (after initial population)
-- Created: 2026-01-07
-- =============================================================================

-- -----------------------------------------------------------------------------
-- OVERVIEW DOMAIN (2 surfaces)
-- Question: "Is the system okay right now?"
-- -----------------------------------------------------------------------------

INSERT INTO l2_1_surface_registry (
    surface_id, domain, subdomain, topic, topic_order,
    o1_enabled, o2_enabled, o3_enabled, o4_enabled, o5_enabled,
    requires_interpreter, requires_ir_hash,
    replay_supported, status, notes
) VALUES
(
    'OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS',
    'Overview', 'SYSTEM_HEALTH', 'CURRENT_STATUS', 1,
    true, false, false, false, false,  -- O1 only (snapshot)
    false, false,                       -- No interpreter needed for O1
    true, 'validated',
    'Primary health indicator. Shows system status at a glance.'
),
(
    'OVERVIEW.SYSTEM_HEALTH.HEALTH_METRICS',
    'Overview', 'SYSTEM_HEALTH', 'HEALTH_METRICS', 2,
    true, true, false, false, false,   -- O1 + O2 (snapshot + list)
    false, false,                       -- No interpreter needed
    true, 'validated',
    'Key health metrics. Uptime, error rates, throughput.'
);

-- -----------------------------------------------------------------------------
-- ACTIVITY DOMAIN (3 surfaces)
-- Question: "What ran / is running?"
-- -----------------------------------------------------------------------------

INSERT INTO l2_1_surface_registry (
    surface_id, domain, subdomain, topic, topic_order,
    o1_enabled, o2_enabled, o3_enabled, o4_enabled, o5_enabled,
    requires_interpreter, requires_ir_hash,
    replay_supported, status, notes
) VALUES
(
    'ACTIVITY.EXECUTIONS.ACTIVE_RUNS',
    'Activity', 'EXECUTIONS', 'ACTIVE_RUNS', 1,
    true, true, false, false, false,   -- O1 + O2 (snapshot + list)
    false, false,                       -- No interpreter needed
    true, 'validated',
    'Currently running executions. Real-time list.'
),
(
    'ACTIVITY.EXECUTIONS.COMPLETED_RUNS',
    'Activity', 'EXECUTIONS', 'COMPLETED_RUNS', 2,
    true, true, true, false, false,    -- O1 + O2 + O3 (with detail)
    true, true,                         -- Interpreter needed for O3
    true, 'validated',
    'Completed executions with detail view.'
),
(
    'ACTIVITY.EXECUTIONS.RUN_DETAILS',
    'Activity', 'EXECUTIONS', 'RUN_DETAILS', 3,
    true, true, true, true, true,      -- Full depth O1-O5
    true, true,                         -- Interpreter needed
    true, 'validated',
    'Full execution detail with proof (O5 terminal).'
);

-- -----------------------------------------------------------------------------
-- INCIDENTS DOMAIN (3 surfaces)
-- Question: "What went wrong?"
-- -----------------------------------------------------------------------------

INSERT INTO l2_1_surface_registry (
    surface_id, domain, subdomain, topic, topic_order,
    o1_enabled, o2_enabled, o3_enabled, o4_enabled, o5_enabled,
    requires_interpreter, requires_ir_hash,
    replay_supported, status, notes
) VALUES
(
    'INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS',
    'Incidents', 'ACTIVE_INCIDENTS', 'OPEN_INCIDENTS', 1,
    true, true, false, false, false,   -- O1 + O2 (snapshot + list)
    false, false,                       -- No interpreter needed
    true, 'validated',
    'Currently open incidents requiring attention.'
),
(
    'INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS',
    'Incidents', 'ACTIVE_INCIDENTS', 'INCIDENT_DETAILS', 2,
    true, true, true, true, false,     -- O1-O4 (with context)
    true, true,                         -- Interpreter needed for O3+
    true, 'validated',
    'Incident detail with context and impact.'
),
(
    'INCIDENTS.HISTORICAL_INCIDENTS.RESOLVED_INCIDENTS',
    'Incidents', 'HISTORICAL_INCIDENTS', 'RESOLVED_INCIDENTS', 3,
    true, true, true, true, true,      -- Full depth O1-O5
    true, true,                         -- Interpreter needed
    true, 'validated',
    'Historical incidents with full proof chain.'
);

-- -----------------------------------------------------------------------------
-- POLICIES DOMAIN (4 surfaces)
-- Question: "How is behavior defined?"
-- -----------------------------------------------------------------------------

INSERT INTO l2_1_surface_registry (
    surface_id, domain, subdomain, topic, topic_order,
    o1_enabled, o2_enabled, o3_enabled, o4_enabled, o5_enabled,
    requires_interpreter, requires_ir_hash,
    replay_supported, status, notes
) VALUES
(
    'POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES',
    'Policies', 'ACTIVE_POLICIES', 'BUDGET_POLICIES', 1,
    true, true, true, false, false,    -- O1-O3 (with explanation)
    true, true,                         -- Interpreter needed for O3
    true, 'validated',
    'Active budget policies with rule explanation.'
),
(
    'POLICIES.ACTIVE_POLICIES.RATE_LIMITS',
    'Policies', 'ACTIVE_POLICIES', 'RATE_LIMITS', 2,
    true, true, true, false, false,    -- O1-O3 (with explanation)
    true, true,                         -- Interpreter needed for O3
    true, 'validated',
    'Active rate limits with configuration detail.'
),
(
    'POLICIES.ACTIVE_POLICIES.APPROVAL_RULES',
    'Policies', 'ACTIVE_POLICIES', 'APPROVAL_RULES', 3,
    true, true, true, true, false,     -- O1-O4 (with context)
    true, true,                         -- Interpreter needed
    true, 'validated',
    'Approval rules with impact context.'
),
(
    'POLICIES.POLICY_AUDIT.POLICY_CHANGES',
    'Policies', 'POLICY_AUDIT', 'POLICY_CHANGES', 4,
    true, true, true, true, true,      -- Full depth O1-O5
    true, true,                         -- Interpreter needed
    true, 'validated',
    'Policy change audit trail with proof.'
);

-- -----------------------------------------------------------------------------
-- LOGS DOMAIN (3 surfaces)
-- Question: "What is the raw truth?"
-- -----------------------------------------------------------------------------

INSERT INTO l2_1_surface_registry (
    surface_id, domain, subdomain, topic, topic_order,
    o1_enabled, o2_enabled, o3_enabled, o4_enabled, o5_enabled,
    requires_interpreter, requires_ir_hash,
    replay_supported, status, notes
) VALUES
(
    'LOGS.AUDIT_LOGS.SYSTEM_AUDIT',
    'Logs', 'AUDIT_LOGS', 'SYSTEM_AUDIT', 1,
    true, true, true, false, true,     -- O1, O2, O3, O5 (skip O4)
    true, true,                         -- Interpreter needed
    true, 'validated',
    'System audit logs with proof (O5 terminal).'
),
(
    'LOGS.AUDIT_LOGS.USER_AUDIT',
    'Logs', 'AUDIT_LOGS', 'USER_AUDIT', 2,
    true, true, true, false, true,     -- O1, O2, O3, O5 (skip O4)
    true, true,                         -- Interpreter needed
    true, 'validated',
    'User action audit logs with proof.'
),
(
    'LOGS.EXECUTION_TRACES.TRACE_DETAILS',
    'Logs', 'EXECUTION_TRACES', 'TRACE_DETAILS', 3,
    true, true, true, true, true,      -- Full depth O1-O5
    true, true,                         -- Interpreter needed
    true, 'validated',
    'Execution trace detail with full proof chain.'
);

-- -----------------------------------------------------------------------------
-- VERIFICATION QUERY
-- -----------------------------------------------------------------------------

-- Verify surface count per domain
SELECT
    domain,
    COUNT(*) as surface_count,
    SUM(CASE WHEN o5_enabled THEN 1 ELSE 0 END) as o5_surfaces
FROM l2_1_surface_registry
GROUP BY domain
ORDER BY domain;

-- Expected output:
-- | domain    | surface_count | o5_surfaces |
-- |-----------|---------------|-------------|
-- | Activity  | 3             | 1           |
-- | Incidents | 3             | 1           |
-- | Logs      | 3             | 3           |
-- | Overview  | 2             | 0           |
-- | Policies  | 4             | 1           |
-- | TOTAL     | 15            | 6           |

