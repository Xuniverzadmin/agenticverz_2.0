-- =============================================================================
-- L2.1 ACTION CAPABILITIES SEED DATA
-- =============================================================================
-- Purpose: Define all actions for all surfaces with proper layer routing.
-- Hard Rule: L2.1 = READ/DOWNLOAD only. WRITE/ACTIVATE = GC_L only.
--
-- Status: FROZEN (after initial population)
-- Created: 2026-01-07
-- =============================================================================

-- -----------------------------------------------------------------------------
-- OVERVIEW DOMAIN ACTIONS
-- -----------------------------------------------------------------------------

-- OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-OVERVIEW-STATUS-VIEW',
    'OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS',
    'read', 'View Status', 'View current system health status',
    'L2_1', 'none', NULL, 1
);

-- OVERVIEW.SYSTEM_HEALTH.HEALTH_METRICS
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-OVERVIEW-METRICS-VIEW',
    'OVERVIEW.SYSTEM_HEALTH.HEALTH_METRICS',
    'read', 'View Metrics', 'View current health metrics',
    'L2_1', 'none', NULL, 1
),
(
    'ACT-OVERVIEW-METRICS-DOWNLOAD',
    'OVERVIEW.SYSTEM_HEALTH.HEALTH_METRICS',
    'download', 'Download Metrics', 'Export health metrics as CSV/JSON',
    'L2_1', 'none', NULL, 2
);

-- -----------------------------------------------------------------------------
-- ACTIVITY DOMAIN ACTIONS
-- -----------------------------------------------------------------------------

-- ACTIVITY.EXECUTIONS.ACTIVE_RUNS
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-ACTIVITY-ACTIVE-VIEW',
    'ACTIVITY.EXECUTIONS.ACTIVE_RUNS',
    'read', 'View Active Runs', 'View list of currently running executions',
    'L2_1', 'none', NULL, 1
);

-- ACTIVITY.EXECUTIONS.COMPLETED_RUNS
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-ACTIVITY-COMPLETED-VIEW',
    'ACTIVITY.EXECUTIONS.COMPLETED_RUNS',
    'read', 'View Completed Runs', 'View list of completed executions',
    'L2_1', 'none', NULL, 1
),
(
    'ACT-ACTIVITY-COMPLETED-DOWNLOAD',
    'ACTIVITY.EXECUTIONS.COMPLETED_RUNS',
    'download', 'Download Run History', 'Export completed runs as CSV/JSON',
    'L2_1', 'none', NULL, 2
);

-- ACTIVITY.EXECUTIONS.RUN_DETAILS
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-ACTIVITY-DETAIL-VIEW',
    'ACTIVITY.EXECUTIONS.RUN_DETAILS',
    'read', 'View Run Details', 'View full execution detail',
    'L2_1', 'none', NULL, 1
),
(
    'ACT-ACTIVITY-DETAIL-DOWNLOAD',
    'ACTIVITY.EXECUTIONS.RUN_DETAILS',
    'download', 'Download Run Detail', 'Export run details with proof',
    'L2_1', 'none', NULL, 2
);

-- -----------------------------------------------------------------------------
-- INCIDENTS DOMAIN ACTIONS
-- This is where WRITE/ACTIVATE actions appear (GC_L routed)
-- -----------------------------------------------------------------------------

-- INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-INCIDENT-LIST-VIEW',
    'INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS',
    'read', 'View Open Incidents', 'View list of open incidents',
    'L2_1', 'none', NULL, 1
),
(
    'ACT-INCIDENT-LIST-DOWNLOAD',
    'INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS',
    'download', 'Download Incident List', 'Export open incidents as CSV',
    'L2_1', 'none', NULL, 2
);

-- INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-INCIDENT-DETAIL-VIEW',
    'INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS',
    'read', 'View Incident', 'View incident detail with context',
    'L2_1', 'none', NULL, 1
),
(
    'ACT-INCIDENT-DETAIL-DOWNLOAD',
    'INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS',
    'download', 'Download Incident', 'Export incident detail with evidence',
    'L2_1', 'none', NULL, 2
),
-- GC_L ACTIONS: These require human confirmation
(
    'ACT-INCIDENT-ACKNOWLEDGE',
    'INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS',
    'write', 'Acknowledge Incident', 'Mark incident as acknowledged',
    'GC_L', 'single_click', 'Acknowledge this incident? This action will be recorded.', 3
),
(
    'ACT-INCIDENT-RESOLVE',
    'INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS',
    'write', 'Resolve Incident', 'Mark incident as resolved',
    'GC_L', 'double_confirm', 'Resolve this incident? This will close the incident and require resolution notes.', 4
),
(
    'ACT-INCIDENT-ESCALATE',
    'INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS',
    'write', 'Escalate Incident', 'Escalate to higher priority',
    'GC_L', 'single_click', 'Escalate this incident? This will notify the on-call team.', 5
);

-- INCIDENTS.HISTORICAL_INCIDENTS.RESOLVED_INCIDENTS
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-INCIDENT-HISTORY-VIEW',
    'INCIDENTS.HISTORICAL_INCIDENTS.RESOLVED_INCIDENTS',
    'read', 'View History', 'View resolved incident history',
    'L2_1', 'none', NULL, 1
),
(
    'ACT-INCIDENT-HISTORY-DOWNLOAD',
    'INCIDENTS.HISTORICAL_INCIDENTS.RESOLVED_INCIDENTS',
    'download', 'Download History', 'Export incident history with proof',
    'L2_1', 'none', NULL, 2
);

-- -----------------------------------------------------------------------------
-- POLICIES DOMAIN ACTIONS
-- Heavy GC_L usage here (policy mutations)
-- -----------------------------------------------------------------------------

-- POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-POLICY-BUDGET-VIEW',
    'POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES',
    'read', 'View Budget Policies', 'View active budget policies',
    'L2_1', 'none', NULL, 1
),
(
    'ACT-POLICY-BUDGET-DOWNLOAD',
    'POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES',
    'download', 'Download Policies', 'Export budget policies as JSON',
    'L2_1', 'none', NULL, 2
),
-- GC_L ACTIONS
(
    'ACT-POLICY-BUDGET-CREATE',
    'POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES',
    'write', 'Create Budget Policy', 'Create a new budget policy',
    'GC_L', 'double_confirm', 'Create this budget policy? This will immediately affect resource allocation.', 3
),
(
    'ACT-POLICY-BUDGET-UPDATE',
    'POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES',
    'write', 'Update Budget Policy', 'Modify an existing budget policy',
    'GC_L', 'double_confirm', 'Update this budget policy? Changes will apply to all affected resources.', 4
),
(
    'ACT-POLICY-BUDGET-ACTIVATE',
    'POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES',
    'activate', 'Activate Budget Policy', 'Enable a budget policy',
    'GC_L', 'double_confirm', 'Activate this budget policy? All matching runs will be subject to this policy.', 5
),
(
    'ACT-POLICY-BUDGET-DEACTIVATE',
    'POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES',
    'activate', 'Deactivate Budget Policy', 'Disable a budget policy',
    'GC_L', 'double_confirm', 'Deactivate this budget policy? Runs will no longer be constrained by this policy.', 6
);

-- POLICIES.ACTIVE_POLICIES.RATE_LIMITS
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-POLICY-RATE-VIEW',
    'POLICIES.ACTIVE_POLICIES.RATE_LIMITS',
    'read', 'View Rate Limits', 'View active rate limit policies',
    'L2_1', 'none', NULL, 1
),
(
    'ACT-POLICY-RATE-DOWNLOAD',
    'POLICIES.ACTIVE_POLICIES.RATE_LIMITS',
    'download', 'Download Rate Limits', 'Export rate limits as JSON',
    'L2_1', 'none', NULL, 2
),
-- GC_L ACTIONS
(
    'ACT-POLICY-RATE-UPDATE',
    'POLICIES.ACTIVE_POLICIES.RATE_LIMITS',
    'write', 'Update Rate Limit', 'Modify rate limit configuration',
    'GC_L', 'double_confirm', 'Update this rate limit? Changes affect API throughput immediately.', 3
),
(
    'ACT-POLICY-RATE-ACTIVATE',
    'POLICIES.ACTIVE_POLICIES.RATE_LIMITS',
    'activate', 'Activate Rate Limit', 'Enable a rate limit',
    'GC_L', 'single_click', 'Activate this rate limit?', 4
);

-- POLICIES.ACTIVE_POLICIES.APPROVAL_RULES
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-POLICY-APPROVAL-VIEW',
    'POLICIES.ACTIVE_POLICIES.APPROVAL_RULES',
    'read', 'View Approval Rules', 'View active approval rules',
    'L2_1', 'none', NULL, 1
),
(
    'ACT-POLICY-APPROVAL-DOWNLOAD',
    'POLICIES.ACTIVE_POLICIES.APPROVAL_RULES',
    'download', 'Download Approval Rules', 'Export approval rules',
    'L2_1', 'none', NULL, 2
),
-- GC_L ACTIONS
(
    'ACT-POLICY-APPROVAL-CREATE',
    'POLICIES.ACTIVE_POLICIES.APPROVAL_RULES',
    'write', 'Create Approval Rule', 'Create a new approval requirement',
    'GC_L', 'human_approval_required', 'Create approval rule. This requires admin approval before activation.', 3
),
(
    'ACT-POLICY-APPROVAL-ACTIVATE',
    'POLICIES.ACTIVE_POLICIES.APPROVAL_RULES',
    'activate', 'Activate Approval Rule', 'Enable an approval rule',
    'GC_L', 'human_approval_required', 'Activate this approval rule. All matching operations will require approval.', 4
);

-- POLICIES.POLICY_AUDIT.POLICY_CHANGES
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-POLICY-AUDIT-VIEW',
    'POLICIES.POLICY_AUDIT.POLICY_CHANGES',
    'read', 'View Policy Changes', 'View policy change audit trail',
    'L2_1', 'none', NULL, 1
),
(
    'ACT-POLICY-AUDIT-DOWNLOAD',
    'POLICIES.POLICY_AUDIT.POLICY_CHANGES',
    'download', 'Download Audit Trail', 'Export policy audit trail with proof',
    'L2_1', 'none', NULL, 2
);

-- -----------------------------------------------------------------------------
-- LOGS DOMAIN ACTIONS
-- Mostly READ/DOWNLOAD (proof surfaces)
-- -----------------------------------------------------------------------------

-- LOGS.AUDIT_LOGS.SYSTEM_AUDIT
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-LOGS-SYSTEM-VIEW',
    'LOGS.AUDIT_LOGS.SYSTEM_AUDIT',
    'read', 'View System Audit', 'View system audit logs',
    'L2_1', 'none', NULL, 1
),
(
    'ACT-LOGS-SYSTEM-DOWNLOAD',
    'LOGS.AUDIT_LOGS.SYSTEM_AUDIT',
    'download', 'Download System Audit', 'Export system audit with cryptographic proof',
    'L2_1', 'none', NULL, 2
);

-- LOGS.AUDIT_LOGS.USER_AUDIT
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-LOGS-USER-VIEW',
    'LOGS.AUDIT_LOGS.USER_AUDIT',
    'read', 'View User Audit', 'View user action audit logs',
    'L2_1', 'none', NULL, 1
),
(
    'ACT-LOGS-USER-DOWNLOAD',
    'LOGS.AUDIT_LOGS.USER_AUDIT',
    'download', 'Download User Audit', 'Export user audit with proof',
    'L2_1', 'none', NULL, 2
);

-- LOGS.EXECUTION_TRACES.TRACE_DETAILS
INSERT INTO l2_1_action_capabilities (
    capability_id, surface_id, action_type, action_name, action_description,
    layer_route, confirmation_type, confirmation_message, display_order
) VALUES
(
    'ACT-LOGS-TRACE-VIEW',
    'LOGS.EXECUTION_TRACES.TRACE_DETAILS',
    'read', 'View Trace', 'View execution trace detail',
    'L2_1', 'none', NULL, 1
),
(
    'ACT-LOGS-TRACE-DOWNLOAD',
    'LOGS.EXECUTION_TRACES.TRACE_DETAILS',
    'download', 'Download Trace', 'Export trace with full proof chain',
    'L2_1', 'none', NULL, 2
);

-- -----------------------------------------------------------------------------
-- VERIFICATION QUERIES
-- -----------------------------------------------------------------------------

-- Count actions by type and layer
SELECT
    action_type,
    layer_route,
    COUNT(*) as action_count
FROM l2_1_action_capabilities
GROUP BY action_type, layer_route
ORDER BY layer_route, action_type;

-- Expected output:
-- | action_type | layer_route | action_count |
-- |-------------|-------------|--------------|
-- | download    | L2_1        | 14           |
-- | read        | L2_1        | 15           |
-- | activate    | GC_L        | 4            |
-- | write       | GC_L        | 7            |

-- Verify no L2_1 WRITE/ACTIVATE violations
SELECT
    capability_id,
    surface_id,
    action_type,
    layer_route
FROM l2_1_action_capabilities
WHERE layer_route = 'L2_1' AND action_type IN ('write', 'activate');
-- Expected: 0 rows

-- Verify all GC_L actions have confirmation
SELECT
    capability_id,
    surface_id,
    action_type,
    confirmation_type
FROM l2_1_action_capabilities
WHERE layer_route = 'GC_L' AND confirmation_type = 'none';
-- Expected: 0 rows

