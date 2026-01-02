-- M26: Constraints
-- Semantic constraints for cost intelligence

-- Constraint: Unique cost event per source/time (prevent duplicates)
CREATE UNIQUE INDEX uq_cost_event_once
ON m26.cost_event(source, source_type, occurred_at);

-- Constraint: Anomaly must have source events
ALTER TABLE m26.cost_anomaly
ADD CONSTRAINT chk_anomaly_has_events CHECK (
    array_length(source_events, 1) > 0
);

-- Constraint: Resolved anomaly must have resolution info
ALTER TABLE m26.cost_anomaly
ADD CONSTRAINT chk_resolved_has_info CHECK (
    NOT (status IN ('RESOLVED', 'FALSE_POSITIVE') AND (resolved_at IS NULL OR resolved_by IS NULL))
);

-- Constraint: Open anomaly should not have resolution info
ALTER TABLE m26.cost_anomaly
ADD CONSTRAINT chk_open_no_resolution CHECK (
    NOT (status = 'OPEN' AND resolved_at IS NOT NULL)
);

-- Constraint: Window must be valid
ALTER TABLE m26.cost_anomaly
ADD CONSTRAINT chk_valid_window CHECK (
    window_end > window_start
);

COMMENT ON INDEX uq_cost_event_once IS
    'Prevent duplicate cost events for same source/time';
COMMENT ON CONSTRAINT chk_anomaly_has_events ON m26.cost_anomaly IS
    'Anomaly must reference at least one source event';
COMMENT ON CONSTRAINT chk_resolved_has_info ON m26.cost_anomaly IS
    'Resolved anomalies must have resolution info';
COMMENT ON CONSTRAINT chk_open_no_resolution ON m26.cost_anomaly IS
    'Open anomalies should not have resolution info';
COMMENT ON CONSTRAINT chk_valid_window ON m26.cost_anomaly IS
    'Window end must be after window start';
