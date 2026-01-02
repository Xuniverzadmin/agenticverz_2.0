-- M26: Tables
-- Cost events and snapshots

-- Raw cost events (truth source)
CREATE TABLE m26.cost_event (
    id BIGSERIAL PRIMARY KEY,

    -- Event identification
    source TEXT NOT NULL,  -- workflow_id, run_id, or system component
    source_type TEXT NOT NULL CHECK (source_type IN ('RUN', 'WORKFLOW', 'SYSTEM', 'ADJUSTMENT')),

    -- Cost data
    cost_units INTEGER NOT NULL CHECK (cost_units >= 0),
    cost_type TEXT NOT NULL CHECK (cost_type IN ('LLM_TOKENS', 'COMPUTE', 'STORAGE', 'NETWORK', 'OTHER')),

    -- Context
    tenant_id TEXT NOT NULL,
    metadata JSONB,

    -- Audit
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Daily cost snapshots (derived, for fast queries)
CREATE TABLE m26.cost_snapshot (
    snapshot_at DATE NOT NULL,
    tenant_id TEXT NOT NULL,
    cost_type TEXT NOT NULL,
    total_units INTEGER NOT NULL CHECK (total_units >= 0),
    event_count INTEGER NOT NULL CHECK (event_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (snapshot_at, tenant_id, cost_type)
);

-- Cost anomalies (detected deviations)
CREATE TABLE m26.cost_anomaly (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    anomaly_type TEXT NOT NULL CHECK (anomaly_type IN ('SPIKE', 'SUSTAINED_HIGH', 'BUDGET_WARNING', 'BUDGET_EXCEEDED')),
    severity TEXT NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),

    -- Deviation data
    expected_units INTEGER NOT NULL,
    actual_units INTEGER NOT NULL,
    deviation_pct NUMERIC(10,2) NOT NULL,

    -- Context
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    source_events BIGINT[] NOT NULL,  -- Array of cost_event IDs

    -- Resolution
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED', 'FALSE_POSITIVE')),
    resolved_at TIMESTAMPTZ,
    resolved_by TEXT,
    resolution_note TEXT,

    -- Audit
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for cost_event
CREATE INDEX idx_cost_event_source ON m26.cost_event(source, source_type);
CREATE INDEX idx_cost_event_tenant ON m26.cost_event(tenant_id, occurred_at DESC);
CREATE INDEX idx_cost_event_occurred ON m26.cost_event(occurred_at);

-- Indexes for cost_anomaly
CREATE INDEX idx_cost_anomaly_tenant ON m26.cost_anomaly(tenant_id, detected_at DESC);
CREATE INDEX idx_cost_anomaly_open ON m26.cost_anomaly(status, detected_at)
    WHERE status = 'OPEN';

COMMENT ON TABLE m26.cost_event IS
    'Raw cost events. Append-only truth source.';
COMMENT ON TABLE m26.cost_snapshot IS
    'Daily aggregated snapshots. Derived from cost_event.';
COMMENT ON TABLE m26.cost_anomaly IS
    'Detected cost anomalies requiring attention.';
COMMENT ON COLUMN m26.cost_event.cost_units IS
    'Cost in smallest units (e.g., tokens for LLM, bytes for storage)';
COMMENT ON COLUMN m26.cost_anomaly.source_events IS
    'Array of cost_event IDs that contributed to this anomaly';
