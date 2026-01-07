-- =============================================================================
-- L2.1 DOMAIN REGISTRY SEED DATA
-- =============================================================================
-- Status: FROZEN
-- Created: 2026-01-07
-- Source: L1 Constitution (CUSTOMER_CONSOLE_V1_CONSTITUTION.md)
--
-- GOVERNANCE:
-- These five domains are FROZEN. No additions without L1 Constitution amendment.
-- Domains must match L1 Constitution exactly.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- DOMAIN: OVERVIEW
-- -----------------------------------------------------------------------------
INSERT INTO l2_1_domain_registry (
    domain_id,
    domain_name,
    core_question,
    status,
    l1_constitution_ref,
    l1_constitution_version,
    object_family,
    forbidden_content,
    is_frozen,
    requires_ratification,
    frozen_at,
    frozen_by
) VALUES (
    'overview',
    'Overview',
    'Is the system okay right now?',
    'frozen',
    'CUSTOMER_CONSOLE_V1_CONSTITUTION.md#3.1',
    '1.0.0',
    '["Status", "Health", "Pulse"]'::jsonb,
    '["Execution history", "Failure details", "Rule definitions"]'::jsonb,
    true,
    true,
    NOW(),
    'system'
);

INSERT INTO l2_1_subdomain_registry (domain_id, subdomain_id, subdomain_name, description, status)
VALUES ('overview', 'system_health', 'System Health', 'Overall system health indicators', 'active');

INSERT INTO l2_1_topic_registry (domain_id, subdomain_id, topic_id, topic_name, question, status)
VALUES
    ('overview', 'system_health', 'current_status', 'Current Status', 'What is the current system state?', 'active'),
    ('overview', 'system_health', 'health_metrics', 'Health Metrics', 'What are the key health indicators?', 'active');

-- -----------------------------------------------------------------------------
-- DOMAIN: ACTIVITY
-- -----------------------------------------------------------------------------
INSERT INTO l2_1_domain_registry (
    domain_id,
    domain_name,
    core_question,
    status,
    l1_constitution_ref,
    l1_constitution_version,
    object_family,
    forbidden_content,
    is_frozen,
    requires_ratification,
    frozen_at,
    frozen_by
) VALUES (
    'activity',
    'Activity',
    'What ran / is running?',
    'frozen',
    'CUSTOMER_CONSOLE_V1_CONSTITUTION.md#3.2',
    '1.0.0',
    '["Runs", "Traces", "Jobs"]'::jsonb,
    '["Failure classification", "Policy evaluation", "Raw audit"]'::jsonb,
    true,
    true,
    NOW(),
    'system'
);

INSERT INTO l2_1_subdomain_registry (domain_id, subdomain_id, subdomain_name, description, status)
VALUES ('activity', 'executions', 'Executions', 'Run execution tracking', 'active');

INSERT INTO l2_1_topic_registry (domain_id, subdomain_id, topic_id, topic_name, question, status)
VALUES
    ('activity', 'executions', 'active_runs', 'Active Runs', 'What is currently running?', 'active'),
    ('activity', 'executions', 'completed_runs', 'Completed Runs', 'What has finished recently?', 'active'),
    ('activity', 'executions', 'run_details', 'Run Details', 'What happened in this specific run?', 'active');

-- -----------------------------------------------------------------------------
-- DOMAIN: INCIDENTS
-- -----------------------------------------------------------------------------
INSERT INTO l2_1_domain_registry (
    domain_id,
    domain_name,
    core_question,
    status,
    l1_constitution_ref,
    l1_constitution_version,
    object_family,
    forbidden_content,
    is_frozen,
    requires_ratification,
    frozen_at,
    frozen_by
) VALUES (
    'incidents',
    'Incidents',
    'What went wrong?',
    'frozen',
    'CUSTOMER_CONSOLE_V1_CONSTITUTION.md#3.3',
    '1.0.0',
    '["Incidents", "Violations", "Failures"]'::jsonb,
    '["Execution traces", "Policy definitions", "Success metrics"]'::jsonb,
    true,
    true,
    NOW(),
    'system'
);

INSERT INTO l2_1_subdomain_registry (domain_id, subdomain_id, subdomain_name, description, status)
VALUES
    ('incidents', 'active_incidents', 'Active Incidents', 'Currently open incidents', 'active'),
    ('incidents', 'historical_incidents', 'Historical Incidents', 'Resolved incidents', 'active');

INSERT INTO l2_1_topic_registry (domain_id, subdomain_id, topic_id, topic_name, question, status)
VALUES
    ('incidents', 'active_incidents', 'open_incidents', 'Open Incidents', 'What incidents need attention?', 'active'),
    ('incidents', 'active_incidents', 'incident_details', 'Incident Details', 'What is the full context of this incident?', 'active'),
    ('incidents', 'historical_incidents', 'resolved_incidents', 'Resolved Incidents', 'What incidents were resolved?', 'active');

-- -----------------------------------------------------------------------------
-- DOMAIN: POLICIES
-- -----------------------------------------------------------------------------
INSERT INTO l2_1_domain_registry (
    domain_id,
    domain_name,
    core_question,
    status,
    l1_constitution_ref,
    l1_constitution_version,
    object_family,
    forbidden_content,
    is_frozen,
    requires_ratification,
    frozen_at,
    frozen_by
) VALUES (
    'policies',
    'Policies',
    'How is behavior defined?',
    'frozen',
    'CUSTOMER_CONSOLE_V1_CONSTITUTION.md#3.4',
    '1.0.0',
    '["Rules", "Limits", "Constraints", "Approvals"]'::jsonb,
    '["Policy violations", "Execution under policy", "Raw policy logs"]'::jsonb,
    true,
    true,
    NOW(),
    'system'
);

INSERT INTO l2_1_subdomain_registry (domain_id, subdomain_id, subdomain_name, description, status)
VALUES
    ('policies', 'active_policies', 'Active Policies', 'Currently enforced policies', 'active'),
    ('policies', 'policy_audit', 'Policy Audit', 'Policy change history', 'active');

INSERT INTO l2_1_topic_registry (domain_id, subdomain_id, topic_id, topic_name, question, status)
VALUES
    ('policies', 'active_policies', 'budget_policies', 'Budget Policies', 'What budget constraints are in effect?', 'active'),
    ('policies', 'active_policies', 'rate_limits', 'Rate Limits', 'What rate limits are configured?', 'active'),
    ('policies', 'active_policies', 'approval_rules', 'Approval Rules', 'What requires approval?', 'active'),
    ('policies', 'policy_audit', 'policy_changes', 'Policy Changes', 'What policies have changed?', 'active');

-- -----------------------------------------------------------------------------
-- DOMAIN: LOGS
-- -----------------------------------------------------------------------------
INSERT INTO l2_1_domain_registry (
    domain_id,
    domain_name,
    core_question,
    status,
    l1_constitution_ref,
    l1_constitution_version,
    object_family,
    forbidden_content,
    is_frozen,
    requires_ratification,
    frozen_at,
    frozen_by
) VALUES (
    'logs',
    'Logs',
    'What is the raw truth?',
    'frozen',
    'CUSTOMER_CONSOLE_V1_CONSTITUTION.md#3.5',
    '1.0.0',
    '["Traces", "Audit", "Proof"]'::jsonb,
    '["Interpreted summaries", "Failure analysis", "Policy evaluation"]'::jsonb,
    true,
    true,
    NOW(),
    'system'
);

INSERT INTO l2_1_subdomain_registry (domain_id, subdomain_id, subdomain_name, description, status)
VALUES
    ('logs', 'audit_logs', 'Audit Logs', 'System and user audit trails', 'active'),
    ('logs', 'execution_traces', 'Execution Traces', 'Raw execution trace data', 'active');

INSERT INTO l2_1_topic_registry (domain_id, subdomain_id, topic_id, topic_name, question, status)
VALUES
    ('logs', 'audit_logs', 'system_audit', 'System Audit', 'What system-level events occurred?', 'active'),
    ('logs', 'audit_logs', 'user_audit', 'User Audit', 'What user actions were recorded?', 'active'),
    ('logs', 'execution_traces', 'trace_details', 'Trace Details', 'What is the full execution trace?', 'active');

-- =============================================================================
-- VERIFICATION QUERY
-- =============================================================================
-- Run this to verify seed data:
--
-- SELECT
--     d.domain_id,
--     d.domain_name,
--     d.core_question,
--     d.status,
--     COUNT(DISTINCT s.subdomain_id) as subdomain_count,
--     COUNT(DISTINCT t.topic_id) as topic_count
-- FROM l2_1_domain_registry d
-- LEFT JOIN l2_1_subdomain_registry s ON d.domain_id = s.domain_id
-- LEFT JOIN l2_1_topic_registry t ON s.domain_id = t.domain_id AND s.subdomain_id = t.subdomain_id
-- GROUP BY d.domain_id, d.domain_name, d.core_question, d.status
-- ORDER BY d.domain_id;
--
-- Expected: 5 domains, 8 subdomains, 15 topics
-- =============================================================================
