-- M26: Views
-- Convenience views for cost intelligence

-- View: Daily cost by tenant
CREATE OR REPLACE VIEW m26.daily_cost_by_tenant AS
SELECT
    snapshot_at,
    tenant_id,
    SUM(total_units) AS total_units,
    SUM(event_count) AS event_count
FROM m26.cost_snapshot
GROUP BY snapshot_at, tenant_id
ORDER BY snapshot_at DESC, tenant_id;

COMMENT ON VIEW m26.daily_cost_by_tenant IS
    'Daily aggregated costs per tenant';

-- View: Cost by type
CREATE OR REPLACE VIEW m26.cost_by_type AS
SELECT
    cost_type,
    SUM(total_units) AS total_units,
    SUM(event_count) AS total_events,
    MIN(snapshot_at) AS first_day,
    MAX(snapshot_at) AS last_day
FROM m26.cost_snapshot
GROUP BY cost_type
ORDER BY total_units DESC;

COMMENT ON VIEW m26.cost_by_type IS
    'Total costs aggregated by cost type';

-- View: Open anomalies
CREATE OR REPLACE VIEW m26.open_anomalies AS
SELECT
    id,
    tenant_id,
    anomaly_type,
    severity,
    expected_units,
    actual_units,
    deviation_pct,
    window_start,
    window_end,
    array_length(source_events, 1) AS event_count,
    detected_at,
    EXTRACT(EPOCH FROM (now() - detected_at)) / 3600 AS hours_since_detection
FROM m26.cost_anomaly
WHERE status = 'OPEN'
ORDER BY
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
    END,
    detected_at DESC;

COMMENT ON VIEW m26.open_anomalies IS
    'Open cost anomalies ordered by severity';

-- View: Recent cost events (last 24h)
CREATE OR REPLACE VIEW m26.recent_events AS
SELECT
    id,
    source,
    source_type,
    cost_type,
    cost_units,
    tenant_id,
    occurred_at
FROM m26.cost_event
WHERE occurred_at > now() - INTERVAL '24 hours'
ORDER BY occurred_at DESC
LIMIT 1000;

COMMENT ON VIEW m26.recent_events IS
    'Cost events from the last 24 hours';

-- View: Anomaly summary
CREATE OR REPLACE VIEW m26.anomaly_summary AS
SELECT
    status,
    severity,
    COUNT(*) AS count,
    SUM(actual_units - expected_units) AS total_deviation_units
FROM m26.cost_anomaly
GROUP BY status, severity
ORDER BY status, severity;

COMMENT ON VIEW m26.anomaly_summary IS
    'Summary of anomalies by status and severity';
