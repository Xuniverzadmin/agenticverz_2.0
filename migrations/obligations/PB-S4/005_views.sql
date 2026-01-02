-- PB-S4: Views
-- Convenience views for policy operations

-- View: Active policies with their current version
CREATE OR REPLACE VIEW pb_s4.active_policies AS
SELECT
    p.id AS policy_id,
    p.name AS policy_name,
    p.policy_type,
    p.scope,
    pv.version AS current_version,
    pv.definition,
    pv.activated_at,
    pv.activated_by
FROM pb_s4.policy p
JOIN pb_s4.policy_version pv ON p.id = pv.policy_id
WHERE pv.is_active = true
ORDER BY p.name;

COMMENT ON VIEW pb_s4.active_policies IS
    'All policies with their currently active version';

-- View: Policy version history
CREATE OR REPLACE VIEW pb_s4.policy_history AS
SELECT
    p.id AS policy_id,
    p.name AS policy_name,
    pv.version,
    pv.is_active,
    pv.created_by,
    pv.created_at,
    pv.activated_at,
    pv.activated_by,
    pv.definition
FROM pb_s4.policy p
JOIN pb_s4.policy_version pv ON p.id = pv.policy_id
ORDER BY p.name, pv.version DESC;

COMMENT ON VIEW pb_s4.policy_history IS
    'Full version history for all policies';

-- View: Policies without active version
CREATE OR REPLACE VIEW pb_s4.inactive_policies AS
SELECT
    p.id AS policy_id,
    p.name AS policy_name,
    p.policy_type,
    p.scope,
    COUNT(pv.id) AS total_versions,
    MAX(pv.version) AS latest_version
FROM pb_s4.policy p
LEFT JOIN pb_s4.policy_version pv ON p.id = pv.policy_id
GROUP BY p.id, p.name, p.policy_type, p.scope
HAVING NOT EXISTS (
    SELECT 1 FROM pb_s4.policy_version pv2
    WHERE pv2.policy_id = p.id AND pv2.is_active = true
);

COMMENT ON VIEW pb_s4.inactive_policies IS
    'Policies that have no active version';
