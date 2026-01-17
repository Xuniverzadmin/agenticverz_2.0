# Activity Domain Audit

**Status:** IMPLEMENTATION READY
**Last Updated:** 2026-01-17
**Reference:** PIN-411 (Unified Facades)

---

## Related Documents (NEW)

| Document | Purpose |
|----------|---------|
| [ACTIVITY_DOMAIN_SQL.md](./ACTIVITY_DOMAIN_SQL.md) | Exact SQL for each endpoint |
| [ACTIVITY_CAPABILITY_REGISTRY.yaml](./ACTIVITY_CAPABILITY_REGISTRY.yaml) | Capability → endpoint mapping |
| [ACTIVITY_DOMAIN_CONTRACT.md](./ACTIVITY_DOMAIN_CONTRACT.md) | CI enforcement rules |
| `scripts/preflight/check_activity_domain.py` | CI enforcement script |

---

## 1. Panel Questions (13 Panels across 3 Topics)

| Topic | O-Level | Panel ID | Panel Question | Status |
|-------|---------|----------|----------------|--------|
| **COMPLETED** | O1 | ACT-LLM-COMP-O1 | How many LLM runs completed in window? | DRAFT |
| | O2 | ACT-LLM-COMP-O2 | How many arranged based on timestamp recency? | DRAFT |
| | O3 | ACT-LLM-COMP-O3 | How many completed critical success/failed/near threshold? | **TODO** |
| | O4 | ACT-LLM-COMP-O4 | Which runs were near cost/time/token limits? | DRAFT |
| | O5 | ACT-LLM-COMP-O5 | Which runs ended early (aborted/cancelled)? | DRAFT |
| **LIVE** | O1 | ACT-LLM-LIVE-O1 | How many runs currently in progress? | DRAFT |
| | O2 | ACT-LLM-LIVE-O2 | How many live runs based on timestamp recency? | **TODO** |
| | O3 | ACT-LLM-LIVE-O3 | Which live runs approaching failure/limits? | DRAFT |
| | O4 | ACT-LLM-LIVE-O4 | Are live runs emitting telemetry/logs/traces? | DRAFT |
| | O5 | ACT-LLM-LIVE-O5 | Distribution of live runs by dimension? | DRAFT |
| **SIGNALS** | O1 | ACT-LLM-SIG-O1 | What's happening right now that matters? | DRAFT |
| | O2 | ACT-LLM-SIG-O2 | Which runs approach policy/cost/failure limits? | DRAFT |
| | O3 | ACT-LLM-SIG-O3 | What patterns indicate instability over time? | DRAFT |
| | O4 | ACT-LLM-SIG-O4 | Where is money being lost/saved unexpectedly? | DRAFT |
| | O5 | ACT-LLM-SIG-O5 | What should we look at first and why? | DRAFT |

---

## 2. Capability Registry (Cleaned)

**Total:** 7 capabilities (after cleanup)
**Deleted:** 11 wrong mappings (discovery, predictions, health, feedback, jobs, agents, tenant, worker, customer)

| Capability | Status | Endpoint | Panel |
|------------|--------|----------|-------|
| `activity.completed_runs` | OBSERVED | `/api/v1/activity/runs` | COMP-O1 |
| `activity.live_runs` | OBSERVED | `/api/v1/activity/runs` | LIVE-O1 |
| `activity.queued_runs` | OBSERVED | `/api/v1/activity/runs` | LIVE-O3 |
| `activity.runs_list` | OBSERVED | `/api/v1/activity/runs` | COMP-O2 |
| `activity.runtime_traces` | OBSERVED | `/api/v1/runtime/traces` | COMP-O5 |
| `activity.signals` | OBSERVED | `/api/v1/activity/runs` | SIG-O1 |
| `activity.summary` | OBSERVED | `/api/v1/activity/summary` | COMP-O2 |

---

## 3. API Routes (Activity Facade)

| Endpoint | Method | Returns | Panels Served |
|----------|--------|---------|---------------|
| `/api/v1/activity/runs` | GET | Runs list with filters | COMP-O1, O2, LIVE-O1, O2, O3, SIG-O1, O2 |
| `/api/v1/activity/runs/{id}` | GET | Run detail | Detail views |
| `/api/v1/activity/runs/{id}/evidence` | GET | Cross-domain impact | COMP-O4 |
| `/api/v1/activity/runs/{id}/proof` | GET | Traces, integrity | COMP-O5 |
| `/api/v1/activity/summary` | GET | Aggregated counts | COMP-O1, O2, O3 |
| `/api/v1/runtime/traces` | GET | Trace records | COMP-O5 |

### Available Filters on `/api/v1/activity/runs`

| Filter | Values | Use Case |
|--------|--------|----------|
| `state` | LIVE, COMPLETED | COMP vs LIVE topics |
| `status` | running, succeeded, failed, aborted, queued, retry | Status breakdown |
| `risk` | true/false | Risk signal filtering |
| `risk_level` | AT_RISK, VIOLATED, NEAR_THRESHOLD, NORMAL | Threshold proximity |
| `latency_bucket` | OK, SLOW, STALLED | Performance signals |
| `evidence_health` | FLOWING, DEGRADED, MISSING | Telemetry status |
| `sort_by` | started_at, completed_at, duration_ms, risk_level | Ordering |
| `sort_order` | asc, desc | Direction |

---

## 4. Panel Coverage Matrix

| Panel | Question | Capability | Route | Status |
|-------|----------|------------|-------|--------|
| COMP-O1 | How many completed? | `activity.completed_runs` | `/activity/runs?state=COMPLETED` | **EXISTS** |
| COMP-O2 | Recent by timestamp? | `activity.runs_list` | `/activity/runs?sort_by=completed_at` | **EXISTS** |
| COMP-O3 | Critical success/failed/threshold? | MISSING | Need `/activity/summary/by-status` | **TODO** |
| COMP-O4 | Near limits? | MISSING | Need threshold query | **TODO** |
| COMP-O5 | Early termination? | `activity.runtime_traces` | `/activity/runs?status=aborted` | **EXISTS** |
| LIVE-O1 | How many live? | `activity.live_runs` | `/activity/runs?state=LIVE` | **EXISTS** |
| LIVE-O2 | Recent live by timestamp? | MISSING | `/activity/runs?state=LIVE&sort_by=started_at` | **EXISTS** (filter combo) |
| LIVE-O3 | Approaching limits? | `activity.queued_runs` | `/activity/runs?state=LIVE&risk=true` | **EXISTS** (filter combo) |
| LIVE-O4 | Emitting telemetry? | MISSING | Need `evidence_health` capability | **PARTIAL** |
| LIVE-O5 | Distribution by dimension? | MISSING | Need groupBy endpoint | **TODO** |
| SIG-O1 | What matters now? | `activity.signals` | `/activity/runs?risk=true` | **EXISTS** |
| SIG-O2 | Approaching limits? | MISSING | Need threshold proximity | **TODO** |
| SIG-O3 | Instability patterns? | MISSING | Need pattern analysis service | **TODO** |
| SIG-O4 | Cost anomalies? | MISSING | Need cost analysis service | **TODO** |
| SIG-O5 | Priority ranking? | MISSING | Need attention algorithm | **TODO** |

---

## 5. Coverage Summary

```
Panels with working capability:    6/13 (46%)
Panels workable with filters:      8/13 (62%)
Panels needing new endpoints:      5/13 (38%)
```

---

## 6. TODO: Missing Implementations

### 6.1 New Endpoints Needed

| Panel | Endpoint | Implementation |
|-------|----------|----------------|
| COMP-O3 | `/api/v1/activity/summary/by-status` | Count by status (succeeded, failed, near_threshold) |
| LIVE-O5 | `/api/v1/activity/runs/by-dimension` | GroupBy provider_type, source, agent |
| SIG-O2 | - | Use existing `risk_level` field |
| SIG-O3 | `/api/v1/activity/patterns` | Pattern analysis on aos_trace_steps |
| SIG-O4 | `/api/v1/activity/cost-analysis` | Cost analysis on worker_runs.cost_cents |
| SIG-O5 | `/api/v1/activity/attention-queue` | Composite scoring algorithm |

### 6.2 New Capabilities Needed

| Capability ID | Panel | Description |
|---------------|-------|-------------|
| `activity.summary_by_status` | COMP-O3 | Status breakdown counts |
| `activity.evidence_health` | LIVE-O4 | Telemetry health status |
| `activity.runs_by_dimension` | LIVE-O5 | Dimension distribution |
| `activity.threshold_signals` | SIG-O2 | Threshold proximity signals |
| `activity.patterns` | SIG-O3 | Instability pattern detection |
| `activity.cost_analysis` | SIG-O4 | Cost anomaly analysis |
| `activity.attention_queue` | SIG-O5 | Priority ranking |

### 6.3 New Services Needed

| Service | Purpose | Data Source |
|---------|---------|-------------|
| PatternDetectionService | Detect instability patterns | `aos_trace_steps` |
| CostAnalysisService | Analyze cost anomalies | `worker_runs.cost_cents` |
| AttentionRankingService | Priority queue scoring | Composite of risk, cost, patterns |

---

## 7. Data Flow

```
SDK.create_run() / SDK.post_goal()
        │
        ▼
   worker_runs table (L6)
        │
        ▼
   v_runs_o2 view (pre-computed risk, latency, evidence)
        │
        ▼
   /api/v1/activity/* (L2 facade)
        │
        ▼
   UI Panel renders data
```

---

## 8. Related Files

| File | Purpose |
|------|---------|
| `backend/app/api/activity.py` | Activity facade (L2) |
| `backend/app/services/activity/customer_activity_read_service.py` | Read service (L4) |
| `backend/app/traces/pg_store.py` | Trace storage (L6) |
| `backend/app/models/tenant.py` | WorkerRun model (L6) |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_activity.*.yaml` | Capabilities |
| `design/l2_1/intents/AURORA_L2_INTENT_ACT-*.yaml` | Panel intents |
| `design/l2_1/ui_plan.yaml` | UI topology |

---

## 9. Cleanup Log

**Date:** 2026-01-16

**Deleted Capabilities (wrong domain):**
- `activity.discovery_list` - Discovery ledger (dev tooling)
- `activity.discovery_stats` - Discovery ledger (dev tooling)
- `activity.predictions_list` - PB-S5 forecasting
- `activity.predictions_summary` - PB-S5 forecasting
- `activity.health_status` - `/health` endpoint (infrastructure)
- `activity.feedback_list` - `/api/v1/feedback` (not runs/traces)
- `activity.jobs_list` - Agent jobs (agent management)
- `activity.live_agents` - Agent management
- `activity.tenant_runs` - Founder console (404)
- `activity.worker_runs` - Specific worker endpoint
- `activity.customer_activity` - Endpoint doesn't exist (404)

**Reason:** These capabilities don't fit the Activity domain which covers runs, traces, and signals.
