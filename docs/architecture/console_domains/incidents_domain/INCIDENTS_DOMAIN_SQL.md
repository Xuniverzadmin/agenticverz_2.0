# Incidents Domain SQL

**Status:** AUTHORITATIVE
**Effective:** 2026-01-17
**Scope:** All Incidents domain endpoints
**Reference:** Incidents Domain Canonical System Design

---

## 0. Source Tables (L6)

### incidents (IMMUTABLE CORE)

```sql
-- Existing columns used by Incidents domain
id                  UUID PRIMARY KEY
tenant_id           UUID NOT NULL
created_at          TIMESTAMPTZ NOT NULL
severity            VARCHAR(20) NOT NULL  -- low, medium, high, critical
status              VARCHAR(20) NOT NULL  -- active, resolved
category            VARCHAR(50)           -- policy, runtime, infra, cost, security
source_run_id       UUID                  -- FK to runs (cross-domain link)
is_synthetic        BOOLEAN DEFAULT FALSE
synthetic_scenario_id VARCHAR(100)

-- NEW columns (Phase 1)
resolution_method   VARCHAR(20)           -- auto, manual, rollback, null if unresolved
cost_impact         DECIMAL(12,2)         -- USD impact, null if unknown
resolved_at         TIMESTAMPTZ           -- when status changed to resolved
resolved_by         VARCHAR(100)          -- system, user_id, automation_id
```

### incident_evidence (APPEND-ONLY)

```sql
id                  UUID PRIMARY KEY
incident_id         UUID NOT NULL REFERENCES incidents(id)
evidence_type       VARCHAR(30) NOT NULL  -- log, trace, metric, action
recovery_executed   BOOLEAN DEFAULT FALSE -- NEW: was recovery attempted
payload             JSONB
created_at          TIMESTAMPTZ NOT NULL
```

### incident_events (APPEND-ONLY TIMELINE)

```sql
id                  UUID PRIMARY KEY
incident_id         UUID NOT NULL REFERENCES incidents(id)
event_type          VARCHAR(30) NOT NULL  -- detected, escalated, mitigated, resolved
actor               VARCHAR(30) NOT NULL  -- system, user, automation
metadata            JSONB
created_at          TIMESTAMPTZ NOT NULL
```

---

## 1. v_incidents_o2 View (L5)

### Definition

```sql
CREATE OR REPLACE VIEW v_incidents_o2 AS
SELECT
    i.id AS incident_id,
    i.tenant_id,
    i.severity,
    i.status,
    i.category,
    i.source_run_id,
    i.resolution_method,
    i.cost_impact,
    i.resolved_at,
    i.resolved_by,
    i.is_synthetic,
    i.created_at AS first_seen_at,

    -- Last event timestamp
    COALESCE(
        (SELECT MAX(created_at) FROM incident_events WHERE incident_id = i.id),
        i.created_at
    ) AS last_seen_at,

    -- Evidence count
    (SELECT COUNT(*) FROM incident_evidence WHERE incident_id = i.id) AS evidence_count,

    -- Recovery executed flag (any evidence with recovery)
    EXISTS(
        SELECT 1 FROM incident_evidence
        WHERE incident_id = i.id AND recovery_executed = TRUE
    ) AS recovery_attempted,

    -- Recurrence count (same category in last 30 days)
    (
        SELECT COUNT(*) FROM incidents i2
        WHERE i2.tenant_id = i.tenant_id
          AND i2.category = i.category
          AND i2.id != i.id
          AND i2.created_at >= i.created_at - INTERVAL '30 days'
          AND i2.created_at < i.created_at
    ) AS recurrence_count,

    -- Time to resolution (if resolved)
    CASE
        WHEN i.resolved_at IS NOT NULL THEN
            EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) * 1000
        ELSE NULL
    END AS time_to_resolution_ms,

    -- Topic classification (for filtering)
    CASE
        WHEN i.status = 'active' THEN 'ACTIVE'
        WHEN i.status = 'resolved' THEN 'RESOLVED'
        ELSE 'UNKNOWN'
    END AS topic

FROM incidents i;
```

### Indexes for v_incidents_o2

```sql
-- Primary query patterns
CREATE INDEX idx_incidents_tenant_status ON incidents(tenant_id, status);
CREATE INDEX idx_incidents_tenant_category ON incidents(tenant_id, category);
CREATE INDEX idx_incidents_tenant_severity ON incidents(tenant_id, severity);
CREATE INDEX idx_incidents_tenant_created ON incidents(tenant_id, created_at DESC);

-- Resolution analysis
CREATE INDEX idx_incidents_resolution ON incidents(tenant_id, resolution_method)
    WHERE resolution_method IS NOT NULL;

-- Cost impact analysis (partial index)
CREATE INDEX idx_incidents_cost_impact ON incidents(tenant_id, cost_impact)
    WHERE cost_impact IS NOT NULL;

-- Cross-domain link
CREATE INDEX idx_incidents_source_run ON incidents(source_run_id)
    WHERE source_run_id IS NOT NULL;

-- Evidence lookup
CREATE INDEX idx_incident_evidence_incident ON incident_evidence(incident_id);

-- Events timeline
CREATE INDEX idx_incident_events_incident ON incident_events(incident_id, created_at);
```

---

## 2. ACT-O1: Active Incidents List

**Capability:** `incidents.list`
**Endpoint:** `GET /incidents?topic=ACTIVE`

```sql
SELECT
    incident_id,
    tenant_id,
    severity,
    status,
    category,
    source_run_id,
    first_seen_at,
    last_seen_at,
    evidence_count,
    recurrence_count
FROM v_incidents_o2
WHERE tenant_id = :tenant_id
  AND topic = 'ACTIVE'
ORDER BY
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    first_seen_at DESC
LIMIT :limit OFFSET :offset;
```

---

## 3. ACT-O2: Incidents Summary

**Capability:** `incidents.summary`
**Endpoint:** `GET /incidents/summary`

```sql
SELECT
    severity,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM v_incidents_o2
WHERE tenant_id = :tenant_id
  AND topic = 'ACTIVE'
GROUP BY severity
ORDER BY
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END;
```

---

## 4. ACT-O3: Incidents Metrics

**Capability:** `incidents.metrics`
**Endpoint:** `GET /incidents/metrics`

```sql
WITH metrics AS (
    SELECT
        COUNT(*) AS total_active,
        COUNT(*) FILTER (WHERE severity = 'critical') AS critical_count,
        COUNT(*) FILTER (WHERE severity = 'high') AS high_count,
        AVG(recurrence_count) AS avg_recurrence,
        SUM(COALESCE(cost_impact, 0)) AS total_cost_impact
    FROM v_incidents_o2
    WHERE tenant_id = :tenant_id
      AND topic = 'ACTIVE'
),
resolution_metrics AS (
    SELECT
        AVG(time_to_resolution_ms) AS avg_resolution_time_ms,
        COUNT(*) AS resolved_count
    FROM v_incidents_o2
    WHERE tenant_id = :tenant_id
      AND topic = 'RESOLVED'
      AND first_seen_at >= NOW() - INTERVAL '24 hours'
)
SELECT
    m.total_active,
    m.critical_count,
    m.high_count,
    ROUND(m.avg_recurrence::numeric, 2) AS avg_recurrence,
    ROUND(m.total_cost_impact, 2) AS total_cost_impact,
    ROUND(r.avg_resolution_time_ms, 0) AS avg_resolution_time_ms,
    r.resolved_count AS resolved_last_24h
FROM metrics m, resolution_metrics r;
```

---

## 5. ACT-O4: Incident Patterns

**Capability:** `incidents.patterns`
**Endpoint:** `GET /incidents/patterns`
**Service:** `IncidentPatternService`

```sql
-- Pattern: Category clusters
WITH category_patterns AS (
    SELECT
        category,
        COUNT(*) AS incident_count,
        array_agg(incident_id ORDER BY first_seen_at DESC) AS incident_ids
    FROM v_incidents_o2
    WHERE tenant_id = :tenant_id
      AND first_seen_at >= NOW() - INTERVAL :window_hours HOUR
    GROUP BY category
    HAVING COUNT(*) >= :threshold
),
-- Pattern: Severity escalation (multiple high/critical in short window)
severity_clusters AS (
    SELECT
        'severity_spike' AS pattern_type,
        severity,
        COUNT(*) AS count,
        array_agg(incident_id) AS incident_ids
    FROM v_incidents_o2
    WHERE tenant_id = :tenant_id
      AND severity IN ('critical', 'high')
      AND first_seen_at >= NOW() - INTERVAL '1 hour'
    GROUP BY severity
    HAVING COUNT(*) >= 3
),
-- Pattern: Same source_run_id (cascading failure)
cascade_patterns AS (
    SELECT
        'cascade_failure' AS pattern_type,
        source_run_id,
        COUNT(*) AS count,
        array_agg(incident_id) AS incident_ids
    FROM v_incidents_o2
    WHERE tenant_id = :tenant_id
      AND source_run_id IS NOT NULL
      AND first_seen_at >= NOW() - INTERVAL :window_hours HOUR
    GROUP BY source_run_id
    HAVING COUNT(*) >= 2
)
SELECT * FROM category_patterns
UNION ALL
SELECT pattern_type, severity::text, count, incident_ids FROM severity_clusters
UNION ALL
SELECT pattern_type, source_run_id::text, count, incident_ids FROM cascade_patterns;
```

---

## 6. ACT-O5: Incident Attribution

**Capability:** `incidents.attribution`
**Endpoint:** `GET /incidents/{id}/evidence`

```sql
SELECT
    i.incident_id,
    i.source_run_id,
    i.category,
    i.severity,
    -- Evidence records
    (
        SELECT json_agg(json_build_object(
            'id', e.id,
            'type', e.evidence_type,
            'recovery_executed', e.recovery_executed,
            'payload', e.payload,
            'created_at', e.created_at
        ) ORDER BY e.created_at)
        FROM incident_evidence e
        WHERE e.incident_id = i.incident_id
    ) AS evidence,
    -- Event timeline
    (
        SELECT json_agg(json_build_object(
            'type', ev.event_type,
            'actor', ev.actor,
            'metadata', ev.metadata,
            'created_at', ev.created_at
        ) ORDER BY ev.created_at)
        FROM incident_events ev
        WHERE ev.incident_id = i.incident_id
    ) AS timeline,
    -- Cross-domain: linked run (if exists)
    (
        SELECT json_build_object(
            'run_id', r.run_id,
            'status', r.status,
            'risk_level', r.risk_level
        )
        FROM v_runs_o2 r
        WHERE r.run_id = i.source_run_id
    ) AS linked_run
FROM v_incidents_o2 i
WHERE i.incident_id = :incident_id
  AND i.tenant_id = :tenant_id;
```

---

## 7. HIST-O1: Historical Incidents

**Capability:** `incidents.historical_list`
**Endpoint:** `GET /incidents?created_before=...`

```sql
SELECT
    incident_id,
    severity,
    status,
    category,
    resolution_method,
    cost_impact,
    first_seen_at,
    resolved_at,
    time_to_resolution_ms,
    recurrence_count
FROM v_incidents_o2
WHERE tenant_id = :tenant_id
  AND first_seen_at < :created_before
ORDER BY first_seen_at DESC
LIMIT :limit OFFSET :offset;
```

---

## 8. HIST-O2: Incidents by Category

**Capability:** `incidents.by_category`
**Endpoint:** `GET /incidents?category=...`

```sql
SELECT
    category,
    COUNT(*) AS count,
    COUNT(*) FILTER (WHERE status = 'active') AS active_count,
    COUNT(*) FILTER (WHERE status = 'resolved') AS resolved_count,
    AVG(recurrence_count) AS avg_recurrence,
    SUM(COALESCE(cost_impact, 0)) AS total_cost
FROM v_incidents_o2
WHERE tenant_id = :tenant_id
  AND (:category IS NULL OR category = :category)
GROUP BY category
ORDER BY count DESC;
```

---

## 9. HIST-O3: Recurring Incidents

**Capability:** `incidents.recurring`
**Endpoint:** `GET /incidents/recurring`
**Service:** `RecurrenceAnalysisService`

```sql
WITH recurrence_groups AS (
    SELECT
        category,
        resolution_method,
        COUNT(*) AS total_occurrences,
        COUNT(DISTINCT DATE(first_seen_at)) AS distinct_days,
        MIN(first_seen_at) AS first_occurrence,
        MAX(first_seen_at) AS last_occurrence,
        array_agg(incident_id ORDER BY first_seen_at DESC) AS incident_ids
    FROM v_incidents_o2
    WHERE tenant_id = :tenant_id
      AND first_seen_at >= NOW() - INTERVAL :baseline_days DAY
    GROUP BY category, resolution_method
    HAVING COUNT(*) >= :recurrence_threshold
)
SELECT
    category,
    resolution_method,
    total_occurrences,
    distinct_days,
    ROUND(total_occurrences::numeric / GREATEST(distinct_days, 1), 2) AS occurrences_per_day,
    first_occurrence,
    last_occurrence,
    incident_ids[1:5] AS recent_incident_ids  -- Last 5
FROM recurrence_groups
ORDER BY total_occurrences DESC
LIMIT :limit;
```

---

## 10. HIST-O4: Cost Impact Analysis

**Capability:** `incidents.cost_impact`
**Endpoint:** `GET /incidents/cost-impact`

```sql
WITH cost_by_category AS (
    SELECT
        category,
        COUNT(*) AS incident_count,
        SUM(COALESCE(cost_impact, 0)) AS total_cost,
        AVG(COALESCE(cost_impact, 0)) AS avg_cost,
        MAX(cost_impact) AS max_cost
    FROM v_incidents_o2
    WHERE tenant_id = :tenant_id
      AND first_seen_at >= NOW() - INTERVAL :window_days DAY
    GROUP BY category
),
cost_by_severity AS (
    SELECT
        severity,
        COUNT(*) AS incident_count,
        SUM(COALESCE(cost_impact, 0)) AS total_cost
    FROM v_incidents_o2
    WHERE tenant_id = :tenant_id
      AND first_seen_at >= NOW() - INTERVAL :window_days DAY
    GROUP BY severity
)
SELECT
    'by_category' AS breakdown_type,
    category AS dimension,
    incident_count,
    ROUND(total_cost, 2) AS total_cost,
    ROUND(avg_cost, 2) AS avg_cost,
    ROUND(max_cost, 2) AS max_cost
FROM cost_by_category
UNION ALL
SELECT
    'by_severity' AS breakdown_type,
    severity AS dimension,
    incident_count,
    ROUND(total_cost, 2) AS total_cost,
    NULL AS avg_cost,
    NULL AS max_cost
FROM cost_by_severity
ORDER BY breakdown_type, total_cost DESC;
```

---

## 11. RES-O1: Resolved Incidents

**Capability:** `incidents.resolved_list`
**Endpoint:** `GET /incidents?topic=RESOLVED`

```sql
SELECT
    incident_id,
    severity,
    category,
    resolution_method,
    cost_impact,
    first_seen_at,
    resolved_at,
    resolved_by,
    time_to_resolution_ms,
    recovery_attempted
FROM v_incidents_o2
WHERE tenant_id = :tenant_id
  AND topic = 'RESOLVED'
ORDER BY resolved_at DESC
LIMIT :limit OFFSET :offset;
```

---

## 12. RES-O2 & RES-O4: Resolution Details & Outcome

**Capability:** `incidents.resolution_method`, `incidents.outcome`
**Endpoint:** `GET /incidents/{id}`

```sql
SELECT
    incident_id,
    severity,
    status,
    category,
    resolution_method,
    cost_impact,
    first_seen_at,
    resolved_at,
    resolved_by,
    time_to_resolution_ms,
    recurrence_count,
    evidence_count,
    recovery_attempted,
    -- Resolution outcome classification
    CASE
        WHEN status = 'resolved' AND resolution_method = 'auto' THEN 'AUTO_RESOLVED'
        WHEN status = 'resolved' AND resolution_method = 'rollback' THEN 'ROLLBACK_APPLIED'
        WHEN status = 'resolved' AND resolution_method = 'manual' THEN 'MANUAL_INTERVENTION'
        WHEN status = 'active' THEN 'PENDING'
        ELSE 'UNKNOWN'
    END AS outcome_classification
FROM v_incidents_o2
WHERE incident_id = :incident_id
  AND tenant_id = :tenant_id;
```

---

## 13. RES-O3: Recovery Actions

**Capability:** `incidents.recovery_actions`
**Endpoint:** `GET /incidents/{id}/evidence` (filtered)

```sql
SELECT
    e.id,
    e.evidence_type,
    e.recovery_executed,
    e.payload,
    e.created_at
FROM incident_evidence e
JOIN incidents i ON i.id = e.incident_id
WHERE e.incident_id = :incident_id
  AND i.tenant_id = :tenant_id
  AND e.evidence_type = 'action'
ORDER BY e.created_at;
```

---

## 14. RES-O5: Learnings

**Capability:** `incidents.learnings`
**Endpoint:** `GET /incidents/{id}/learnings`
**Service:** `PostMortemService`

```sql
-- Learnings are structured records, not AI-generated
-- Stored in incident_evidence with type = 'postmortem'
SELECT
    e.id AS learning_id,
    e.payload->>'summary' AS summary,
    e.payload->>'root_cause' AS root_cause,
    e.payload->>'prevention_steps' AS prevention_steps,
    e.payload->>'action_items' AS action_items,
    e.payload->>'created_by' AS created_by,
    e.created_at
FROM incident_evidence e
JOIN incidents i ON i.id = e.incident_id
WHERE e.incident_id = :incident_id
  AND i.tenant_id = :tenant_id
  AND e.evidence_type = 'postmortem'
ORDER BY e.created_at DESC
LIMIT 1;
```

---

## 15. Index Summary

| Index | Columns | Purpose |
|-------|---------|---------|
| `idx_incidents_tenant_status` | (tenant_id, status) | Topic filtering |
| `idx_incidents_tenant_category` | (tenant_id, category) | Category breakdown |
| `idx_incidents_tenant_severity` | (tenant_id, severity) | Severity filtering |
| `idx_incidents_tenant_created` | (tenant_id, created_at DESC) | Time-based queries |
| `idx_incidents_resolution` | (tenant_id, resolution_method) | Resolution analysis |
| `idx_incidents_cost_impact` | (tenant_id, cost_impact) | Cost analysis |
| `idx_incidents_source_run` | (source_run_id) | Cross-domain link |
| `idx_incident_evidence_incident` | (incident_id) | Evidence lookup |
| `idx_incident_events_incident` | (incident_id, created_at) | Timeline queries |

---

## 16. Related Documents

| Document | Purpose |
|----------|---------|
| `INCIDENTS_DOMAIN_AUDIT.md` | Coverage analysis |
| `INCIDENTS_DOMAIN_CONTRACT.md` | Enforcement rules |
| `CROSS_DOMAIN_CONTRACT.md` | Activity ↔ Incidents ↔ Policies |
