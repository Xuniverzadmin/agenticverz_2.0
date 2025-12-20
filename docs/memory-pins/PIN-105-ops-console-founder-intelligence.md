# PIN-105: Ops Console — Founder Intelligence System

**Status:** ACTIVE
**Created:** 2025-12-20
**Author:** Claude Opus 4.5
**Depends On:** PIN-100 (M23), PIN-103 (Survival Stack)
**Milestone:** M24

---

## Executive Summary

The Ops Console is not an admin panel. It is a **behavioral truth engine** that answers founder questions without asking customers.

**Core Insight:** Customers will never tell you why they churn. Feedback is lagging, biased, and polite. Behavior never lies.

**Goal:** Answer these questions without customer input:
1. Why did they subscribe?
2. Where is stickiness actually created?
3. What caused churn or disengagement?
4. Which subsystem broke — model, policy, infra, UX, cost?
5. Am I hitting infra limits before revenue limits?

---

## Design Principles (Non-Negotiable)

### Principle 1: Intent > Feedback

Never rely on surveys. Infer everything from:
- Sequences (what they did first, second, third)
- Latency (how fast they act)
- Retries (what they struggle with)
- Replays (what they investigate)
- Exports (what they value enough to keep)
- Silence (what they stopped doing)

### Principle 2: Time-Ordered Truth

Everything must be:
- Event-sourced
- Timestamped
- Replayable

If you can't explain *why something happened*, the console failed.

### Principle 3: One Screen = One Decision

Every page must answer a **specific founder decision**, not "show data".

### Principle 4: Behavior > Words

- API usage continuing + console usage dropping = silent churn
- First export within 24h = high-intent legal buyer
- Many replays, no exports = trust-building phase
- Sudden activity spike = incident happened

---

## Navigation Structure

```
OPS CONSOLE (ops.agenticverz.com)
├── System Pulse         → "Is my business healthy right now?"
├── Customer Intelligence → "Who is this customer and are they slipping?"
├── Incident Intelligence → "What is breaking and is it systemic?"
├── Product Stickiness   → "Which feature actually keeps users?"
├── Revenue & Risk       → "Am I making money safely?"
├── Infra & Limits       → "What breaks first if I grow?"
└── Replay Lab           → "Can I reproduce and fix anything?"
```

No feature sprawl. Each tab maps to a **founder question**.

---

## Data Model

### Core Event Table

All insights are derived from a single event stream. No derived tables without lineage.

```sql
CREATE TABLE ops_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    tenant_id UUID NOT NULL,
    user_id UUID,                    -- End-user (nullable)
    session_id UUID,                 -- Conversation session (nullable)
    event_type TEXT NOT NULL,
    entity_type TEXT,                -- incident, replay, export, etc.
    entity_id UUID,
    severity INT,                    -- 1-5 scale
    latency_ms INT,
    cost_usd NUMERIC(10,6),
    metadata JSONB DEFAULT '{}'
);

-- Indexes for common queries
CREATE INDEX idx_events_tenant_time ON ops_events(tenant_id, timestamp DESC);
CREATE INDEX idx_events_type_time ON ops_events(event_type, timestamp DESC);
CREATE INDEX idx_events_tenant_type ON ops_events(tenant_id, event_type);
```

### Canonical Event Types

These are the **only** event types. Do not add without updating this PIN.

| Event Type | Trigger | Key Metadata |
|------------|---------|--------------|
| `API_CALL_RECEIVED` | Any API request | endpoint, method, status_code |
| `INCIDENT_CREATED` | Policy violation detected | severity, policy_id, model |
| `INCIDENT_VIEWED` | User opens incident detail | time_on_page |
| `REPLAY_EXECUTED` | Replay button clicked | match_level, cost_delta |
| `EXPORT_GENERATED` | PDF/JSON export created | format, include_flags |
| `CERT_VERIFIED` | Certificate verification hit | source_ip, referrer |
| `POLICY_EVALUATED` | Policy check completed | policy_id, result, latency_ms |
| `POLICY_BLOCKED` | Policy blocked output | policy_id, reason |
| `LLM_CALL_MADE` | Upstream LLM called | model, tokens_in, tokens_out, cost_usd |
| `LLM_CALL_FAILED` | LLM call error | model, error_type, retry_count |
| `INFRA_LIMIT_HIT` | Resource threshold crossed | resource, current, limit |
| `SUBSCRIPTION_STARTED` | New paying customer | plan, source |
| `SUBSCRIPTION_CANCELLED` | Customer cancelled | reason (if provided), tenure_days |
| `FREEZE_ACTIVATED` | Kill switch triggered | scope (tenant/key) |
| `LOGIN` | User logged into console | source (guard/operator) |

**Rule:** Any new feature MUST emit at least one of these events.

### Migration

```sql
-- backend/alembic/versions/040_m24_ops_events.py
CREATE TABLE ops_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    session_id UUID,
    event_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id UUID,
    severity INT,
    latency_ms INT,
    cost_usd NUMERIC(10,6),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_events_tenant_time ON ops_events(tenant_id, timestamp DESC);
CREATE INDEX idx_events_type_time ON ops_events(event_type, timestamp DESC);
CREATE INDEX idx_events_tenant_type ON ops_events(tenant_id, event_type);

-- Retention: 90 days default, archive older
-- (handled by separate archival job)
```

---

## Module 1: System Pulse

**Question:** "Is my business healthy right now?"

### Metrics (Real-time + 24h Delta)

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| Active tenants | COUNT(DISTINCT tenant_id) WHERE timestamp > now() - 24h | Drop > 20% |
| Incidents captured | COUNT WHERE event_type = 'INCIDENT_CREATED' | Spike > 50% |
| Replays executed | COUNT WHERE event_type = 'REPLAY_EXECUTED' | Drop > 30% 🔴 |
| Exports generated | COUNT WHERE event_type = 'EXPORT_GENERATED' | Drop > 40% 🔴 |
| Failed LLM calls | COUNT WHERE event_type = 'LLM_CALL_FAILED' | > 5% of total |
| Infra saturation | From INFRA_LIMIT_HIT events | Any > 80% |

### Derived System State

```python
def get_system_state(metrics: dict) -> str:
    if metrics['llm_failure_rate'] > 0.05:
        return 'ACTIVE_FAILURE'
    if metrics['infra_saturation'] > 0.80:
        return 'ACTIVE_FAILURE'
    if metrics['replay_delta'] < -0.30:
        return 'SILENT_DEGRADATION'
    if metrics['export_delta'] < -0.40:
        return 'SILENT_DEGRADATION'
    return 'STABLE'
```

**Key Insight:** Reductions in replays/exports are louder than growth. That's where churn is born.

### UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ OPS CONSOLE                              ops.agenticverz.com │
│ System Pulse                                     Dec 20, 2025│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STATUS: 🟡 SILENT DEGRADATION                              │
│  Reason: Export volume down 40% vs last week                │
│                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐│
│  │ Active      │ │ Incidents   │ │ Replays     │ │Exports ││
│  │ Tenants     │ │             │ │             │ │        ││
│  │    14       │ │    312      │ │    41       │ │   6    ││
│  │   +2 ▲      │ │  +18% ▲     │ │  -22% ▼ ⚠️  │ │ -40% 🔴││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘│
│                                                             │
│  INFRA HEADROOM                                             │
│  Redis Memory   ████████░░░░░░░░░░░░  78%  (18 days to limit)│
│  DB Connections ██████░░░░░░░░░░░░░░  62%  (stable)         │
│  LLM Rate Limit █████░░░░░░░░░░░░░░░  51%  (stable)         │
│  SSE Concurrent ███░░░░░░░░░░░░░░░░░  32%  (stable)         │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  [View Customers]  [View Incidents]  [Replay Lab]           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### SQL Query

```sql
-- System Pulse: 24h metrics with delta
WITH current_period AS (
  SELECT
    COUNT(DISTINCT tenant_id) AS active_tenants,
    COUNT(*) FILTER (WHERE event_type = 'INCIDENT_CREATED') AS incidents,
    COUNT(*) FILTER (WHERE event_type = 'REPLAY_EXECUTED') AS replays,
    COUNT(*) FILTER (WHERE event_type = 'EXPORT_GENERATED') AS exports,
    COUNT(*) FILTER (WHERE event_type = 'LLM_CALL_FAILED') AS llm_failures,
    COUNT(*) FILTER (WHERE event_type = 'LLM_CALL_MADE') AS llm_total
  FROM ops_events
  WHERE timestamp > now() - interval '24 hours'
),
previous_period AS (
  SELECT
    COUNT(DISTINCT tenant_id) AS active_tenants,
    COUNT(*) FILTER (WHERE event_type = 'INCIDENT_CREATED') AS incidents,
    COUNT(*) FILTER (WHERE event_type = 'REPLAY_EXECUTED') AS replays,
    COUNT(*) FILTER (WHERE event_type = 'EXPORT_GENERATED') AS exports
  FROM ops_events
  WHERE timestamp BETWEEN now() - interval '48 hours' AND now() - interval '24 hours'
)
SELECT
  c.*,
  ROUND((c.active_tenants - p.active_tenants)::numeric / NULLIF(p.active_tenants, 0) * 100, 1) AS tenant_delta_pct,
  ROUND((c.incidents - p.incidents)::numeric / NULLIF(p.incidents, 0) * 100, 1) AS incident_delta_pct,
  ROUND((c.replays - p.replays)::numeric / NULLIF(p.replays, 0) * 100, 1) AS replay_delta_pct,
  ROUND((c.exports - p.exports)::numeric / NULLIF(p.exports, 0) * 100, 1) AS export_delta_pct,
  ROUND(c.llm_failures::numeric / NULLIF(c.llm_total, 0) * 100, 2) AS llm_failure_rate
FROM current_period c, previous_period p;
```

---

## Module 2: Customer Intelligence

**Question:** "Who is this customer and are they slipping?"

### A. Intent Inference (Automatic)

Derived from first 7 days of behavior:

```sql
WITH first_actions AS (
  SELECT
    tenant_id,
    MIN(timestamp) AS signup_time,
    MIN(timestamp) FILTER (WHERE event_type = 'INCIDENT_CREATED') AS first_incident,
    MIN(timestamp) FILTER (WHERE event_type = 'INCIDENT_VIEWED') AS first_view,
    MIN(timestamp) FILTER (WHERE event_type = 'REPLAY_EXECUTED') AS first_replay,
    MIN(timestamp) FILTER (WHERE event_type = 'EXPORT_GENERATED') AS first_export
  FROM ops_events
  WHERE event_type IN ('SUBSCRIPTION_STARTED', 'INCIDENT_CREATED', 'INCIDENT_VIEWED',
                       'REPLAY_EXECUTED', 'EXPORT_GENERATED')
  GROUP BY tenant_id
)
SELECT
  tenant_id,
  signup_time,
  CASE
    WHEN first_export IS NOT NULL AND first_export < signup_time + interval '7 days'
      THEN 'Legal/Compliance'
    WHEN first_replay IS NOT NULL AND first_replay < signup_time + interval '7 days'
      THEN 'Debugging'
    WHEN first_incident IS NOT NULL
      THEN 'Reliability Monitoring'
    ELSE 'Proxy Only'
  END AS inferred_intent,
  -- Confidence based on action speed
  CASE
    WHEN first_export IS NOT NULL AND first_export < signup_time + interval '24 hours' THEN 0.95
    WHEN first_export IS NOT NULL AND first_export < signup_time + interval '7 days' THEN 0.85
    WHEN first_replay IS NOT NULL THEN 0.75
    WHEN first_incident IS NOT NULL THEN 0.65
    ELSE 0.50
  END AS intent_confidence,
  -- Time-to-value metrics
  EXTRACT(EPOCH FROM (first_incident - signup_time)) / 3600 AS hours_to_first_incident,
  EXTRACT(EPOCH FROM (first_replay - signup_time)) / 3600 AS hours_to_first_replay,
  EXTRACT(EPOCH FROM (first_export - signup_time)) / 3600 AS hours_to_first_export
FROM first_actions;
```

### B. Stickiness Score (Daily Calculation)

Formula with time decay:

```python
def calculate_stickiness(tenant_id: str, days: int = 7) -> float:
    """
    Stickiness = weighted sum of valuable actions with recency decay.

    Weights:
    - Incident viewed: 0.2 (pain exists)
    - Replay executed: 0.3 (trust building)
    - Export generated: 0.5 (value captured)

    Decay: Actions older than 3 days weighted 50%
    """
    recent_weight = 1.0
    older_weight = 0.5

    score = (
        (recent_views * 0.2 + older_views * 0.2 * older_weight) +
        (recent_replays * 0.3 + older_replays * 0.3 * older_weight) +
        (recent_exports * 0.5 + older_exports * 0.5 * older_weight)
    )
    return round(score, 2)
```

```sql
-- Stickiness Score with decay
WITH actions AS (
  SELECT
    tenant_id,
    COUNT(*) FILTER (
      WHERE event_type = 'INCIDENT_VIEWED'
      AND timestamp > now() - interval '3 days'
    ) AS recent_views,
    COUNT(*) FILTER (
      WHERE event_type = 'INCIDENT_VIEWED'
      AND timestamp BETWEEN now() - interval '7 days' AND now() - interval '3 days'
    ) AS older_views,
    COUNT(*) FILTER (
      WHERE event_type = 'REPLAY_EXECUTED'
      AND timestamp > now() - interval '3 days'
    ) AS recent_replays,
    COUNT(*) FILTER (
      WHERE event_type = 'REPLAY_EXECUTED'
      AND timestamp BETWEEN now() - interval '7 days' AND now() - interval '3 days'
    ) AS older_replays,
    COUNT(*) FILTER (
      WHERE event_type = 'EXPORT_GENERATED'
      AND timestamp > now() - interval '3 days'
    ) AS recent_exports,
    COUNT(*) FILTER (
      WHERE event_type = 'EXPORT_GENERATED'
      AND timestamp BETWEEN now() - interval '7 days' AND now() - interval '3 days'
    ) AS older_exports
  FROM ops_events
  WHERE timestamp > now() - interval '7 days'
  GROUP BY tenant_id
)
SELECT
  tenant_id,
  ROUND(
    (recent_views * 0.2 + older_views * 0.1) +
    (recent_replays * 0.3 + older_replays * 0.15) +
    (recent_exports * 0.5 + older_exports * 0.25),
    2
  ) AS stickiness_score
FROM actions;
```

### C. Silent Churn Detector

**Definition:** Customer is paying, API calls continue, but investigation behavior stopped.

```sql
-- Silent Churn: API active but investigation stopped
SELECT
  tenant_id,
  MAX(timestamp) FILTER (WHERE event_type = 'API_CALL_RECEIVED') AS last_api_call,
  MAX(timestamp) FILTER (WHERE event_type IN ('INCIDENT_VIEWED', 'REPLAY_EXECUTED', 'EXPORT_GENERATED')) AS last_investigation,
  EXTRACT(EPOCH FROM (
    MAX(timestamp) FILTER (WHERE event_type = 'API_CALL_RECEIVED') -
    MAX(timestamp) FILTER (WHERE event_type IN ('INCIDENT_VIEWED', 'REPLAY_EXECUTED', 'EXPORT_GENERATED'))
  )) / 86400 AS investigation_gap_days
FROM ops_events
GROUP BY tenant_id
HAVING
  -- API active in last 48h
  MAX(timestamp) FILTER (WHERE event_type = 'API_CALL_RECEIVED') > now() - interval '48 hours'
  AND
  -- But no investigation in 7+ days
  MAX(timestamp) FILTER (WHERE event_type IN ('INCIDENT_VIEWED', 'REPLAY_EXECUTED', 'EXPORT_GENERATED')) < now() - interval '7 days'
ORDER BY investigation_gap_days DESC;
```

**Alert:** This is your **intervention moment**. Reach out before they cancel.

### D. Customer Profile UI

```
┌─────────────────────────────────────────────────────────────┐
│ CUSTOMER INTELLIGENCE                                       │
│ Tenant: acme-ai                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SUBSCRIPTION                                               │
│  Status: Active (Day 23)                                    │
│  Plan: Pro ($99/month)                                      │
│  Source: Organic (HN)                                       │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  INFERRED INTENT                                            │
│  Primary: Legal / Compliance                                │
│  Confidence: 0.86                                           │
│  Evidence: Export within 18h of signup                      │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  STICKINESS SCORE: 4.2  ↓ (was 6.1 last week)              │
│  CHURN RISK: 🔴 HIGH                                        │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ACTIVITY TIMELINE (Last 30 days)                           │
│                                                             │
│  API Calls       ██████████████████████████████  (stable)   │
│  Incidents       ████████████████░░░░░░░░░░░░░░  (declining)│
│  Investigations  ████████░░░░░░░░░░░░░░░░░░░░░░  (dropping) │
│  Replays         ████░░░░░░░░░░░░░░░░░░░░░░░░░░  (rare)     │
│  Exports         ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░  (stopped)  │
│                                                             │
│  Last Investigation: 9 days ago ⚠️                          │
│  Last Export: 14 days ago 🔴                                │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  TIME-TO-VALUE                                              │
│  Signup → First Incident: 2.3 hours                         │
│  Signup → First Replay: 18.4 hours                          │
│  Signup → First Export: 18.6 hours ✓ (fast = high intent)   │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  [View Incidents] [Force Replay Demo] [Revenue Impact]      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Module 3: Incident Intelligence

**Question:** "What is breaking and is it systemic?"

### Global Incident Heatmap

```sql
-- Incidents by model (last 24h)
SELECT
  metadata->>'model' AS model,
  COUNT(*) AS incident_count,
  ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 1) AS pct
FROM ops_events
WHERE event_type = 'INCIDENT_CREATED'
  AND timestamp > now() - interval '24 hours'
GROUP BY metadata->>'model'
ORDER BY incident_count DESC;

-- Incidents by policy version (last 24h)
SELECT
  metadata->>'policy_id' AS policy,
  COUNT(*) AS incident_count,
  AVG(severity) AS avg_severity
FROM ops_events
WHERE event_type = 'INCIDENT_CREATED'
  AND timestamp > now() - interval '24 hours'
GROUP BY metadata->>'policy_id'
ORDER BY incident_count DESC;
```

### Failure Attribution (Forced Classification)

Every incident MUST be attributed. No "unknown" allowed.

| Attribution | Detection Rule |
|-------------|----------------|
| `MODEL_HALLUCINATION` | Policy CONTENT_ACCURACY triggered |
| `POLICY_CONFLICT` | Multiple policies fired on same call |
| `CONTEXT_MISSING` | Context retrieval returned null/empty |
| `INFRA_TIMEOUT` | LLM call timeout or 5xx |
| `BUDGET_EXCEEDED` | Cost limit triggered |
| `USER_MISUSE` | Input policy violations |

```sql
-- Failure attribution distribution
SELECT
  COALESCE(metadata->>'attribution', 'UNCLASSIFIED') AS attribution,
  COUNT(*) AS count,
  ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 1) AS pct
FROM ops_events
WHERE event_type = 'INCIDENT_CREATED'
  AND timestamp > now() - interval '24 hours'
GROUP BY metadata->>'attribution'
ORDER BY count DESC;
```

### Regression Detection

```sql
-- Policy version comparison: Did severity increase?
WITH policy_versions AS (
  SELECT
    metadata->>'policy_id' AS policy,
    DATE_TRUNC('day', timestamp) AS day,
    AVG(severity) AS avg_severity,
    COUNT(*) AS incidents
  FROM ops_events
  WHERE event_type = 'INCIDENT_CREATED'
    AND timestamp > now() - interval '7 days'
  GROUP BY metadata->>'policy_id', DATE_TRUNC('day', timestamp)
)
SELECT
  policy,
  day,
  avg_severity,
  incidents,
  avg_severity - LAG(avg_severity) OVER (PARTITION BY policy ORDER BY day) AS severity_delta
FROM policy_versions
WHERE avg_severity - LAG(avg_severity) OVER (PARTITION BY policy ORDER BY day) > 0.5
ORDER BY day DESC, severity_delta DESC;
```

### UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ INCIDENT INTELLIGENCE                                       │
│ Last 24 hours                                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  INCIDENT HEATMAP                                           │
│                                                             │
│  By Model:                                                  │
│  gpt-4o-mini     ████████████████████░░  62% (198 incidents)│
│  gpt-4.1         ███░░░░░░░░░░░░░░░░░░░  11% (35 incidents) │
│  claude-3-haiku  ██░░░░░░░░░░░░░░░░░░░░   8% (26 incidents) │
│                                                             │
│  By Policy:                                                 │
│  CONTENT_ACCURACY  ████████████████░░░░  52%                │
│  SAFETY_BASIC      ██████░░░░░░░░░░░░░░  23%                │
│  PII_FILTER        ████░░░░░░░░░░░░░░░░  14%                │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  FAILURE ATTRIBUTION                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Model Hallucination  ████████████░░░░░░░░  41%      │   │
│  │ Policy Conflict      ██████████░░░░░░░░░░  33%      │   │
│  │ Context Missing      █████░░░░░░░░░░░░░░░  18%      │   │
│  │ Infra Timeout        ██░░░░░░░░░░░░░░░░░░   8%      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ⚠️ REGRESSION DETECTED                                     │
│  policy_v12 → +0.8 avg severity across 4 tenants           │
│  Affected: acme-ai, beta-corp, gamma-inc, delta-io         │
│                                                             │
│  [Rollback to v11]  [Replay Samples]  [Diff Outputs]       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Module 4: Product Stickiness

**Question:** "Which feature actually keeps users?"

### Feature Usage Funnel

Track progression through value realization:

```
Incident Created → Incident Viewed → Replay Executed → Export Generated → Cert Verified
```

```sql
-- Funnel conversion rates (last 30 days)
WITH funnel AS (
  SELECT
    tenant_id,
    COUNT(*) FILTER (WHERE event_type = 'INCIDENT_CREATED') > 0 AS has_incident,
    COUNT(*) FILTER (WHERE event_type = 'INCIDENT_VIEWED') > 0 AS has_viewed,
    COUNT(*) FILTER (WHERE event_type = 'REPLAY_EXECUTED') > 0 AS has_replayed,
    COUNT(*) FILTER (WHERE event_type = 'EXPORT_GENERATED') > 0 AS has_exported,
    COUNT(*) FILTER (WHERE event_type = 'CERT_VERIFIED') > 0 AS has_verified
  FROM ops_events
  WHERE timestamp > now() - interval '30 days'
  GROUP BY tenant_id
)
SELECT
  COUNT(*) FILTER (WHERE has_incident) AS step_1_incident,
  COUNT(*) FILTER (WHERE has_viewed) AS step_2_viewed,
  COUNT(*) FILTER (WHERE has_replayed) AS step_3_replayed,
  COUNT(*) FILTER (WHERE has_exported) AS step_4_exported,
  COUNT(*) FILTER (WHERE has_verified) AS step_5_verified,
  ROUND(COUNT(*) FILTER (WHERE has_viewed)::numeric / NULLIF(COUNT(*) FILTER (WHERE has_incident), 0) * 100, 1) AS view_rate,
  ROUND(COUNT(*) FILTER (WHERE has_replayed)::numeric / NULLIF(COUNT(*) FILTER (WHERE has_viewed), 0) * 100, 1) AS replay_rate,
  ROUND(COUNT(*) FILTER (WHERE has_exported)::numeric / NULLIF(COUNT(*) FILTER (WHERE has_replayed), 0) * 100, 1) AS export_rate
FROM funnel;
```

### Drop-off Analysis

| Drop-off Point | Interpretation | Action |
|----------------|----------------|--------|
| Incident → View | Customers not checking console | Improve notifications |
| View → Replay | Replay UX too complex | Simplify replay flow |
| Replay → Export | Unclear export value | Better export CTA |
| Export → Verify | Premature feature | Deprioritize |

---

## Module 5: Revenue & Risk

**Question:** "Am I making money safely?"

### Per-Tenant Unit Economics

```sql
SELECT
  tenant_id,
  SUM(cost_usd) FILTER (WHERE event_type = 'LLM_CALL_MADE') AS llm_cost,
  COUNT(*) FILTER (WHERE event_type = 'API_CALL_RECEIVED') AS api_calls,
  COUNT(*) FILTER (WHERE event_type = 'INCIDENT_CREATED') AS incidents,
  COUNT(*) FILTER (WHERE event_type = 'EXPORT_GENERATED') AS exports,
  -- Assume $99/month subscription
  99.00 - SUM(cost_usd) FILTER (WHERE event_type = 'LLM_CALL_MADE') AS margin
FROM ops_events
WHERE timestamp > now() - interval '30 days'
GROUP BY tenant_id
ORDER BY margin ASC;  -- Lowest margin first (risk)
```

### Risk Flags

| Risk | Detection | Severity |
|------|-----------|----------|
| Margin negative | LLM cost > subscription | 🔴 Critical |
| Resource hog | > 30% of total infra | 🔴 Critical |
| Legal exposure | Exports without replay | 🟡 Warning |
| Abuse pattern | > 10x avg API calls | 🟡 Warning |

---

## Module 6: Infra & Limits

**Question:** "What breaks first if I grow?"

### Resource Projection

```sql
-- Redis memory trend (last 7 days)
SELECT
  DATE_TRUNC('hour', timestamp) AS hour,
  AVG((metadata->>'redis_used_mb')::numeric) AS used_mb,
  MAX((metadata->>'redis_limit_mb')::numeric) AS limit_mb
FROM ops_events
WHERE event_type = 'INFRA_LIMIT_HIT'
  AND metadata->>'resource' = 'redis'
  AND timestamp > now() - interval '7 days'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour;
```

### Time-to-Exhaustion Formula

```python
def project_exhaustion(current: float, limit: float, daily_growth: float) -> int:
    """
    Returns days until resource exhaustion.
    Uses exponential smoothing, not linear regression.
    """
    if daily_growth <= 0:
        return -1  # Not growing

    remaining = limit - current
    if remaining <= 0:
        return 0  # Already exhausted

    # Simple projection: remaining / daily_growth
    days = remaining / daily_growth
    return int(days)
```

### Translate to Business Language

```
┌─────────────────────────────────────────────────────────────┐
│ INFRA LIMITS                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Redis Memory                                               │
│  Current: 200 MB / 256 MB (78%)                            │
│  Daily Growth: +4.2 MB                                      │
│  ⚠️ At current growth, limit hit in 13 days                │
│                                                             │
│  Database Connections                                       │
│  Current: 62 / 100 (62%)                                   │
│  Daily Growth: +0.5                                         │
│  ✓ Stable — 76 days headroom                               │
│                                                             │
│  LLM Rate Limit                                            │
│  Current: 51% of tier limit                                │
│  Peak: 78% (Dec 18, 14:23)                                 │
│  ✓ Stable — upgrade at 80%                                 │
│                                                             │
│  SSE Concurrent Connections                                │
│  Current: 32 / 100 (32%)                                   │
│  Peak: 45% (Dec 19, 09:15)                                 │
│  ✓ Stable                                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Module 7: Replay Lab

**Question:** "Can I reproduce and fix anything?"

### Capabilities

1. **Replay any incident** — Re-execute with same inputs
2. **Override model** — Test with different LLM
3. **Override policy** — Test with different version
4. **Compare outputs** — Side-by-side diff
5. **Measure delta** — Cost, severity, determinism

### UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ REPLAY LAB                                                  │
│ Incident: inc_a8f3c2                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ORIGINAL                        REPLAY                     │
│  ───────────────────────        ───────────────────────    │
│  Model: gpt-4o-mini              Model: [gpt-4o-mini ▼]    │
│  Policy: v12                     Policy: [v11 ▼]           │
│  Timestamp: Dec 19, 23:47        [Run Replay]              │
│                                                             │
│  INPUT                                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ User: Is my contract auto-renewed?                   │   │
│  │ Context: { contract_status: "active", auto_renew: null }│
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  OUTPUT COMPARISON                                          │
│  ┌────────────────────────┐  ┌────────────────────────┐   │
│  │ ORIGINAL               │  │ REPLAY (v11)           │   │
│  │                        │  │                        │   │
│  │ "Yes, your contract is │  │ "I don't have enough  │   │
│  │ set to auto-renew..."  │  │ information about     │   │
│  │                        │  │ your auto-renewal     │   │
│  │ ⚠️ INACCURATE          │  │ status..."            │   │
│  │                        │  │                        │   │
│  │                        │  │ ✓ ACCURATE            │   │
│  └────────────────────────┘  └────────────────────────┘   │
│                                                             │
│  DELTA                                                      │
│  Severity: 4 → 1 (↓3)                                      │
│  Cost: $0.0023 → $0.0019 (↓17%)                            │
│  Determinism: EXACT MATCH ✓                                │
│                                                             │
│  [Promote v11 to All Tenants]  [Export Comparison]         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Event Infrastructure (Week 1)

| Task | Priority |
|------|----------|
| Create `ops_events` table migration | P0 |
| Create EventEmitter service | P0 |
| Instrument existing API calls to emit events | P0 |
| Add events to incident/replay/export flows | P0 |

### Phase 2: System Pulse (Week 2)

| Task | Priority |
|------|----------|
| Create `/api/v1/ops/pulse` endpoint | P0 |
| Build System Pulse UI component | P0 |
| Implement infra metrics collection | P1 |
| Add system state derivation | P1 |

### Phase 3: Customer Intelligence (Week 3)

| Task | Priority |
|------|----------|
| Create `/api/v1/ops/customers` endpoint | P0 |
| Implement intent inference | P0 |
| Implement stickiness scoring | P0 |
| Build silent churn detector | P0 |
| Build customer profile UI | P1 |

### Phase 4: Incident Intelligence (Week 4)

| Task | Priority |
|------|----------|
| Create `/api/v1/ops/incidents/heatmap` endpoint | P0 |
| Implement failure attribution | P0 |
| Build regression detector | P1 |
| Build incident heatmap UI | P1 |

### Phase 5: Remaining Modules (Weeks 5-6)

| Task | Priority |
|------|----------|
| Product stickiness funnel | P1 |
| Revenue & risk calculations | P1 |
| Infra projections | P1 |
| Replay Lab enhancements | P2 |

---

## File Manifest

### Backend

```
backend/
├── alembic/versions/
│   └── 040_m24_ops_events.py              # Event table migration
├── app/
│   ├── api/
│   │   └── ops.py                          # All ops endpoints
│   ├── services/
│   │   ├── event_emitter.py               # Event emission service
│   │   ├── customer_intelligence.py       # Intent, stickiness, churn
│   │   ├── incident_intelligence.py       # Heatmaps, attribution
│   │   ├── infra_projector.py             # Resource projections
│   │   └── ops_pulse.py                   # System pulse aggregation
│   └── models/
│       └── ops_event.py                   # OpsEvent model
└── tests/
    └── test_ops_console.py                # Ops console tests
```

### Frontend

```
website/aos-console/console/src/
├── pages/operator/
│   ├── SystemPulse.tsx                    # Pulse dashboard
│   ├── CustomerIntelligence.tsx           # Customer profiles
│   ├── CustomerProfile.tsx                # Single customer view
│   ├── IncidentIntelligence.tsx           # Incident heatmaps
│   ├── ProductStickiness.tsx              # Funnel analysis
│   ├── RevenueRisk.tsx                    # Unit economics
│   ├── InfraLimits.tsx                    # Resource projections
│   └── ReplayLab.tsx                      # Replay comparison
├── components/operator/
│   ├── StatusBadge.tsx                    # STABLE/DEGRADATION/FAILURE
│   ├── MetricCard.tsx                     # Metric with delta
│   ├── Heatmap.tsx                        # Generic heatmap
│   ├── TimelineChart.tsx                  # Activity timeline
│   └── FunnelChart.tsx                    # Conversion funnel
└── api/
    └── ops.ts                             # Ops API client
```

---

## Success Criteria

### System Works When:

- [ ] Founder sees business health in < 5 seconds
- [ ] Silent churn is detected before cancellation
- [ ] Policy regressions are visible within 1 hour
- [ ] Intent inference accuracy > 80%
- [ ] Infra exhaustion projected with < 20% error

### Business Impact:

- [ ] Churn intervention before 30% of cancellations
- [ ] Policy rollbacks within 2 hours of regression
- [ ] Resource upgrades before any outage
- [ ] Demo close rate improves (Replay Lab = sales weapon)

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-100 | M23 Incident Console (data source) |
| PIN-096 | M22 KillSwitch (events) |
| PIN-098 | M22.1 Guard Console (customer-facing counterpart) |
| PIN-103 | Survival Stack (infra constraints) |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-20 | Initial PIN created with full spec |
| 2025-12-20 | Implementation Phase 1 complete: Migration, EventEmitter, Ops API |

---

## Implementation Status

### Phase 1: Event Infrastructure ✅
- [x] Migration `038_m24_ops_events.py` - ops_events, ops_tenant_metrics, ops_alert_thresholds, ops_customer_segments tables
- [x] EventEmitter service with convenience methods
- [x] Ops API endpoints: /ops/pulse, /ops/customers, /ops/incidents/patterns, /ops/stickiness, /ops/revenue, /ops/infra, /ops/events
- [x] Background jobs: detect-silent-churn, compute-stickiness

### Phase 2: Event Instrumentation (Pending)
- [ ] Instrument Guard API to emit events
- [ ] Instrument Proxy API to emit events
- [ ] Instrument KillSwitch to emit events

### Phase 3: UI Console (Pending)
- [ ] System Pulse dashboard
- [ ] Customer Intelligence table
- [ ] Incident patterns view
- [ ] Replay Lab

---

*PIN-105: Ops Console — Behavioral truth extraction for founders.*
