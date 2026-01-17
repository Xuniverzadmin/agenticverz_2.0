# Activity Domain — Exact SQL Definitions

**Status:** IMPLEMENTATION READY
**Created:** 2026-01-17
**Reference:** Activity Domain System Design

---

## 0. Schema Foundation

### Source Tables (L6)

```sql
-- Primary source: runs table with O2 columns
-- View: v_runs_o2 (read-only projection)

-- Key columns from v_runs_o2:
-- run_id, tenant_id, project_id, is_synthetic
-- source, provider_type, state, status
-- started_at, last_seen_at, completed_at, duration_ms
-- risk_level, latency_bucket, evidence_health, integrity_status
-- incident_count, policy_draft_count, policy_violation
-- input_tokens, output_tokens, estimated_cost_usd

-- Secondary source: aos_trace_steps
-- Key columns:
-- trace_id, step_index, skill_id, skill_name
-- status, outcome_category, outcome_code
-- cost_cents, duration_ms, retry_count
-- timestamp
```

### Existing Indexes (from 086_runs_o2_schema)

```sql
idx_runs_tenant_state_started   -- (tenant_id, state, started_at)
idx_runs_tenant_risk            -- (tenant_id, risk_level)
idx_runs_tenant_status          -- (tenant_id, status)
idx_runs_tenant_completed       -- (tenant_id, completed_at)
idx_runs_tenant_latency         -- (tenant_id, latency_bucket)
idx_runs_tenant_lastseen        -- (tenant_id, last_seen_at)
idx_runs_tenant_project         -- (tenant_id, project_id)
```

---

## 1. COMP-O3 — Status Summary

### Endpoint

```
GET /api/v1/activity/summary/by-status
```

### Capability

```
activity.summary_by_status
```

### SQL (Exact)

```sql
-- Summary by status for completed runs
-- Uses existing idx_runs_tenant_status index

SELECT
    status,
    COUNT(*) as count
FROM v_runs_o2
WHERE tenant_id = :tenant_id
  AND state = 'COMPLETED'
  AND (:project_id IS NULL OR project_id = :project_id)
  AND (:started_after IS NULL OR started_at >= :started_after)
  AND (:started_before IS NULL OR started_at <= :started_before)
GROUP BY status
ORDER BY count DESC;
```

### Response Shape

```json
{
  "tenant_id": "tenant_xxx",
  "window": {
    "started_after": "2026-01-10T00:00:00Z",
    "started_before": "2026-01-17T23:59:59Z"
  },
  "summary": {
    "succeeded": 1203,
    "failed": 84,
    "aborted": 12,
    "retry": 5
  },
  "near_threshold_count": 31,
  "total": 1335
}
```

### Near-Threshold Query (Supplemental)

```sql
-- Count runs where risk_level indicates proximity to limits
SELECT COUNT(*) as near_threshold_count
FROM v_runs_o2
WHERE tenant_id = :tenant_id
  AND state = 'COMPLETED'
  AND risk_level IN ('NEAR_THRESHOLD', 'AT_RISK')
  AND (:project_id IS NULL OR project_id = :project_id)
  AND (:started_after IS NULL OR started_at >= :started_after)
  AND (:started_before IS NULL OR started_at <= :started_before);
```

### Index Recommendation

```sql
-- Existing idx_runs_tenant_status is sufficient
-- No new index required
```

---

## 2. LIVE-O5 — Runs by Dimension

### Endpoint

```
GET /api/v1/activity/runs/by-dimension?dim=provider_type|source|agent_id
```

### Capability

```
activity.runs_by_dimension
```

### SQL (Exact)

```sql
-- Dynamic GROUP BY based on dimension parameter
-- Dimension MUST be from allowlist: provider_type, source, agent_id

-- For dim=provider_type:
SELECT
    provider_type as dimension_key,
    COUNT(*) as count
FROM v_runs_o2
WHERE tenant_id = :tenant_id
  AND state = :state  -- 'LIVE' or 'COMPLETED'
  AND (:project_id IS NULL OR project_id = :project_id)
GROUP BY provider_type
ORDER BY count DESC
LIMIT 20;

-- For dim=source:
SELECT
    source as dimension_key,
    COUNT(*) as count
FROM v_runs_o2
WHERE tenant_id = :tenant_id
  AND state = :state
  AND (:project_id IS NULL OR project_id = :project_id)
GROUP BY source
ORDER BY count DESC
LIMIT 20;

-- For dim=agent_id:
SELECT
    COALESCE(agent_id, 'unknown') as dimension_key,
    COUNT(*) as count
FROM runs  -- Note: uses runs table, not v_runs_o2 (agent_id not in view)
WHERE tenant_id = :tenant_id
  AND state = :state
  AND (:project_id IS NULL OR project_id = :project_id)
GROUP BY agent_id
ORDER BY count DESC
LIMIT 20;
```

### Response Shape

```json
{
  "dimension": "provider_type",
  "state": "LIVE",
  "buckets": [
    { "key": "anthropic", "count": 412 },
    { "key": "openai", "count": 304 },
    { "key": "internal", "count": 28 }
  ],
  "total_runs": 744
}
```

### Dimension Allowlist (Enforced in Code)

```python
ALLOWED_DIMENSIONS = frozenset({"provider_type", "source", "agent_id"})

def validate_dimension(dim: str) -> None:
    if dim not in ALLOWED_DIMENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_dimension",
                "allowed": list(ALLOWED_DIMENSIONS),
                "received": dim
            }
        )
```

### Index Recommendation

```sql
-- New index for provider_type grouping
CREATE INDEX idx_runs_tenant_provider
ON runs (tenant_id, provider_type)
WHERE state IS NOT NULL;

-- New index for source grouping
CREATE INDEX idx_runs_tenant_source
ON runs (tenant_id, source)
WHERE state IS NOT NULL;
```

---

## 3. SIG-O2 — Threshold Signals

### Capability

```
activity.threshold_signals
```

### Design Decision

No new endpoint needed. Use existing `/activity/runs` with filters:

```
GET /api/v1/activity/runs?risk_level=NEAR_THRESHOLD&risk_level=AT_RISK
```

### SQL (Already Implemented)

```sql
-- Part of existing list_runs query
WHERE tenant_id = :tenant_id
  AND risk_level = ANY(:risk_level)  -- ['NEAR_THRESHOLD', 'AT_RISK']
```

### Threshold Definition (Code Constant)

```python
# risk_level is pre-computed in v_runs_o2
# Definition of "near threshold" for SIG-O2:
NEAR_THRESHOLD_LEVELS = frozenset({"NEAR_THRESHOLD", "AT_RISK"})
```

---

## 4. SIG-O3 — Pattern Detection

### Endpoint

```
GET /api/v1/activity/patterns
```

### Capability

```
activity.patterns
```

### SQL (Pattern Queries)

```sql
-- Pattern 1: Retry Loops (>3 retries in same run)
SELECT
    t.run_id,
    'retry_loop' as pattern_type,
    COUNT(*) as retry_count,
    MAX(s.retry_count) as max_step_retries
FROM aos_traces t
JOIN aos_trace_steps s ON s.trace_id = t.trace_id
WHERE t.tenant_id = :tenant_id
  AND t.started_at >= :window_start
  AND s.retry_count > 0
GROUP BY t.run_id
HAVING SUM(s.retry_count) >= 3
ORDER BY retry_count DESC
LIMIT 10;

-- Pattern 2: Step Oscillation (same skill called >3 times non-consecutively)
WITH step_sequences AS (
    SELECT
        trace_id,
        skill_id,
        step_index,
        LAG(skill_id) OVER (PARTITION BY trace_id ORDER BY step_index) as prev_skill
    FROM aos_trace_steps
    WHERE trace_id IN (
        SELECT trace_id FROM aos_traces
        WHERE tenant_id = :tenant_id
          AND started_at >= :window_start
    )
)
SELECT
    t.run_id,
    'step_oscillation' as pattern_type,
    ss.skill_id,
    COUNT(*) as oscillation_count
FROM step_sequences ss
JOIN aos_traces t ON t.trace_id = ss.trace_id
WHERE ss.skill_id = ss.prev_skill  -- Same skill called again
GROUP BY t.run_id, ss.skill_id
HAVING COUNT(*) >= 3
ORDER BY oscillation_count DESC
LIMIT 10;

-- Pattern 3: Tool-Call Loops (repeated skill within 5 steps)
WITH windowed_skills AS (
    SELECT
        trace_id,
        skill_id,
        step_index,
        COUNT(*) OVER (
            PARTITION BY trace_id, skill_id
            ORDER BY step_index
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ) as recent_calls
    FROM aos_trace_steps
    WHERE trace_id IN (
        SELECT trace_id FROM aos_traces
        WHERE tenant_id = :tenant_id
          AND started_at >= :window_start
    )
)
SELECT
    t.run_id,
    'tool_call_loop' as pattern_type,
    ws.skill_id,
    MAX(ws.recent_calls) as loop_depth
FROM windowed_skills ws
JOIN aos_traces t ON t.trace_id = ws.trace_id
WHERE ws.recent_calls >= 3
GROUP BY t.run_id, ws.skill_id
ORDER BY loop_depth DESC
LIMIT 10;

-- Pattern 4: Timeout Cascades (multiple steps with duration > expected)
SELECT
    t.run_id,
    'timeout_cascade' as pattern_type,
    COUNT(*) as slow_step_count,
    AVG(s.duration_ms) as avg_duration_ms
FROM aos_traces t
JOIN aos_trace_steps s ON s.trace_id = t.trace_id
WHERE t.tenant_id = :tenant_id
  AND t.started_at >= :window_start
  AND s.duration_ms > :slow_threshold_ms  -- e.g., 5000ms
GROUP BY t.run_id
HAVING COUNT(*) >= 2
ORDER BY slow_step_count DESC
LIMIT 10;
```

### Response Shape

```json
{
  "window": {
    "start": "2026-01-17T00:00:00Z",
    "end": "2026-01-17T23:59:59Z"
  },
  "patterns": [
    {
      "pattern_type": "retry_loop",
      "run_ids": ["run_abc", "run_def"],
      "count": 2,
      "confidence": 0.95,
      "details": { "avg_retries": 4.5 }
    },
    {
      "pattern_type": "tool_call_loop",
      "run_ids": ["run_xyz"],
      "count": 1,
      "confidence": 0.82,
      "details": { "skill_id": "llm_invoke_v2", "loop_depth": 5 }
    }
  ]
}
```

### Index Recommendation

```sql
-- Improve step analysis performance
CREATE INDEX idx_aos_trace_steps_skill_retry
ON aos_trace_steps (trace_id, skill_id, retry_count);

CREATE INDEX idx_aos_trace_steps_duration
ON aos_trace_steps (trace_id, duration_ms);
```

---

## 5. SIG-O4 — Cost Analysis

### Endpoint

```
GET /api/v1/activity/cost-analysis
```

### Capability

```
activity.cost_analysis
```

### SQL (Exact)

```sql
-- Step 1: Calculate baseline stats per agent (last 7 days)
WITH baseline AS (
    SELECT
        COALESCE(agent_id, 'unknown') as agent_id,
        AVG(estimated_cost_usd) as avg_cost,
        STDDEV(estimated_cost_usd) as stddev_cost,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY estimated_cost_usd) as p95_cost,
        COUNT(*) as run_count
    FROM runs
    WHERE tenant_id = :tenant_id
      AND completed_at >= NOW() - INTERVAL '7 days'
      AND completed_at < NOW() - INTERVAL '1 day'  -- Exclude today
      AND estimated_cost_usd IS NOT NULL
    GROUP BY agent_id
),

-- Step 2: Current window stats (today)
current_window AS (
    SELECT
        COALESCE(agent_id, 'unknown') as agent_id,
        AVG(estimated_cost_usd) as current_avg_cost,
        SUM(estimated_cost_usd) as total_cost,
        COUNT(*) as run_count
    FROM runs
    WHERE tenant_id = :tenant_id
      AND started_at >= NOW() - INTERVAL '1 day'
      AND estimated_cost_usd IS NOT NULL
    GROUP BY agent_id
)

-- Step 3: Compute anomalies (Z-score > 2)
SELECT
    c.agent_id,
    c.current_avg_cost,
    c.total_cost,
    c.run_count,
    b.avg_cost as baseline_avg,
    b.p95_cost as baseline_p95,
    CASE
        WHEN b.stddev_cost > 0 THEN
            (c.current_avg_cost - b.avg_cost) / b.stddev_cost
        ELSE 0
    END as z_score,
    CASE
        WHEN b.stddev_cost > 0 AND (c.current_avg_cost - b.avg_cost) / b.stddev_cost > 2 THEN true
        WHEN c.current_avg_cost > b.p95_cost THEN true
        ELSE false
    END as is_anomaly
FROM current_window c
LEFT JOIN baseline b ON b.agent_id = c.agent_id
ORDER BY z_score DESC;
```

### Response Shape

```json
{
  "window": {
    "current": "last_24h",
    "baseline": "7_day_average"
  },
  "agents": [
    {
      "agent_id": "agent_sales_001",
      "current_cost_usd": 12.50,
      "baseline_avg_usd": 4.20,
      "baseline_p95_usd": 8.00,
      "z_score": 2.8,
      "is_anomaly": true,
      "run_count": 45
    },
    {
      "agent_id": "agent_support_002",
      "current_cost_usd": 3.10,
      "baseline_avg_usd": 3.00,
      "baseline_p95_usd": 5.50,
      "z_score": 0.2,
      "is_anomaly": false,
      "run_count": 120
    }
  ],
  "total_anomalies": 1,
  "total_cost_usd": 156.40
}
```

### Index Recommendation

```sql
-- Cost analysis index
CREATE INDEX idx_runs_tenant_agent_cost
ON runs (tenant_id, agent_id, estimated_cost_usd, completed_at)
WHERE estimated_cost_usd IS NOT NULL;
```

---

## 6. SIG-O5 — Attention Queue (Composite)

### Endpoint

```
GET /api/v1/activity/attention-queue
```

### Capability

```
activity.attention_queue
```

### SQL (Composite Scoring)

```sql
-- Attention queue combines multiple signals into a single score
-- Weights are frozen constants (not configurable)

WITH run_signals AS (
    SELECT
        run_id,
        tenant_id,
        -- Risk score (0-1)
        CASE risk_level
            WHEN 'VIOLATED' THEN 1.0
            WHEN 'AT_RISK' THEN 0.8
            WHEN 'NEAR_THRESHOLD' THEN 0.5
            ELSE 0.0
        END as risk_score,
        -- Latency score (0-1)
        CASE latency_bucket
            WHEN 'STALLED' THEN 1.0
            WHEN 'SLOW' THEN 0.5
            ELSE 0.0
        END as latency_score,
        -- Evidence health score (0-1)
        CASE evidence_health
            WHEN 'MISSING' THEN 1.0
            WHEN 'DEGRADED' THEN 0.5
            ELSE 0.0
        END as evidence_score,
        -- Impact score (0-1)
        CASE
            WHEN policy_violation THEN 0.8
            WHEN incident_count > 0 THEN 0.6
            ELSE 0.0
        END as impact_score,
        -- Recency score (0-1, decays over 24h)
        GREATEST(0, 1 - EXTRACT(EPOCH FROM (NOW() - started_at)) / 86400) as recency_score,
        state,
        status,
        started_at
    FROM v_runs_o2
    WHERE tenant_id = :tenant_id
      AND (state = 'LIVE' OR completed_at >= NOW() - INTERVAL '24 hours')
)

SELECT
    run_id,
    -- Composite score (weights are FROZEN)
    (
        risk_score * 0.35 +
        latency_score * 0.15 +
        evidence_score * 0.10 +
        impact_score * 0.25 +
        recency_score * 0.15
    ) as attention_score,
    -- Reason codes for transparency
    ARRAY_REMOVE(ARRAY[
        CASE WHEN risk_score > 0 THEN 'risk' END,
        CASE WHEN latency_score > 0 THEN 'latency' END,
        CASE WHEN evidence_score > 0 THEN 'evidence' END,
        CASE WHEN impact_score > 0 THEN 'impact' END
    ], NULL) as reasons,
    state,
    status,
    started_at
FROM run_signals
WHERE (
    risk_score > 0 OR
    latency_score > 0 OR
    evidence_score > 0 OR
    impact_score > 0
)
ORDER BY attention_score DESC
LIMIT :limit;  -- Default 20
```

### Weight Constants (Frozen in Code)

```python
# ATTENTION_WEIGHTS - DO NOT MODIFY without governance approval
ATTENTION_WEIGHTS = {
    "risk": 0.35,       # Risk level contribution
    "impact": 0.25,     # Policy violation / incidents
    "latency": 0.15,    # Performance degradation
    "recency": 0.15,    # Time-based decay
    "evidence": 0.10,   # Telemetry health
}

# Sum must equal 1.0
assert sum(ATTENTION_WEIGHTS.values()) == 1.0
```

### Response Shape

```json
{
  "queue": [
    {
      "run_id": "run_abc123",
      "attention_score": 0.91,
      "reasons": ["risk", "impact"],
      "state": "COMPLETED",
      "status": "failed",
      "started_at": "2026-01-17T10:30:00Z"
    },
    {
      "run_id": "run_def456",
      "attention_score": 0.72,
      "reasons": ["risk", "latency"],
      "state": "LIVE",
      "status": "running",
      "started_at": "2026-01-17T11:15:00Z"
    }
  ],
  "total_attention_items": 2,
  "weights_version": "1.0",
  "generated_at": "2026-01-17T12:00:00Z"
}
```

---

## 7. Migration: New Indexes

### Migration File: `095_activity_signal_indexes.py`

```python
"""
PIN-XXX: Add indexes for Activity signal endpoints

Supports:
- COMP-O3: Summary by status (uses existing index)
- LIVE-O5: Runs by dimension (new provider/source indexes)
- SIG-O3: Pattern detection (step analysis indexes)
- SIG-O4: Cost analysis (agent cost index)
- SIG-O5: Attention queue (composite, uses existing indexes)

Revision ID: 095_activity_signal_indexes
Revises: 094_limit_overrides
Create Date: 2026-01-17
"""

from alembic import op

revision = "095_activity_signal_indexes"
down_revision = "094_limit_overrides"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # LIVE-O5: Dimension grouping indexes
    op.create_index(
        "idx_runs_tenant_provider",
        "runs",
        ["tenant_id", "provider_type"],
        postgresql_using="btree"
    )

    op.create_index(
        "idx_runs_tenant_source",
        "runs",
        ["tenant_id", "source"],
        postgresql_using="btree"
    )

    # SIG-O3: Pattern detection indexes
    op.create_index(
        "idx_aos_trace_steps_skill_retry",
        "aos_trace_steps",
        ["trace_id", "skill_id", "retry_count"],
        postgresql_using="btree"
    )

    op.create_index(
        "idx_aos_trace_steps_duration",
        "aos_trace_steps",
        ["trace_id", "duration_ms"],
        postgresql_using="btree"
    )

    # SIG-O4: Cost analysis index
    op.execute("""
        CREATE INDEX idx_runs_tenant_agent_cost
        ON runs (tenant_id, agent_id, estimated_cost_usd, completed_at)
        WHERE estimated_cost_usd IS NOT NULL
    """)


def downgrade() -> None:
    op.drop_index("idx_runs_tenant_agent_cost", table_name="runs")
    op.drop_index("idx_aos_trace_steps_duration", table_name="aos_trace_steps")
    op.drop_index("idx_aos_trace_steps_skill_retry", table_name="aos_trace_steps")
    op.drop_index("idx_runs_tenant_source", table_name="runs")
    op.drop_index("idx_runs_tenant_provider", table_name="runs")
```

---

## 8. Summary

| Endpoint | SQL Complexity | Index Status | Implementation Effort |
|----------|----------------|--------------|----------------------|
| COMP-O3 `/summary/by-status` | Simple GROUP BY | EXISTS | Low |
| LIVE-O5 `/runs/by-dimension` | Simple GROUP BY | NEEDS INDEX | Low |
| SIG-O2 (threshold) | Existing query | EXISTS | None (use filters) |
| SIG-O3 `/patterns` | Window functions | NEEDS INDEX | Medium |
| SIG-O4 `/cost-analysis` | CTE with stats | NEEDS INDEX | Medium |
| SIG-O5 `/attention-queue` | Composite CTE | EXISTS | Medium |

---

## 9. Query Plan Validation

Before deployment, run EXPLAIN ANALYZE on each query:

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
-- <insert query here>
```

Expected characteristics:
- Index Scan or Index Only Scan (not Seq Scan)
- Execution time < 100ms for 10K rows
- No disk sorts (work_mem sufficient)
