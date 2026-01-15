# PIN-411: Aurora + Activity Data Population Upgrade

**Status:** IMPLEMENTED
**Category:** Architecture / Aurora Pipeline / Runtime Projections
**Created:** 2026-01-13
**Updated:** 2026-01-13 (Endpoint implemented)
**Author:** System
**Related:** PIN-370 (SDSR), PIN-352 (L2.1 UI Pipeline), PIN-408 (Aurora Projection Fix)

---

## Summary

Comprehensive implementation plan for upgrading the Aurora L2 pipeline to support **runtime data population** for Activity domain panels. This upgrade extends the compile-time projection system with a runtime layer that queries Neon for O2-O5 order data.

---

## Critical Architectural Clarification (LOCKED)

### O1 Panels Are NOT Data Panels

> **O1 panels do NOT populate O1 data.**
> They are **structural headers + navigation anchors only**.

**O1 panels:**
- Show **header info only** (title, short description, scope)
- May show **static counts / hints only if precomputed**
- Contain **menu / navigation controls**
- Allow drill-down into **O2–O5**

**O1 panels DO NOT:**
- ❌ Query Neon
- ❌ Render tables, lists, cards with live data
- ❌ Depend on runtime APIs

**Mental Model:**
```
O1 = Entry point / Navigation surface
O2+ = Data surfaces (first real data appears at O2)
```

This prevents the common failure mode of turning dashboards into slow, confused, half-data pages.

---

## Domain Separation: Overview vs Activity (LOCKED)

### Overview Domain

**Purpose:** "What needs my attention right now?"

| Characteristic | Value |
|----------------|-------|
| Scope | Cross-domain |
| Volume | Low (curated) |
| Signal | High (opinionated) |
| Mode | Decision-centric |
| Question | "What decisions are pending?" |

### Activity Domain

**Purpose:** "Show me the ground truth of executions"

| Characteristic | Value |
|----------------|-------|
| Scope | Single domain (runs) |
| Volume | High (all executions) |
| Signal | Neutral (factual) |
| Mode | Exploration-centric |
| Question | "Let me explore, slice, and drill" |

> **Activity never competes with Overview.**
> Activity is descriptive and factual, not alarm-driven.

---

## Locked Structure: Activity Domain (FROZEN)

### Domain → Subdomain → Topics

```
Activity (Domain)
└── Runs (Subdomain)
    ├── Live (Topic)
    ├── Completed (Topic)
    └── Risk Signals (Topic)
```

### Subdomain Definition

**Runs** = Every execution, regardless of actor (agent, human, SDK, provider)

### Topic Definitions (Horizontal Tabs)

#### Topic 1: Live

> "Runs that are currently executing or recently active"

**Includes:**
- Running
- Stalled
- At-risk

**Note:** NOT strictly "active only" — last-seen logic applies

#### Topic 2: Completed

> "Runs that reached a terminal state"

**Includes:**
- Succeeded
- Failed
- Aborted

**Scoping:** Time-scoped (today / last 24h / custom)

#### Topic 3: Risk Signals

> "Runs that matter because something crossed a line"

**Includes:**
- Near-threshold
- Violations
- Incidents raised
- Policy drafts generated

**Note:** This topic is **derived**, not a state.

---

## O1 Panels Per Topic (Navigation + Summary Only)

### Activity → Runs → Live (O1 Panels)

| Panel | Content | CTA |
|-------|---------|-----|
| **Live Runs Overview** | `3 Live Runs` | View Live Runs (O2) |
| **Latency Watch** | `1 run > 5 min` | View Slow Runs |
| **Risk-in-Flight** | `1 run at risk` | View At-Risk Runs |
| **Evidence Health** | `Evidence flowing: 100%` | View Evidence Status |

### Activity → Runs → Completed (O1 Panels)

| Panel | Content | CTA |
|-------|---------|-----|
| **Completed Summary** | `9 Completed Runs` | View Completed Runs (O2) |
| **Outcome Breakdown** | `6 Succeeded / 2 Failed / 1 Aborted` | — |
| **Failure Density** | `2 failed in last hour` | View Failed Runs |
| **Terminal Integrity** | `100% integrity verified` | View Proofs |

### Activity → Runs → Risk Signals (O1 Panels)

| Panel | Content | CTA |
|-------|---------|-----|
| **Active Near Threshold** | `1 Active Near Threshold` | View Live Risk |
| **Violations Detected** | `2 Completed Runs Violated` | View Violations |
| **Incidents Raised** | `3 Incidents Raised` | → Incidents (deep link) |
| **Policy Drafts** | `3 Policy Drafts Awaiting` | → Policies → Proposals |

> **Note:** Risk Signals topic **bridges domains** but does not own them.

---

## O1 → O5 API Mapping (Locked)

| Order | Type | Endpoint | Access |
|-------|------|----------|--------|
| **O1** | Static | `ui_projection_lock.json` | All |
| **O2** | List | `/api/v1/runtime/activity/runs?state=LIVE` | All |
| **O2** | List | `/api/v1/runtime/activity/runs?state=COMPLETED` | All |
| **O2** | List | `/api/v1/runtime/activity/runs?risk=true` | All |
| **O3** | Detail | `/api/v1/runtime/activity/runs/{run_id}` | All |
| **O4** | Evidence | `/api/v1/runtime/activity/runs/{run_id}/evidence` | Preflight |
| **O5** | Proof | `/api/v1/runtime/activity/runs/{run_id}/proof` | Preflight |

---

## O2 Runs Table Schema (LOCKED)

> **This is the runtime contract between Aurora and the frontend.**
> One row = one run. No joins required for initial render.
> Everything filterable is a column. Everything expensive deferred to O3+.

### Core Principles

- O2 tables are the **primary mechanical surface**
- Every O3/O4/O5 drill-down **starts from an O2 row**
- Risk Signals topic is **a filtered O2 view**, not a new entity
- Caching, pagination, and latency budgets enforced at O2

### Schema Definition

#### Identity & Scope (Required)

| Column | Type | Notes |
|--------|------|-------|
| `run_id` | UUID | Primary key |
| `tenant_id` | UUID | Tenant isolation |
| `project_id` | UUID | Project scope |
| `is_synthetic` | BOOLEAN | SDSR test data flag |
| `source` | ENUM | `agent`, `human`, `sdk` |
| `provider_type` | ENUM | `openai`, `anthropic`, `internal` |

#### Execution State (Required)

| Column | Type | Notes |
|--------|------|-------|
| `state` | ENUM | `LIVE`, `COMPLETED` |
| `status` | ENUM | `RUNNING`, `SUCCEEDED`, `FAILED`, `ABORTED` |
| `started_at` | TIMESTAMP | Run start time |
| `last_seen_at` | TIMESTAMP | Last activity (for LIVE runs) |
| `completed_at` | TIMESTAMP | NULL for LIVE runs |
| `duration_ms` | INTEGER | NULL until completed |

#### Risk & Health (Derived, Denormalized)

| Column | Type | Notes |
|--------|------|-------|
| `risk_level` | ENUM | `NORMAL`, `NEAR_THRESHOLD`, `AT_RISK`, `VIOLATED` |
| `latency_bucket` | ENUM | `OK`, `SLOW`, `STALLED` |
| `evidence_health` | ENUM | `FLOWING`, `DEGRADED`, `MISSING` |
| `integrity_status` | ENUM | `UNKNOWN`, `VERIFIED`, `DEGRADED`, `FAILED` |

#### Impact Signals (Counts, Not Joins)

| Column | Type | Notes |
|--------|------|-------|
| `incident_count` | INTEGER | Count of incidents caused |
| `policy_draft_count` | INTEGER | Count of policy drafts generated |
| `policy_violation` | BOOLEAN | Has policy violation |

#### Cost / Volume (Future-Proof)

| Column | Type | Notes |
|--------|------|-------|
| `input_tokens` | INTEGER | Token usage |
| `output_tokens` | INTEGER | Token usage |
| `estimated_cost_usd` | DECIMAL(10,4) | Cost estimate |

### Required Indexes (Non-Negotiable)

```sql
-- Primary query patterns
INDEX idx_runs_tenant_state_started (tenant_id, state, started_at DESC);
INDEX idx_runs_tenant_risk (tenant_id, risk_level);
INDEX idx_runs_tenant_status (tenant_id, status);
INDEX idx_runs_tenant_lastseen (tenant_id, last_seen_at);

-- Optional (add when needed)
INDEX idx_runs_tenant_provider (tenant_id, provider_type);
INDEX idx_runs_tenant_source (tenant_id, source);
```

### Topic → Filter Mapping

Each topic is a **filtered O2 view**, not a new endpoint.

#### Live Topic

```http
GET /api/v1/runtime/activity/runs?state=LIVE
```

Optional filters:
- `latency_bucket!=OK` (slow runs)
- `risk_level IN (NEAR_THRESHOLD, AT_RISK)` (at-risk runs)

#### Completed Topic

```http
GET /api/v1/runtime/activity/runs?state=COMPLETED
```

Optional filters:
- `status=FAILED` (failed runs)
- `integrity_status!=VERIFIED` (integrity issues)

#### Risk Signals Topic

```http
GET /api/v1/runtime/activity/runs?risk=true
```

Internally translates to:
```sql
WHERE risk_level != 'NORMAL'
   OR incident_count > 0
   OR policy_violation = true
```

### O1 Panel → O2 Filter Binding

Each O1 panel defines a filter preset, not embedded data:

```json
{
  "panel": "Active Near Threshold",
  "navigate_to": "/activity/runs",
  "filters": {
    "state": "LIVE",
    "risk_level": "NEAR_THRESHOLD"
  }
}
```

### What You Do NOT Do (Hard No)

- ❌ No separate `risk_runs` table
- ❌ No O1 counters querying Neon directly
- ❌ No joins in O2 endpoint
- ❌ No UI-side aggregation logic
- ❌ No topic-specific APIs

---

## Current State Analysis

### Aurora L2 Pipeline Architecture

The Aurora L2 pipeline is a **compile-time UI projection system**:

```
Intent CSV → Pipeline → ui_projection_lock.json → Frontend reads projection
```

**Key Characteristics:**
- 54 panels across 5 domains (Overview, Activity, Incidents, Policies, Logs)
- Compile-time: Never queries Neon at runtime
- Surface-to-Slot Resolution: 52 slots with 1:1 panel mapping
- SDSR Integration: Scenarios inject causes, engines create effects

### Activity Domain Current State

| Intent ID | Order | Purpose | Status |
|-----------|-------|---------|--------|
| ACT-EX-AR-O1 | O1 | Active Runs Summary | UNREVIEWED |
| ACT-EX-AR-O2 | O2 | Active Runs List | UNREVIEWED |
| ACT-EX-CR-O1 | O1 | Completed Runs Summary | UNREVIEWED |
| ACT-EX-CR-O2 | O2 | Completed Runs List | UNREVIEWED |
| ACT-EX-CR-O3 | O3 | Completed Run Detail | UNREVIEWED |
| ACT-EX-RD-O1 | O1 | Run Details Summary | UNREVIEWED |
| ACT-EX-RD-O2 | O2 | Run Steps List | UNREVIEWED |
| ACT-EX-RD-O3 | O3 | Run Step Detail | UNREVIEWED |
| ACT-EX-RD-O4 | O4 | Run Evidence Context | UNREVIEWED |
| ACT-EX-RD-O5 | O5 | Raw Execution Proof | UNREVIEWED |

### Identified Gaps

1. **Missing Slot Metadata**: No `binding` field to indicate STATIC vs RUNTIME
2. **No Runtime APIs**: O2-O5 panels have no backend endpoints to fetch data
3. **No Latency Budgets**: Runtime queries need performance SLAs
4. **No Cache Strategy**: Repeated queries without caching

---

## O1-O5 Order System Contract

### Order Definitions (Epistemic Depth)

| Order | Type | Binding | Renders | Use Case |
|-------|------|---------|---------|----------|
| **O1** | Navigation/Header | STATIC | Header, description, menu buttons | "What can I explore here?" |
| **O2** | Instance List | RUNTIME | Tables, lists, cards | "Show me all runs" |
| **O3** | Entity Detail | RUNTIME | Detail view, timeline | "Explain this run" |
| **O4** | Context/Impact | RUNTIME | Evidence (B/D/G/H taxonomy) | "What else did this affect?" |
| **O5** | Raw Proof | RUNTIME | Traces, logs, integrity | "Show me proof" |

### O1 Panel Structure (Navigation Only)

```
┌─────────────────────────────────────────┐
│  Activity / Runs (O1)                   │
├─────────────────────────────────────────┤
│  Header: "Runs"                         │
│  Description: "Live, completed, and     │
│               risk-signaled executions" │
│                                         │
│  Menu buttons:                          │
│    [Live Runs →]                        │
│    [Completed Runs →]                   │
│    [Risk Signals →]                     │
│                                         │
│  NO DATA. NO TABLES. NO METRICS.        │
└─────────────────────────────────────────┘
```

Each menu click resolves to an O2 panel backed by runtime endpoints.

### Binding Contract

```yaml
slot_binding_contract:
  STATIC:
    applies_to: O1 only
    source: compile_time_projection
    queries_neon: false
    cache: permanent_until_rebuild
    latency: 0ms (pre-computed)
    content_blocks_allowed: [HEADER, NAVIGATION, DESCRIPTION]
    content_blocks_forbidden: [DATA, TABLE, CARD, LIST]

  RUNTIME:
    applies_to: O2, O3, O4, O5
    source: runtime_projection_layer
    queries_neon: true
    cache: ttl_based (configurable)
    latency_budget: p95 < 200ms
    latency_alert: p95 > 150ms (early warning)
```

### Depth Access by Console

| Console | Max Depth | Rationale |
|---------|-----------|-----------|
| Preflight | O5 (full) | Debugging, raw proof access |
| Customer | O3 (detail) | Actionable context, no raw internals |

---

## Implementation Plan

### Phase 1: Slot Metadata Enhancement

**Objective:** Extend slot definitions with binding intent metadata.

**Changes to `ui_projection_lock.json` schema:**

```json
{
  "slot_id": "ACT-EX-AR-O2",
  "panel_id": "panel_active_runs_list",
  "binding": "RUNTIME",
  "latency_budget_ms": 200,
  "cache_ttl_seconds": 30,
  "runtime_endpoint": "/api/v1/runtime/activity/active-runs"
}
```

**Files to Modify:**
- `design/l2_1/ui_contract/ui_projection_lock.json`
- `scripts/tools/ui_projection_builder.py`
- `scripts/tools/surface_to_slot_resolver.py`

**New Schema Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `binding` | enum | YES | `STATIC` or `RUNTIME` |
| `latency_budget_ms` | int | RUNTIME only | p95 latency SLA |
| `cache_ttl_seconds` | int | RUNTIME only | Cache duration |
| `runtime_endpoint` | string | RUNTIME only | Backend API path |

---

### Phase 2: Runtime Projection Layer

**Objective:** Create new namespace `app/runtime_projections/` for O2-O5 APIs.

**Directory Structure:**

```
backend/app/runtime_projections/
├── __init__.py
├── router.py                    # FastAPI router mount
├── activity/
│   ├── __init__.py
│   ├── active_runs.py           # O2: Active runs list
│   ├── completed_runs.py        # O2/O3: Completed runs list + detail
│   ├── run_steps.py             # O2/O3: Run steps list + detail
│   ├── run_evidence.py          # O4: Evidence context
│   └── run_proof.py             # O5: Raw execution proof
├── incidents/
│   └── ... (future)
├── policies/
│   └── ... (future)
└── logs/
    └── ... (future)
```

**Layer Classification:**

```python
# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Runtime data projection for Aurora UI panels
# Callers: Frontend via slot binding
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
```

---

### Phase 3: OpenAPI Specifications (Pre-Implementation)

**Objective:** Define API contracts before implementation.

#### Design Principle: Unified Query Model

Instead of state-encoded paths (`/active-runs`, `/completed-runs`), use a single endpoint with filters:

```
GET /api/v1/runtime/activity/runs?state=LIVE
GET /api/v1/runtime/activity/runs?state=COMPLETED
GET /api/v1/runtime/activity/runs?state=COMPLETED&outcome=FAILED
```

**Why this matters:**
- Prevents endpoint explosion
- Allows future states without new routes
- Keeps filters orthogonal (state, outcome, risk, provider, actor)

#### Path Semantics Clarification

| Path | Order | Meaning |
|------|-------|---------|
| `/runs` | O2 | List of runs (filtered) |
| `/runs/{id}` | O3 | Run detail (summary, state, timeline) |
| `/runs/{id}/steps` | O2 | Execution steps (trace-level, ordered) |
| `/runs/{id}/evidence` | O4 | Governed evidence (taxonomy B/D/G/H) |
| `/runs/{id}/proof` | O5 | Raw traces, logs, integrity proof |

**Important:** `/steps` and `/evidence` are **different things**:
- **`/steps`** = What happened during execution (ordered sequence)
- **`/evidence`** = What this run caused/affected across domains

#### Activity Runtime APIs

**3.1 Runs List (O2) — Canonical Unified Endpoint**

```yaml
/api/v1/runtime/activity/runs:
  get:
    operationId: getRunsList
    tags: [runtime-projections, activity]
    summary: List runs with unified query filters
    parameters:
      - name: tenant_id
        in: query
        required: true
        schema:
          type: string
      - name: project_id
        in: query
        required: false
        schema:
          type: string
      - name: state
        in: query
        description: Run lifecycle state
        schema:
          type: string
          enum: [LIVE, COMPLETED, ALL]
          default: ALL
      - name: outcome
        in: query
        description: Run outcome (only for COMPLETED)
        schema:
          type: array
          items:
            type: string
            enum: [SUCCESS, FAILED, CANCELLED, TIMEOUT]
      - name: risk_level
        in: query
        description: Filter by risk classification
        schema:
          type: array
          items:
            type: string
            enum: [NONE, LOW, MEDIUM, HIGH, CRITICAL]
      - name: since
        in: query
        schema:
          type: string
          format: date-time
      - name: limit
        in: query
        schema:
          type: integer
          default: 50
          maximum: 200
      - name: offset
        in: query
        schema:
          type: integer
          default: 0
    responses:
      200:
        description: Paginated runs list
        content:
          application/json:
            schema:
              type: object
              properties:
                items:
                  type: array
                  items:
                    $ref: '#/components/schemas/RunSummary'
                total:
                  type: integer
                has_more:
                  type: boolean
                filters_applied:
                  type: object
```

**3.2 Run Detail (O3)**

```yaml
/api/v1/runtime/activity/runs/{run_id}:
  get:
    operationId: getRunDetail
    tags: [runtime-projections, activity]
    summary: Run detail with summary, state, and timeline
    parameters:
      - name: run_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
    responses:
      200:
        description: Run detail
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RunDetail'
```

**3.3 Run Steps (O2) — Execution Trace**

```yaml
/api/v1/runtime/activity/runs/{run_id}/steps:
  get:
    operationId: getRunSteps
    tags: [runtime-projections, activity]
    summary: Execution steps (trace-level, ordered sequence)
    description: |
      Returns the ordered sequence of execution steps.
      This is the "what happened" view of the run.
    parameters:
      - name: run_id
        in: path
        required: true
      - name: level_filter
        in: query
        schema:
          type: array
          items:
            type: string
            enum: [info, warning, error, critical]
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                steps:
                  type: array
                  items:
                    $ref: '#/components/schemas/ExecutionStep'
                total_count:
                  type: integer
```

**3.4 Run Evidence (O4) — Cross-Domain Impact**

```yaml
/api/v1/runtime/activity/runs/{run_id}/evidence:
  get:
    operationId: getRunEvidence
    tags: [runtime-projections, activity]
    summary: Governed evidence (taxonomy B/D/G/H)
    description: |
      Returns cross-domain impact and evidence context.
      This is the "what this run caused/affected" view.
      Uses Evidence Architecture v1.1 taxonomy.
    parameters:
      - name: run_id
        in: path
        required: true
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                incidents_caused:
                  type: array
                  description: Category B - Execution-Authored
                  items:
                    $ref: '#/components/schemas/IncidentRef'
                policies_triggered:
                  type: array
                  description: Category G - Governance-Bound
                  items:
                    $ref: '#/components/schemas/PolicyRef'
                decisions_made:
                  type: array
                  description: Category D - Decision-Authored
                  items:
                    $ref: '#/components/schemas/DecisionRef'
                traces_linked:
                  type: array
                  description: Category H - History-Authored
                  items:
                    $ref: '#/components/schemas/TraceRef'
```

**3.5 Run Proof (O5) — Raw Evidence**

```yaml
/api/v1/runtime/activity/runs/{run_id}/proof:
  get:
    operationId: getRunProof
    tags: [runtime-projections, activity]
    summary: Raw execution evidence, logs, payloads
    description: |
      Returns raw traces, logs, and integrity proof.
      Preflight-only depth (Customer Console limited to O3).
    parameters:
      - name: run_id
        in: path
        required: true
      - name: include_payloads
        in: query
        description: Include full request/response payloads
        schema:
          type: boolean
          default: false
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                aos_traces:
                  type: array
                  items:
                    $ref: '#/components/schemas/AosTrace'
                aos_trace_steps:
                  type: array
                  items:
                    $ref: '#/components/schemas/AosTraceStep'
                raw_logs:
                  type: array
                  items:
                    type: string
                integrity:
                  type: object
                  properties:
                    root_hash:
                      type: string
                    verification_status:
                      type: string
                      enum: [VERIFIED, UNVERIFIED, TAMPERED]
```

---

### Phase 4: Frontend Integration

**Objective:** Wire UI panels to runtime endpoints via slot binding.

**Changes to PanelContentRegistry:**

```typescript
// src/components/panels/PanelContentRegistry.tsx

const RUNTIME_BINDINGS: Record<string, RuntimeBinding> = {
  'panel_active_runs_list': {
    endpoint: '/api/v1/runtime/activity/active-runs',
    method: 'GET',
    queryParams: ['tenant_id', 'project_id', 'limit', 'offset'],
    cacheKey: (params) => `active-runs:${params.tenant_id}:${params.project_id}`,
    ttl: 30000, // 30 seconds
  },
  // ... other bindings
};
```

**New Component: RuntimePanelLoader**

```typescript
// src/components/panels/RuntimePanelLoader.tsx

interface RuntimePanelLoaderProps {
  slotId: string;
  panelId: string;
  binding: RuntimeBinding;
  renderContent: (data: unknown) => ReactNode;
}

export function RuntimePanelLoader({
  slotId,
  panelId,
  binding,
  renderContent
}: RuntimePanelLoaderProps) {
  const { data, isLoading, error } = useRuntimeQuery(binding);

  if (isLoading) return <PanelSkeleton />;
  if (error) return <PanelError error={error} />;

  return renderContent(data);
}
```

---

### Phase 5: Performance Safeguards

**Objective:** Ensure runtime queries meet latency SLAs.

**5.1 Materialized Views (Optional)**

For frequently accessed aggregates, consider materialized views:

```sql
-- Activity domain materialized views
CREATE MATERIALIZED VIEW mv_active_runs_summary AS
SELECT
  tenant_id,
  project_id,
  COUNT(*) as active_count,
  MAX(created_at) as latest_start
FROM runs
WHERE status IN ('pending', 'running')
GROUP BY tenant_id, project_id;

CREATE INDEX idx_mv_active_runs ON mv_active_runs_summary(tenant_id, project_id);
```

**5.2 Query Performance Monitoring**

```python
# backend/app/runtime_projections/middleware.py

from functools import wraps
import time
from prometheus_client import Histogram

RUNTIME_QUERY_LATENCY = Histogram(
    'runtime_projection_latency_seconds',
    'Runtime projection query latency',
    ['endpoint', 'slot_id']
)

def monitor_latency(slot_id: str, budget_ms: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000

            RUNTIME_QUERY_LATENCY.labels(
                endpoint=func.__name__,
                slot_id=slot_id
            ).observe(elapsed_ms / 1000)

            if elapsed_ms > budget_ms:
                logger.warning(
                    f"Latency budget exceeded: {slot_id} "
                    f"took {elapsed_ms:.1f}ms (budget: {budget_ms}ms)"
                )

            return result
        return wrapper
    return decorator
```

**5.3 Response Caching**

```python
# backend/app/runtime_projections/cache.py

from aiocache import cached
from aiocache.serializers import JsonSerializer

def runtime_cache(ttl: int, key_builder: Callable):
    return cached(
        ttl=ttl,
        serializer=JsonSerializer(),
        key_builder=key_builder,
        namespace="runtime_projections"
    )
```

---

## Invariants

### INV-AURORA-001: Compile-Time Purity

> O1 slots MUST remain compile-time only. No runtime queries for O1 panels.

### INV-AURORA-002: Runtime Isolation

> Runtime projection endpoints MUST NOT modify state. Read-only operations only.

### INV-AURORA-003: Binding Consistency

> Slot binding type MUST match endpoint availability. RUNTIME slots MUST have valid `runtime_endpoint`.

### INV-AURORA-004: Latency Enforcement

> All RUNTIME queries MUST have `latency_budget_ms` defined. p95 violations MUST be logged.

### INV-AURORA-005: SDSR Compatibility

> Runtime endpoints MUST respect `is_synthetic` and `synthetic_scenario_id` for SDSR test data.

### INV-AURORA-006: O1 Panels Are Non-Data Panels (LOCKED)

> **O1 panels are navigation surfaces, not data surfaces.**

**Rules:**

1. `order: O1` panels:
   - MUST NOT specify `runtime_endpoint`
   - MUST have `binding: STATIC`

2. `content_blocks` in O1 panels:
   - Allowed: `HEADER`, `NAVIGATION`, `DESCRIPTION`
   - Forbidden: `DATA`, `TABLE`, `CARD`, `LIST`

3. Any panel with `binding: RUNTIME`:
   - MUST be `order >= O2`

4. Drill-down from O1:
   - MUST resolve into an O2 topic view
   - MUST NOT reuse the same panel_id

**Enforcement:** If any of these are violated → **compiler error**, not warning.

---

## Compiler Enforcement Rules

The Aurora compiler (`backend/aurora_l2/SDSR_UI_AURORA_compiler.py`) MUST enforce:

```python
# Compiler validation rules
COMPILER_RULES = {
    'O1_STATIC_ONLY': {
        'condition': lambda panel: panel['order'] == 'O1',
        'requirement': lambda panel: panel.get('binding') == 'STATIC',
        'error': 'O1 panels MUST have binding: STATIC',
        'severity': 'ERROR'
    },
    'O1_NO_RUNTIME_ENDPOINT': {
        'condition': lambda panel: panel['order'] == 'O1',
        'requirement': lambda panel: panel.get('runtime_endpoint') is None,
        'error': 'O1 panels MUST NOT specify runtime_endpoint',
        'severity': 'ERROR'
    },
    'O1_NO_DATA_BLOCKS': {
        'condition': lambda panel: panel['order'] == 'O1',
        'requirement': lambda panel: not any(
            block['type'] in ['DATA', 'TABLE', 'CARD', 'LIST']
            for block in panel.get('content_blocks', [])
        ),
        'error': 'O1 panels MUST NOT have DATA/TABLE/CARD/LIST content blocks',
        'severity': 'ERROR'
    },
    'RUNTIME_REQUIRES_O2_PLUS': {
        'condition': lambda panel: panel.get('binding') == 'RUNTIME',
        'requirement': lambda panel: panel['order'] in ['O2', 'O3', 'O4', 'O5'],
        'error': 'RUNTIME binding requires order >= O2',
        'severity': 'ERROR'
    },
    'RUNTIME_REQUIRES_ENDPOINT': {
        'condition': lambda panel: panel.get('binding') == 'RUNTIME',
        'requirement': lambda panel: panel.get('runtime_endpoint') is not None,
        'error': 'RUNTIME binding requires runtime_endpoint',
        'severity': 'ERROR'
    }
}
```

---

## Claude Implementation Guardrails

### What Claude MUST NOT Do

- ❌ Add joins between evidence tables in O2 list APIs
- ❌ Add any Neon queries to Aurora helpers
- ❌ Add client-side filtering for Activity
- ❌ Add conditional UI logic based on "preflight vs console"
- ❌ Add new slots for O2+ data
- ❌ Add `DATA`, `TABLE`, `CARD`, `LIST` blocks to O1 panels
- ❌ Add `runtime_endpoint` to O1 panels

### What Claude MUST Do

- ✅ Keep runtime APIs read-only
- ✅ Enforce auth_context at runtime layer
- ✅ Return empty sets explicitly (never implicit nulls)
- ✅ Treat SDSR runs exactly like real runs (flag only)
- ✅ Keep O1 panels as navigation-only surfaces
- ✅ Use unified query model for list endpoints
- ✅ Validate order vs binding consistency at compile time

---

## Implementation Sequence

```
Phase 1: Slot Metadata Enhancement
├── 1.1 Update ui_projection_lock.json schema
├── 1.2 Modify ui_projection_builder.py
├── 1.3 Validate with existing 54 panels
└── 1.4 Document new schema fields

Phase 2: Runtime Projection Layer
├── 2.1 Create app/runtime_projections/ namespace
├── 2.2 Implement Activity runtime APIs
├── 2.3 Add to FastAPI router
└── 2.4 Write integration tests

Phase 3: OpenAPI Specifications
├── 3.1 Generate OpenAPI spec file
├── 3.2 Review with frontend team
└── 3.3 Lock API contracts

Phase 4: Frontend Integration
├── 4.1 Implement RuntimePanelLoader
├── 4.2 Update PanelContentRegistry
├── 4.3 Wire Activity panels
└── 4.4 E2E testing

Phase 5: Performance Safeguards
├── 5.1 Add latency monitoring
├── 5.2 Implement response caching
├── 5.3 Evaluate materialized views
└── 5.4 Performance baseline report
```

---

## Success Criteria

| Criteria | Metric | Target |
|----------|--------|--------|
| O2-O5 API Coverage | Activity domain APIs | 6/6 implemented |
| Latency SLA | p95 response time | < 200ms |
| Cache Hit Rate | RUNTIME queries | > 70% |
| Test Coverage | Runtime projection tests | > 80% |
| SDSR Compatibility | Synthetic data filtering | 100% |

---

## Artifacts to Create

| Artifact | Location | Purpose |
|----------|----------|---------|
| Runtime Projections OpenAPI | `docs/api/runtime_projections_openapi.yaml` | API contract |
| Activity Runtime Module | `backend/app/runtime_projections/activity/` | Implementation |
| RuntimePanelLoader | `website/app-shell/src/components/panels/` | Frontend component |
| Slot Schema Update | `design/l2_1/ui_contract/` | Projection metadata |
| Performance Baseline | `docs/test_reports/TR-XXX_runtime_perf.md` | Latency benchmarks |

---

## Reference Implementation: Activity Run O1→O5 Walkthrough

**Scenario:** User investigates a failed run that caused an incident.

### O1 — Navigation Surface (Instant, No Neon Query)

**User Action:** Clicks "Activity" in sidebar

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Activity / Runs                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  HEADER: "Runs"                                                             │
│  DESCRIPTION: "Live, completed, and risk-signaled agent executions"         │
│                                                                             │
│  NAVIGATION BUTTONS:                                                        │
│    [Live Runs →]  [Completed Runs →]  [Risk Signals →]                      │
│                                                                             │
│  [NO DATA RENDERED - INSTANT LOAD]                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Projection Payload:**
```json
{
  "panel_id": "ACT-EX-RD-O1",
  "order": "O1",
  "binding": "STATIC",
  "content_blocks": [
    { "type": "HEADER", "components": ["title", "description"] },
    { "type": "NAVIGATION", "components": ["menu_buttons"] }
  ],
  "runtime_endpoint": null
}
```

### O2 — Runs List (First Runtime Query)

**User Action:** Clicks "Completed Runs →"

**API Request:**
```
GET /api/v1/runtime/activity/runs?state=COMPLETED&limit=50&offset=0
```

**API Response:**
```json
{
  "items": [
    {
      "run_id": "run_7f3e2a1b-4c5d-6e7f-8a9b-0c1d2e3f4a5b",
      "agent_name": "Customer Support Agent",
      "status": "FAILED",
      "outcome": "TIMEOUT",
      "risk_level": "HIGH",
      "duration_ms": 205000,
      "step_count": 47,
      "cost_usd": 0.0234,
      "has_incident": true
    }
  ],
  "total": 1847,
  "has_more": true
}
```

### O3 — Run Detail (Entity Projection)

**User Action:** Clicks on failed run

**API Request:**
```
GET /api/v1/runtime/activity/runs/run_7f3e2a1b...
```

**API Response (excerpt):**
```json
{
  "run_id": "run_7f3e2a1b...",
  "execution": {
    "status": "FAILED",
    "outcome": "TIMEOUT",
    "duration_ms": 205000,
    "timeout_budget_ms": 180000
  },
  "quality": {
    "risk_level": "HIGH",
    "risk_factors": ["timeout_exceeded", "retry_exhausted"],
    "error_count": 3
  },
  "incident": {
    "incident_id": "inc_9a8b7c6d...",
    "severity": "P2",
    "status": "OPEN"
  }
}
```

**Customer Console stops here (O3 max depth)**

### O4 — Evidence (Cross-Domain Impact) — Preflight Only

**API Request:**
```
GET /api/v1/runtime/activity/runs/run_7f3e2a1b.../evidence
```

**API Response:**
```json
{
  "incidents_caused": [
    { "incident_id": "inc_9a8b7c6d...", "severity": "P2", "category": "B" }
  ],
  "policies_triggered": [
    { "policy_id": "pol_timeout_budget", "action_taken": "BLOCKED", "category": "G" }
  ],
  "decisions_made": [
    { "decision_type": "RETRY", "output": "Attempt 2/3", "category": "D" },
    { "decision_type": "ABORT", "output": "Run terminated", "category": "D" }
  ]
}
```

### O5 — Proof (Raw Evidence) — Preflight Only

**API Request:**
```
GET /api/v1/runtime/activity/runs/run_7f3e2a1b.../proof?include_payloads=true
```

**API Response:**
```json
{
  "integrity": {
    "root_hash": "sha256:9f86d081884c7d659a2feaa0c55ad015...",
    "verification_status": "VERIFIED",
    "chain_length": 47
  },
  "aos_trace_steps": [
    {
      "sequence": 1, "level": "INFO", "message": "Run started",
      "step_hash": "sha256:e3b0c442..."
    },
    {
      "sequence": 23, "level": "ERROR", "message": "External API timeout",
      "payload": { "error_code": "ETIMEDOUT" }
    },
    {
      "sequence": 47, "level": "CRITICAL", "message": "Timeout budget exceeded",
      "payload": { "exceeded_by_ms": 25000 }
    }
  ]
}
```

### Journey Summary

| Order | Panel | Data Source | Latency | Console Access |
|-------|-------|-------------|---------|----------------|
| O1 | Navigation | Projection (static) | 0ms | All |
| O2 | Runs List | Runtime API | <200ms | All |
| O3 | Run Detail | Runtime API | <200ms | All |
| O4 | Evidence | Runtime API | <200ms | Preflight only |
| O5 | Proof | Runtime API | <200ms | Preflight only |

**Each order answered a different question:**
- O1: "What can I explore here?" → Navigation
- O2: "Show me all completed runs" → List
- O3: "Explain this failed run" → Detail
- O4: "What did this run cause?" → Cross-domain impact
- O5: "Show me the raw proof" → Integrity verification

---

## OpenAPI Specification — `/runs` Endpoint (LOCKED)

This is the **exact** OpenAPI specification for the unified runs endpoint, matching the locked O2 schema.

### Full OpenAPI YAML

```yaml
openapi: 3.1.0
info:
  title: Aurora Runtime Projections - Activity Domain
  version: 1.0.0
  description: |
    Runtime projection APIs for the Activity domain.
    O2-O5 data endpoints backing Aurora UI panels.

servers:
  - url: /api/v1/runtime/activity
    description: Activity domain runtime projections

paths:
  /runs:
    get:
      operationId: listRuns
      summary: List runs with unified query filters
      description: |
        Returns paginated list of runs matching filter criteria.
        This is the canonical O2 endpoint for all Activity domain topics.

        Topic mapping:
        - Live Topic: `?state=LIVE`
        - Completed Topic: `?state=COMPLETED`
        - Risk Signals Topic: `?risk=true`
      tags:
        - activity
        - o2-list
      parameters:
        # Required scope parameters
        - name: tenant_id
          in: query
          required: true
          description: Tenant isolation boundary
          schema:
            type: string
            format: uuid

        - name: project_id
          in: query
          required: false
          description: Project scope (optional narrowing)
          schema:
            type: string
            format: uuid

        # State filters
        - name: state
          in: query
          required: false
          description: Run lifecycle state
          schema:
            type: string
            enum: [LIVE, COMPLETED]

        - name: status
          in: query
          required: false
          description: Run status (can specify multiple)
          schema:
            type: array
            items:
              type: string
              enum: [RUNNING, SUCCEEDED, FAILED, ABORTED]
          style: form
          explode: true

        # Risk filters (for Risk Signals topic)
        - name: risk
          in: query
          required: false
          description: |
            If true, returns runs with risk signals:
            risk_level != NORMAL OR incident_count > 0 OR policy_violation = true
          schema:
            type: boolean
            default: false

        - name: risk_level
          in: query
          required: false
          description: Filter by specific risk level(s)
          schema:
            type: array
            items:
              type: string
              enum: [NORMAL, NEAR_THRESHOLD, AT_RISK, VIOLATED]
          style: form
          explode: true

        # Health filters
        - name: latency_bucket
          in: query
          required: false
          description: Filter by latency classification
          schema:
            type: array
            items:
              type: string
              enum: [OK, SLOW, STALLED]
          style: form
          explode: true

        - name: evidence_health
          in: query
          required: false
          description: Filter by evidence health status
          schema:
            type: array
            items:
              type: string
              enum: [FLOWING, DEGRADED, MISSING]
          style: form
          explode: true

        - name: integrity_status
          in: query
          required: false
          description: Filter by integrity verification status
          schema:
            type: array
            items:
              type: string
              enum: [UNKNOWN, VERIFIED, DEGRADED, FAILED]
          style: form
          explode: true

        # Source filters
        - name: source
          in: query
          required: false
          description: Filter by run source
          schema:
            type: array
            items:
              type: string
              enum: [agent, human, sdk]
          style: form
          explode: true

        - name: provider_type
          in: query
          required: false
          description: Filter by LLM provider
          schema:
            type: array
            items:
              type: string
              enum: [openai, anthropic, internal]
          style: form
          explode: true

        # SDSR filter
        - name: is_synthetic
          in: query
          required: false
          description: |
            Filter by synthetic data flag.
            If not specified, returns both real and synthetic runs.
          schema:
            type: boolean

        # Time filters
        - name: started_after
          in: query
          required: false
          description: Filter runs started after this timestamp
          schema:
            type: string
            format: date-time

        - name: started_before
          in: query
          required: false
          description: Filter runs started before this timestamp
          schema:
            type: string
            format: date-time

        - name: completed_after
          in: query
          required: false
          description: Filter runs completed after this timestamp (COMPLETED only)
          schema:
            type: string
            format: date-time

        - name: completed_before
          in: query
          required: false
          description: Filter runs completed before this timestamp (COMPLETED only)
          schema:
            type: string
            format: date-time

        # Pagination
        - name: limit
          in: query
          required: false
          description: Maximum number of runs to return
          schema:
            type: integer
            default: 50
            minimum: 1
            maximum: 200

        - name: offset
          in: query
          required: false
          description: Number of runs to skip
          schema:
            type: integer
            default: 0
            minimum: 0

        # Sorting
        - name: sort_by
          in: query
          required: false
          description: Field to sort by
          schema:
            type: string
            enum: [started_at, last_seen_at, completed_at, risk_level, duration_ms]
            default: started_at

        - name: sort_order
          in: query
          required: false
          description: Sort direction
          schema:
            type: string
            enum: [asc, desc]
            default: desc

      responses:
        '200':
          description: Paginated list of runs
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RunListResponse'

        '400':
          description: Invalid query parameters
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

        '401':
          description: Authentication required
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

        '403':
          description: Tenant access denied
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /runs/{run_id}:
    get:
      operationId: getRunDetail
      summary: Get run detail (O3)
      description: |
        Returns detailed information about a specific run.
        Includes execution timeline, quality metrics, and incident linkage.
      tags:
        - activity
        - o3-detail
      parameters:
        - name: run_id
          in: path
          required: true
          description: Run identifier
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Run detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RunDetailResponse'
        '404':
          description: Run not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /runs/{run_id}/evidence:
    get:
      operationId: getRunEvidence
      summary: Get run evidence (O4)
      description: |
        Returns cross-domain impact and evidence context.
        Uses Evidence Architecture v1.1 taxonomy (B/D/G/H categories).
        Preflight console only.
      tags:
        - activity
        - o4-evidence
        - preflight-only
      parameters:
        - name: run_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Evidence context
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RunEvidenceResponse'
        '403':
          description: Preflight access required
        '404':
          description: Run not found

  /runs/{run_id}/proof:
    get:
      operationId: getRunProof
      summary: Get run proof (O5)
      description: |
        Returns raw traces, logs, and integrity proof.
        Preflight console only.
      tags:
        - activity
        - o5-proof
        - preflight-only
      parameters:
        - name: run_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - name: include_payloads
          in: query
          required: false
          description: Include full request/response payloads
          schema:
            type: boolean
            default: false
      responses:
        '200':
          description: Raw proof and integrity verification
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RunProofResponse'
        '403':
          description: Preflight access required
        '404':
          description: Run not found

components:
  schemas:
    # ================================================================
    # O2 Run Summary (matches locked schema exactly)
    # ================================================================
    RunSummary:
      type: object
      description: O2 table row - one run summary for list view
      required:
        - run_id
        - tenant_id
        - project_id
        - is_synthetic
        - source
        - provider_type
        - state
        - status
        - started_at
        - risk_level
        - latency_bucket
        - evidence_health
        - integrity_status
      properties:
        # Identity & Scope
        run_id:
          type: string
          format: uuid
          description: Primary key
        tenant_id:
          type: string
          format: uuid
          description: Tenant isolation
        project_id:
          type: string
          format: uuid
          description: Project scope
        is_synthetic:
          type: boolean
          description: SDSR test data flag
        source:
          type: string
          enum: [agent, human, sdk]
          description: Run initiator type
        provider_type:
          type: string
          enum: [openai, anthropic, internal]
          description: LLM provider

        # Execution State
        state:
          type: string
          enum: [LIVE, COMPLETED]
          description: Run lifecycle state
        status:
          type: string
          enum: [RUNNING, SUCCEEDED, FAILED, ABORTED]
          description: Run status
        started_at:
          type: string
          format: date-time
          description: Run start time
        last_seen_at:
          type: string
          format: date-time
          nullable: true
          description: Last activity (for LIVE runs)
        completed_at:
          type: string
          format: date-time
          nullable: true
          description: Completion time (NULL for LIVE runs)
        duration_ms:
          type: integer
          nullable: true
          description: Duration in milliseconds (NULL until completed)

        # Risk & Health (Derived)
        risk_level:
          type: string
          enum: [NORMAL, NEAR_THRESHOLD, AT_RISK, VIOLATED]
          description: Risk classification
        latency_bucket:
          type: string
          enum: [OK, SLOW, STALLED]
          description: Latency classification
        evidence_health:
          type: string
          enum: [FLOWING, DEGRADED, MISSING]
          description: Evidence collection health
        integrity_status:
          type: string
          enum: [UNKNOWN, VERIFIED, DEGRADED, FAILED]
          description: Integrity verification status

        # Impact Signals (Counts)
        incident_count:
          type: integer
          default: 0
          description: Count of incidents caused
        policy_draft_count:
          type: integer
          default: 0
          description: Count of policy drafts generated
        policy_violation:
          type: boolean
          default: false
          description: Has policy violation

        # Cost / Volume
        input_tokens:
          type: integer
          nullable: true
          description: Input token count
        output_tokens:
          type: integer
          nullable: true
          description: Output token count
        estimated_cost_usd:
          type: number
          format: decimal
          nullable: true
          description: Estimated cost in USD

    # ================================================================
    # Response Wrappers
    # ================================================================
    RunListResponse:
      type: object
      required:
        - items
        - total
        - has_more
        - filters_applied
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/RunSummary'
        total:
          type: integer
          description: Total count matching filters
        has_more:
          type: boolean
          description: More results available
        filters_applied:
          type: object
          description: Echo of applied filters
          additionalProperties: true
        pagination:
          type: object
          properties:
            limit:
              type: integer
            offset:
              type: integer
            next_offset:
              type: integer
              nullable: true

    RunDetailResponse:
      type: object
      description: O3 run detail
      required:
        - run
        - execution
        - quality
      properties:
        run:
          $ref: '#/components/schemas/RunSummary'
        execution:
          type: object
          properties:
            step_count:
              type: integer
            timeline:
              type: array
              items:
                type: object
                properties:
                  timestamp:
                    type: string
                    format: date-time
                  event:
                    type: string
                  level:
                    type: string
                    enum: [info, warning, error, critical]
        quality:
          type: object
          properties:
            risk_factors:
              type: array
              items:
                type: string
            error_count:
              type: integer
            warning_count:
              type: integer
        incident:
          type: object
          nullable: true
          properties:
            incident_id:
              type: string
              format: uuid
            severity:
              type: string
            status:
              type: string

    RunEvidenceResponse:
      type: object
      description: O4 evidence context (taxonomy B/D/G/H)
      properties:
        incidents_caused:
          type: array
          description: Category B - Execution-Authored
          items:
            type: object
            properties:
              incident_id:
                type: string
                format: uuid
              severity:
                type: string
              category:
                type: string
                const: B
        policies_triggered:
          type: array
          description: Category G - Governance-Bound
          items:
            type: object
            properties:
              policy_id:
                type: string
              action_taken:
                type: string
              category:
                type: string
                const: G
        decisions_made:
          type: array
          description: Category D - Decision-Authored
          items:
            type: object
            properties:
              decision_type:
                type: string
              output:
                type: string
              category:
                type: string
                const: D
        traces_linked:
          type: array
          description: Category H - History-Authored
          items:
            type: object
            properties:
              trace_id:
                type: string
                format: uuid
              category:
                type: string
                const: H

    RunProofResponse:
      type: object
      description: O5 raw proof
      properties:
        integrity:
          type: object
          required:
            - root_hash
            - verification_status
          properties:
            root_hash:
              type: string
              description: SHA256 hash of trace chain
            verification_status:
              type: string
              enum: [VERIFIED, UNVERIFIED, TAMPERED]
            chain_length:
              type: integer
        aos_traces:
          type: array
          items:
            type: object
            properties:
              trace_id:
                type: string
                format: uuid
              run_id:
                type: string
                format: uuid
              created_at:
                type: string
                format: date-time
        aos_trace_steps:
          type: array
          items:
            type: object
            properties:
              step_id:
                type: string
                format: uuid
              trace_id:
                type: string
                format: uuid
              sequence:
                type: integer
              level:
                type: string
              message:
                type: string
              step_hash:
                type: string
              payload:
                type: object
                nullable: true
        raw_logs:
          type: array
          items:
            type: string

    ErrorResponse:
      type: object
      required:
        - error
        - message
      properties:
        error:
          type: string
          description: Error code
        message:
          type: string
          description: Human-readable message
        details:
          type: object
          additionalProperties: true
```

---

## Risk Computation Rules (LOCKED)

> **Status:** LOCKED
> **Depends On:** O2 schema locked ✅, OpenAPI spec locked ✅
> **Computed:** Upstream (execution finalization / integrity computation)
> **Stored:** Neon (O2 columns)
> **Endpoint:** Read-only (no computation at query time)

---

### Core Principle

> **Risk is a system fact, not a query trick.**
> Risk is computed upstream, stored in Neon, and read by `/runs`.
> No UI inference. No query-time calculation. No fuzzy logic.

---

### Computation Location (WHERE)

| Logic | Location | Timing |
|-------|----------|--------|
| `latency_bucket` | Run finalizer + LIVE heartbeat | On state change |
| `evidence_health` | Evidence capture pipeline | After each step |
| `integrity_status` | Integrity computation worker | At run terminal |
| `risk_level` | Run finalizer | After all inputs ready |

**NOT in:**
- `/runs` endpoint (read-only)
- UI Projection Builder
- Frontend filters
- SQL WHERE clauses

---

### 1️⃣ Latency Bucket (Mechanical)

```python
class LatencyBucket(str, Enum):
    OK = "OK"
    SLOW = "SLOW"
    STALLED = "STALLED"


# Configurable thresholds (from policy or global config)
LATENCY_CONFIG = {
    "default_expected_ms": 60_000,      # 1 minute
    "slow_multiplier": 5,               # 5× expected = SLOW
    "stall_timeout_ms": 120_000,        # 2 minutes no heartbeat = STALLED
}


def compute_latency_bucket(
    run: Run,
    now: datetime,
    expected_latency_ms: int | None = None
) -> LatencyBucket:
    """
    Compute latency bucket based on run state and duration.

    Rules:
    - OK:      duration ≤ expected_latency_ms
    - SLOW:    expected < duration ≤ (expected × slow_multiplier)
    - STALLED: last_seen_at > stall_timeout (LIVE only)
              OR duration > (expected × slow_multiplier) (COMPLETED)

    Inputs:
    - run.state (LIVE | COMPLETED)
    - run.started_at
    - run.last_seen_at (for LIVE runs)
    - run.duration_ms (for COMPLETED runs)
    - expected_latency_ms (from intent/policy, or default)
    """
    expected = expected_latency_ms or LATENCY_CONFIG["default_expected_ms"]
    slow_threshold = expected * LATENCY_CONFIG["slow_multiplier"]

    if run.state == State.LIVE:
        # Check stall first (heartbeat timeout)
        if run.last_seen_at:
            since_last_seen = (now - run.last_seen_at).total_seconds() * 1000
            if since_last_seen > LATENCY_CONFIG["stall_timeout_ms"]:
                return LatencyBucket.STALLED

        # Check elapsed duration
        elapsed_ms = (now - run.started_at).total_seconds() * 1000
    else:
        # COMPLETED: use final duration
        elapsed_ms = run.duration_ms or 0

    if elapsed_ms <= expected:
        return LatencyBucket.OK
    elif elapsed_ms <= slow_threshold:
        return LatencyBucket.SLOW
    else:
        return LatencyBucket.STALLED
```

**Computation Timing:**
- LIVE runs: On heartbeat update (periodic)
- COMPLETED runs: Once at finalization (immutable after)

---

### 2️⃣ Evidence Health (Taxonomy-Aware)

```python
class EvidenceHealth(str, Enum):
    FLOWING = "FLOWING"
    DEGRADED = "DEGRADED"
    MISSING = "MISSING"


def compute_evidence_health(
    run: Run,
    evidence_stats: EvidenceStats
) -> EvidenceHealth:
    """
    Compute evidence health based on capture completeness.

    Uses Evidence Architecture v1.1 taxonomy (B/D/G/H categories).

    Rules:
    - FLOWING:  All expected evidence captured for all steps
                B (Execution) + G (Governance) present
    - DEGRADED: ≥1 capture failure recorded
                OR partial evidence for some steps
    - MISSING:  Expected evidence absent at terminal
                OR no B/G categories captured

    Inputs:
    - evidence_stats.total_steps
    - evidence_stats.steps_with_evidence
    - evidence_stats.capture_failures
    - evidence_stats.categories_present (set of B/D/G/H)
    """
    # Required categories for complete evidence
    REQUIRED_CATEGORIES = {"B", "G"}  # Execution + Governance

    # Terminal run with no evidence = MISSING
    if run.state == State.COMPLETED:
        if evidence_stats.steps_with_evidence == 0:
            return EvidenceHealth.MISSING

        # Check required categories present
        if not REQUIRED_CATEGORIES.issubset(evidence_stats.categories_present):
            return EvidenceHealth.MISSING

    # Any capture failures = DEGRADED
    if evidence_stats.capture_failures > 0:
        return EvidenceHealth.DEGRADED

    # Partial coverage = DEGRADED
    if evidence_stats.total_steps > 0:
        coverage = evidence_stats.steps_with_evidence / evidence_stats.total_steps
        if coverage < 1.0:
            return EvidenceHealth.DEGRADED

    return EvidenceHealth.FLOWING


@dataclass
class EvidenceStats:
    """Evidence statistics for a run."""
    total_steps: int
    steps_with_evidence: int
    capture_failures: int
    categories_present: set[str]  # B, D, G, H
```

**Computation Timing:**
- Updated after each step completion
- Final value locked at run terminal

---

### 3️⃣ Integrity Status (Terminal Only)

```python
class IntegrityStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    VERIFIED = "VERIFIED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


# Configurable threshold
INTEGRITY_THRESHOLD = 0.95  # 95% integrity score required for VERIFIED


def compute_integrity_status(
    run: Run,
    integrity_result: IntegrityResult | None
) -> IntegrityStatus:
    """
    Compute integrity status at run terminal.

    Rules:
    - UNKNOWN:  Run not terminal OR integrity not computed yet
    - VERIFIED: integrity_score = 1.0 (perfect)
    - DEGRADED: integrity_score ≥ threshold (acceptable)
    - FAILED:   integrity_score < threshold OR hash mismatch

    Inputs:
    - run.state
    - integrity_result.score (0.0 - 1.0)
    - integrity_result.hash_valid (bool)
    - integrity_result.chain_complete (bool)

    Immutability:
    - Computed ONCE at terminal
    - NEVER recomputed on read
    - Stored permanently
    """
    # Non-terminal runs are UNKNOWN
    if run.state != State.COMPLETED:
        return IntegrityStatus.UNKNOWN

    # No integrity result yet
    if integrity_result is None:
        return IntegrityStatus.UNKNOWN

    # Hash mismatch = immediate FAILED
    if not integrity_result.hash_valid:
        return IntegrityStatus.FAILED

    # Incomplete chain = FAILED
    if not integrity_result.chain_complete:
        return IntegrityStatus.FAILED

    # Score-based classification
    if integrity_result.score >= 1.0:
        return IntegrityStatus.VERIFIED
    elif integrity_result.score >= INTEGRITY_THRESHOLD:
        return IntegrityStatus.DEGRADED
    else:
        return IntegrityStatus.FAILED


@dataclass
class IntegrityResult:
    """Integrity computation result."""
    score: float           # 0.0 - 1.0
    hash_valid: bool       # Root hash matches
    chain_complete: bool   # All steps present
    root_hash: str         # SHA256
    chain_length: int
```

**Computation Timing:**
- Once at run terminal (COMPLETED/FAILED/ABORTED)
- Triggered by integrity computation worker
- Immutable after computation

---

### 4️⃣ Risk Level (Derived, Deterministic)

```python
class RiskLevel(str, Enum):
    NORMAL = "NORMAL"
    NEAR_THRESHOLD = "NEAR_THRESHOLD"
    AT_RISK = "AT_RISK"
    VIOLATED = "VIOLATED"


def compute_risk_level(
    latency_bucket: LatencyBucket,
    evidence_health: EvidenceHealth,
    integrity_status: IntegrityStatus,
    incident_count: int,
    policy_violation: bool
) -> RiskLevel:
    """
    Compute risk level from derived columns.

    Rules (explicit, no fuzzy logic):

    VIOLATED (highest severity):
      - integrity_status = FAILED
      - OR policy_violation = true

    AT_RISK:
      - latency_bucket = STALLED
      - OR integrity_status = DEGRADED
      - OR incident_count ≥ 1

    NEAR_THRESHOLD:
      - latency_bucket = SLOW
      - OR evidence_health = DEGRADED

    NORMAL (default):
      - latency_bucket = OK
      - AND evidence_health = FLOWING
      - AND integrity_status ∈ {UNKNOWN, VERIFIED}
      - AND incident_count = 0
      - AND policy_violation = false

    Priority: VIOLATED > AT_RISK > NEAR_THRESHOLD > NORMAL
    """
    # VIOLATED: highest severity, check first
    if integrity_status == IntegrityStatus.FAILED:
        return RiskLevel.VIOLATED
    if policy_violation:
        return RiskLevel.VIOLATED

    # AT_RISK: second highest
    if latency_bucket == LatencyBucket.STALLED:
        return RiskLevel.AT_RISK
    if integrity_status == IntegrityStatus.DEGRADED:
        return RiskLevel.AT_RISK
    if incident_count >= 1:
        return RiskLevel.AT_RISK

    # NEAR_THRESHOLD: warning level
    if latency_bucket == LatencyBucket.SLOW:
        return RiskLevel.NEAR_THRESHOLD
    if evidence_health == EvidenceHealth.DEGRADED:
        return RiskLevel.NEAR_THRESHOLD

    # NORMAL: all clear
    return RiskLevel.NORMAL
```

**Priority Order (explicit):**
```
VIOLATED > AT_RISK > NEAR_THRESHOLD > NORMAL
```

**No fuzzy logic. No percentages. No UI inference.**

---

### Computation Flow (End-to-End)

```
Run Started
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  LIVE Run Processing                                        │
│                                                             │
│  On each heartbeat/step:                                    │
│    1. Update last_seen_at                                   │
│    2. Recompute latency_bucket                              │
│    3. Update evidence_health (after evidence capture)       │
│    4. Recompute risk_level                                  │
│    5. WRITE to Neon                                         │
│                                                             │
│  integrity_status = UNKNOWN (always for LIVE)               │
└─────────────────────────────────────────────────────────────┘
    │
    ▼ (Run completes)
    │
┌─────────────────────────────────────────────────────────────┐
│  Run Finalization (TERMINAL)                                │
│                                                             │
│  1. Set state = COMPLETED                                   │
│  2. Set completed_at = now()                                │
│  3. Set duration_ms = completed_at - started_at             │
│  4. Final latency_bucket computation                        │
│  5. Final evidence_health computation                       │
│  6. Trigger integrity computation worker                    │
│     └─> Sets integrity_status (VERIFIED/DEGRADED/FAILED)    │
│  7. Final risk_level computation                            │
│  8. WRITE to Neon (immutable after)                         │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  /runs Endpoint (READ-ONLY)                                 │
│                                                             │
│  • Pure SELECT from Neon                                    │
│  • NO computation at query time                             │
│  • NO derived columns computed in SQL                       │
│  • Filter on pre-computed columns only                      │
└─────────────────────────────────────────────────────────────┘
```

---

### Implementation Location

```
backend/
├── app/
│   ├── domain/
│   │   └── runs/
│   │       ├── risk_computation.py    # ← ALL RISK LOGIC HERE
│   │       │   ├── compute_latency_bucket()
│   │       │   ├── compute_evidence_health()
│   │       │   ├── compute_integrity_status()
│   │       │   └── compute_risk_level()
│   │       │
│   │       └── finalizer.py           # ← CALLS RISK COMPUTATION
│   │
│   ├── workers/
│   │   └── integrity_worker.py        # ← INTEGRITY COMPUTATION
│   │
│   └── runtime_projections/
│       └── activity/
│           └── runs.py                # ← READ-ONLY ENDPOINT
```

---

### Invariants (LOCKED)

| ID | Rule | Enforcement |
|----|------|-------------|
| INV-RISK-001 | Risk computed upstream, not at query time | Code structure |
| INV-RISK-002 | integrity_status computed ONCE at terminal | Finalization guard |
| INV-RISK-003 | No fuzzy logic in risk_level | Explicit conditionals |
| INV-RISK-004 | `/runs` is read-only for derived columns | No UPDATE in endpoint |
| INV-RISK-005 | All thresholds configurable, not hardcoded | Config injection |

---

### Confirmation

> **`/runs` endpoint will be READ-ONLY.**
> All risk columns are pre-computed and stored in Neon.
> Query-time computation is FORBIDDEN.

---

## References

- `design/l2_1/AURORA_L2.md` - Aurora pipeline documentation
- `design/l2_1/ui_contract/ui_projection_lock.json` - Current projection lock
- `backend/aurora_l2/SDSR_UI_AURORA_compiler.py` - Aurora compiler
- `backend/app/api/activity.py` - Legacy activity API
- `docs/governance/SDSR_SYSTEM_CONTRACT.md` - SDSR compatibility rules
- PIN-370 (SDSR), PIN-352 (L2.1 Pipeline), PIN-408 (Aurora Fix)
---

## Updates

### Update (2026-01-13)

## 2026-01-13: O1 Panel Binding Implementation Complete

### Summary

Implemented O1 Activity Panel Binding per PIN-411 specification. O1 panels are now **navigation-only** with instant render (no data fetch).

### Changes Made

| File | Change |
|------|--------|
| `PanelContentRegistry.tsx` | Replaced data-fetching O1 components with navigation-only components |
| `routes/index.tsx` | Added route `/precus/activity/runs` for O2 runs list |
| `pages/activity/RunsListPage.tsx` | **NEW** - O2 runs list page with URL filter support |

### O1 Component Mapping

| Panel ID | Old Component | New Component | Navigation Target |
|----------|--------------|---------------|-------------------|
| ACT-EX-AR-O1 | ActiveRunsSummary (useQuery) | LiveRunsNavigation | `/precus/activity/runs?state=LIVE` |
| ACT-EX-CR-O1 | CompletedRunsSummary (useQuery) | CompletedRunsNavigation | `/precus/activity/runs?state=COMPLETED` |
| ACT-EX-RD-O1 | RunDetailsSummary (useQuery) | RiskSignalsNavigation | `/precus/activity/runs?risk=true` |

### Acceptance Criteria Met

- ✅ O1 panels do NOT fetch data (no useQuery)
- ✅ O1 panels render instantly (no loading spinners)
- ✅ No counts rendered in O1
- ✅ O2 loads data only after navigation
- ✅ Uses runtime API: `GET /api/v1/runtime/activity/runs`

### Issues Faced

1. **O1 panels were data-fetching** - Replaced with nav-only components
2. **No route for O2 runs list** - Added `/precus/activity/runs` route
3. **Missing imports** - Added useNavigate, Activity, CheckCircle, AlertTriangle
4. **Registry name mismatch** - Updated registry to use new component names
5. **Scope warning** - Non-blocking (within budget 9/35)
6. **Tenant ID hardcoded** - Tech debt for auth integration

### Frontend Build Status

```
✓ built in 14.95s
```

### Next Steps

- ~~Wire tenant_id from auth context (currently hardcoded to test tenant)~~ **DONE**
- ~~Test O1 → O2 navigation flow in browser~~ **DONE**
- ~~Add O3/O4/O5 detail views for run inspection~~ **DONE**

---

## 2026-01-13: PIN-411 Closure Tasks Complete

### Summary

Completed 7-task closure list for Activity domain. Activity is now **architecturally finished**.

### Closure Tasks Completed

| Task | Description | Status |
|------|-------------|--------|
| **TASK 1** | Remove tenant_id from frontend | ✅ DONE |
| **TASK 2** | Enforce tenant derivation in backend | ✅ DONE |
| **TASK 3** | Fix scope rule (remove warning) | ✅ DONE |
| **TASK 4** | Lock O2 table UX (pure render) | ✅ DONE |
| **TASK 5** | O3 Detail Page (minimum viable) | ✅ DONE |
| **TASK 6** | Preflight gate for O4/O5 | ✅ DONE |
| **TASK 7** | Remove all SDSR UI special-casing | ✅ DONE |

### Security Invariant Enforced

**Frontend MUST NOT send tenant_id. Backend derives from auth_context.**

- `RunsListPage.tsx`: Removed tenant_id from fetch params
- `runs.py`: Rejects tenant_id if provided (400 error), derives from auth_context

### Files Changed

**Backend:**
- `backend/app/db.py` - Fixed `async_sessionmaker` for SQLAlchemy 2.0+
- `backend/app/runtime_projections/activity/runs.py` - Security guardrail + preflight gate

**Frontend:**
- `src/pages/activity/RunsListPage.tsx` - Removed tenant_id, added credentials: 'include'
- `src/pages/activity/RunDetailPage.tsx` - **NEW** O3 detail page
- `src/routes/index.tsx` - Added O3 route `/precus/activity/runs/:id`
- `src/products/ai-console/pages/activity/ActivityPage.tsx` - Removed SDSR badges/counts
- `src/components/panels/PanelContentRegistry.tsx` - Removed SDSR badges/counts
- `website/app-shell/scripts/ui-hygiene-check.cjs` - Added RunsListPage, RunDetailPage to allowed list

### Activity Domain Final Architecture

```
O1 (Panels)     → Navigation only, zero data fetch
O2 (RunsList)   → Pure render from /api/v1/runtime/activity/runs
O3 (RunDetail)  → Pure render from /api/v1/runtime/activity/runs/:id
O4 (Evidence)   → Preflight only (403 in production)
O5 (Proof)      → Preflight only (403 in production)
```

### Issues Faced During Closure

1. **Async Session Error**: `async_sessionmaker` required for SQLAlchemy 2.0+
2. **Docker Volume Mount**: `runtime_projections/` not mounted, required rebuild
3. **Auth Header Confusion**: Must use X-AOS-Key for API testing, not Bearer token
4. **Session Context Loss**: Re-read files after session compaction
5. **Line Number Drift**: Re-grep after edits to get accurate line numbers

### Acceptance Checklist (All TRUE)

- [x] Frontend sends zero tenant identifiers
- [x] Backend rejects tenant_id in query params (400)
- [x] Backend derives tenant_id from auth_context
- [x] No scope warnings in build
- [x] O1 panels navigation-only, zero data
- [x] O2 table pure render (no client aggregation)
- [x] O3 detail page navigable
- [x] O4/O5 preflight-gated
- [x] SDSR badges removed from UI

### Status

**CLOSED** - Activity domain architecturally finished.
