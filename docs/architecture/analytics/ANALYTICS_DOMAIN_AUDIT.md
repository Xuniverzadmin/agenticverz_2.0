# Analytics Domain Audit

**Status:** ✅ DECLARED (De Jure Backend Domain)
**Last Updated:** 2026-01-17
**Reference:** PIN-411 (Unified Facades), Analytics Domain Declaration v1

> **Domain Declaration (2026-01-17):** Analytics is now a first-class backend domain.
> - Domain: Analytics
> - Subdomain: Statistics
> - Topic v1: Usage (first truth-producing topic)
> - Unified Facade: `/api/v1/analytics/*`
> - Console sidebar: DEFERRED (not missing)
> - Reporting/export: DEFERRED (not missing)

---

## 0. Domain Characteristics

> **Analytics is a DECLARED backend domain with a unified facade.**
> Console sidebar exposure is explicitly deferred, not missing.

**Question Analytics Answers:** "How much am I spending and where?"

**Object Family:**
- Costs (attributed spend)
- Usage (consumption metrics)
- Budgets (limits and thresholds)
- Anomalies (unusual patterns)

**Architecture Status:**
- Backend: ✅ PRODUCTION READY + UNIFIED FACADE
- Console Integration: ⏸️ DEFERRED (not missing)
- Unified Facade: ✅ IMPLEMENTED (`/api/v1/analytics/*`)

---

## 1. Summary Status

| Component | Status | Details |
|-----------|--------|---------|
| **Cost Recording** | ✅ COMPLETE | Full attribution: tenant → user → feature → model |
| **Cost Dashboards** | ✅ COMPLETE | Summary, by-feature, by-user, by-model |
| **Anomaly Detection** | ✅ COMPLETE | M29 engine with severity bands |
| **Budget Management** | ✅ COMPLETE | Tenant/feature/user level budgets |
| **Usage Tracking** | ✅ IMPLEMENTED | `GET /api/v1/analytics/statistics/usage` |
| **Unified Facade** | ✅ IMPLEMENTED | `/api/v1/analytics/*` |
| **Console Sidebar** | ⏸️ DEFERRED | Explicitly deferred (not missing) |
| **Cross-Domain Integration** | ⚠️ PARTIAL | One-way to Overview, no bidirectional |

---

## 2. Domain Status (Constitutional)

### Backend Domain Declaration

| Layer | Status |
|-------|--------|
| Domain existence | ✅ DECLARED |
| Subdomain | ✅ Statistics |
| Topic v1 | ✅ Usage |
| Console sidebar | ⏸️ DEFERRED |
| Reporting/export | ⏸️ DEFERRED |
| Facade API | ✅ IMPLEMENTED |

### Customer Console Sidebar

| Domain | Sidebar | Status |
|--------|---------|--------|
| Overview | ✅ | FROZEN |
| Activity | ✅ | FROZEN |
| Incidents | ✅ | FROZEN |
| Policies | ✅ | FROZEN |
| Logs | ✅ | FROZEN |
| **Analytics** | ⏸️ | **DEFERRED** (backend-first) |

**Note:** Console promotion requires a separate amendment. Backend-first is the correct sequencing.

---

## 3. API Routes

### Unified Facade (v1) - IMPLEMENTED

**File:** `backend/app/api/analytics.py`
**Base Path:** `/api/v1/analytics`

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/analytics/statistics/usage` | GET | Usage statistics (time series) | ✅ IMPLEMENTED |
| `/api/v1/analytics/_status` | GET | Capability probe | ✅ IMPLEMENTED |
| `/api/v1/analytics/health` | GET | Internal health check | ✅ IMPLEMENTED |

### Usage Endpoint Contract

```
GET /api/v1/analytics/statistics/usage
Query: from, to, resolution (hour|day), scope (org|project|env)
Response: { window, totals, series, signals }
```

### Legacy Signal APIs (Latent Providers)

```
/cost/*                    - M26 Cost Intelligence (internal)
/ops/cost/*                - Founder cost overview (ops-only)
/guard/costs/*             - Customer cost guard (DEPRECATED)
/api/v1/overview/costs     - Overview projection
```

**Note:** Legacy APIs remain as internal signal sources. All external consumers should use the unified facade.

### Future Facade Extensions (Declared, Not Implemented)

```
⏸️ /api/v1/analytics/statistics/cost      - Cost topic (rebind existing)
⏸️ /api/v1/analytics/statistics/anomalies - Anomalies topic
⏸️ /api/v1/analytics/reporting/exports    - Reporting topic
```

---

## 4. Capability Registry

**Total Capabilities:** 6
**Status:** 5 OBSERVED, 1 DECLARED

| Capability | Endpoint | Panel ID | Status |
|------------|----------|----------|--------|
| `analytics.usage` | `/api/v1/analytics/statistics/usage` | ANL-STAT-USG-O1 | DECLARED |
| `analytics.tenant_usage` | `/api/v1/tenant/usage` | ANL-USG-SUM-O1 | DEPRECATED |
| `analytics.cost_summary` | `/cost/dashboard` | ANL-CST-SUM-O1 | OBSERVED |
| `analytics.cost_by_actor` | `/cost/by-user` | ANL-CST-ACT-O1 | OBSERVED |
| `analytics.cost_by_model` | `/cost/by-model` | ANL-CST-MOD-O1 | OBSERVED |
| `analytics.anomaly_detection` | `/cost/anomalies` | ANL-CST-ANM-O1 | OBSERVED |

### Capability Notes

| Capability | Notes |
|------------|-------|
| `analytics.usage` | New unified facade endpoint, awaiting E2E validation |
| `analytics.tenant_usage` | Deprecated - replaced by `analytics.usage` |

---

## 5. Database Schema

### Tables (Migrations 046, 047)

| Table | Purpose | Status |
|-------|---------|--------|
| `cost_records` | Cost attribution records | ✅ ACTIVE |
| `cost_budgets` | Budget definitions | ✅ ACTIVE |
| `cost_anomalies` | Detected anomalies | ✅ ACTIVE |
| `feature_tags` | Feature tag registry | ✅ ACTIVE |
| `cost_snapshots` | Historical baselines (M27) | ✅ ACTIVE |
| `usage_records` | Usage tracking | ❌ MISSING |

### cost_records Schema

```python
class CostRecord(SQLModel):
    id: str
    tenant_id: str (FK → Tenant)
    user_id: str (FK → User)

    # Attribution
    feature_tag: str           # "customer_support.chat"
    request_id: str
    workflow_id: str
    skill_id: str
    model: str                 # "claude-3-opus"

    # Metrics
    input_tokens: int
    output_tokens: int
    cost_cents: int

    # Timestamps
    created_at: datetime
```

### cost_anomalies Schema

```python
class CostAnomaly(SQLModel):
    id: str
    tenant_id: str (FK → Tenant)

    # Detection
    anomaly_type: str          # ABSOLUTE_SPIKE | SUSTAINED_DRIFT | BUDGET_WARNING | BUDGET_EXCEEDED
    severity: str              # LOW | MEDIUM | HIGH
    entity_type: str           # tenant | feature | user
    entity_id: str

    # Resolution
    detected_at: datetime
    resolved: bool
    resolved_at: datetime

    # Cross-domain
    incident_id: str (FK → Incident)  # M25 escalation link
```

---

## 6. Services (L4 Domain Engine)

| Service | File | Lines | Role |
|---------|------|-------|------|
| CostWriteService | `cost_write_service.py` | 181 | CRUD for tags, records, budgets |
| CostAnomalyDetector | `cost_anomaly_detector.py` | 1,100+ | M29 anomaly detection engine |
| CostModelEngine | `cost_model_engine.py` | 400+ | Cost calculation, token pricing |

### Anomaly Detection Rules (M29)

| Type | Condition | Severity Bands |
|------|-----------|----------------|
| **ABSOLUTE_SPIKE** | daily_spend > baseline × 1.4 for 2 consecutive days | LOW: +15-25%, MEDIUM: +25-40%, HIGH: >40% |
| **SUSTAINED_DRIFT** | 7d rolling avg > baseline_7d × 1.25 for ≥3 days | Same bands |
| **BUDGET_WARNING** | spend > budget × 0.8 | Always MEDIUM |
| **BUDGET_EXCEEDED** | spend > budget | Always HIGH |

### M25 Escalation

HIGH/CRITICAL anomalies can trigger incident loop via `/cost/anomalies/detect` endpoint (manual trigger, not automatic).

---

## 7. Provenance Envelope Pattern

All interpretation panels include provenance:

```python
class AnalyticsProvenance(BaseModel):
    sources: List[str]        # ["cost_records", "feature_tags"]
    window: str               # "24h" | "7d" | "30d"
    aggregation: str          # "SUM" | "GROUP_BY:user" | "DETECT:anomaly"
    generated_at: datetime
```

**Why:** SDSR requires data provenance for UI interpretation panels (distinguishes raw facts from derived insights).

---

## 8. Cross-Domain Integration

### Data Flow Map

```
ANALYTICS
    │
    ├──────────────────────────► OVERVIEW
    │   cost_records             /api/v1/overview/costs
    │   cost_anomalies           cost panels in highlights
    │
    ├──────────────────────────► ACTIVITY
    │   WorkerRun.cost_cents     (populated from cost_records)
    │   ◄── NO REVERSE LINK
    │
    ├──────────────────────────► INCIDENTS
    │   CostAnomaly.incident_id  (M25 escalation)
    │   ONE-WAY: anomaly → incident
    │   ◄── Incident doesn't list related anomalies
    │
    ├──────────────────────────► POLICIES
    │   CostBudget (independent)
    │   ◄── NO policy enforcement of budgets
    │
    └──────────────────────────► LOGS
        Audit trail of cost changes
        ◄── No cost-specific audit queries
```

### Integration Gaps

| Flow | Implemented | Gap |
|------|-------------|-----|
| Run → Cost Record | ✅ YES | - |
| Cost Anomaly → Incident | ⚠️ PARTIAL | Manual trigger only, not automatic |
| Policy → Cost Limit | ❌ NO | Budgets exist but policies can't enforce |
| Incident → Cost Investigation | ❌ NO | No reverse link in UI |
| Logs → Cost Audit | ❌ NO | No cost-specific audit queries |

---

## 9. SDSR Verification

| Scenarios | Status |
|-----------|--------|
| SDSR-ANL-CST-SUM-001 | ✅ PASSING |
| SDSR-ANL-CST-FEA-001 | ✅ PASSING |
| SDSR-ANL-CST-USR-001 | ✅ PASSING |
| SDSR-ANL-CST-MOD-001 | ✅ PASSING |
| SDSR-ANL-CST-ANM-001 | ✅ PASSING |
| SDSR-ANL-USG-SUM-001 | ❌ FAILING (endpoint missing) |

**Last Run:** 2026-01-15

---

## 10. Coverage Summary

```
Backend Implementation:       90% COMPLETE
  - Cost Recording:           ✅ COMPLETE
  - Cost Dashboards:          ✅ COMPLETE
  - Anomaly Detection:        ✅ COMPLETE
  - Budget Management:        ✅ COMPLETE
  - Usage Tracking:           ✅ IMPLEMENTED (v1)
  - Reporting/Export:         ⏸️ DEFERRED

Console Integration:          25% COMPLETE (DEFERRED)
  - Sidebar Domain:           ⏸️ DEFERRED
  - Dedicated Page:           ⏸️ DEFERRED
  - Overview Panels:          ✅ EMBEDDED

API Architecture:             75% COMPLETE
  - Unified Facade:           ✅ IMPLEMENTED
  - Consistent Auth:          ✅ UNIFIED (via facade)
  - Cross-Domain Links:       ⚠️ PARTIAL

Lifecycle Operations:         30% COMPLETE
  - Create:                   ✅ IMPLEMENTED
  - Read:                     ✅ IMPLEMENTED
  - Update:                   ⚠️ PARTIAL (tags only)
  - Delete/Archive:           ⏸️ DEFERRED
  - Reconcile:                ⏸️ DEFERRED
  - Export:                   ⏸️ DEFERRED
```

---

## 11. TODO: Remaining Work

### 11.1 Unified Analytics Facade - ✅ COMPLETE

```
Implemented:
✅ GET /api/v1/analytics/statistics/usage  - Usage tracking
✅ GET /api/v1/analytics/_status           - Capability probe

Next extensions (when usage stabilizes):
⏸️ GET /api/v1/analytics/statistics/cost      - Cost topic (rebind existing)
⏸️ GET /api/v1/analytics/statistics/anomalies - Anomalies topic
⏸️ GET /api/v1/analytics/reporting/exports    - Reporting topic
```

### 11.2 Usage Tracking - ✅ COMPLETE

Usage tracking is now implemented via the unified facade:
- Endpoint: `GET /api/v1/analytics/statistics/usage`
- Signal sources: cost_records, llm.usage, worker.execution
- Time series with reconciliation across sources

### 11.3 Automatic Incident Creation (DEFERRED)

```
Current: Manual trigger via /cost/anomalies/detect
Missing: Automatic incident on budget threshold

Needed:
1. Background job to check budget thresholds
2. Auto-create incident when spend > budget × threshold
3. Link incident_id to cost_anomaly record
4. Bidirectional UI link (incident ↔ anomaly)
```

### 11.4 Reporting & Export (MEDIUM PRIORITY)

```
GET /api/v1/analytics/reports/monthly
Response: PDF or JSON billing report

POST /api/v1/analytics/export
Request: { format: "csv"|"json", date_range, filters }
Response: { download_url, expires_at }
```

### 11.5 Policy-Driven Cost Limits (LOW PRIORITY)

```
Integration needed:
1. PolicyRule can reference CostBudget
2. Runtime enforces cost limits (block run if budget exceeded)
3. Cost impact analysis before policy changes
```

---

## 12. Console Integration Plan

### Current State

```
┌─────────────────────────────┐
│ CORE LENSES (Sidebar)       │
│   Overview ◄─── cost panels embedded here
│   Activity                  │
│   Incidents                 │
│   Policies                  │
│   Logs                      │
└─────────────────────────────┘
```

### Proposed State

```
┌─────────────────────────────┐
│ CORE LENSES (Sidebar)       │
│   Overview                  │
│   Activity                  │
│   Incidents                 │
│   Policies                  │
│   Logs                      │
│   Analytics ◄─── NEW DOMAIN │
│     ▸ Cost Intelligence     │
│     ▸ Usage                 │
│     ▸ Budgets               │
│     ▸ Reports               │
└─────────────────────────────┘
```

### Decision Required

| Option | Description | Impact |
|--------|-------------|--------|
| A | Keep Analytics embedded in Overview | Minimal change, less visibility |
| B | Promote Analytics to 6th sidebar domain | Full visibility, constitutional amendment needed |
| C | Create Analytics as Connectivity subsection | Middle ground |

---

## 13. Related Files

| File | Purpose | Layer |
|------|---------|-------|
| `backend/app/api/cost_intelligence.py` | Cost API routes | L2 |
| `backend/app/services/cost_write_service.py` | Cost CRUD | L4 |
| `backend/app/services/cost_anomaly_detector.py` | Anomaly engine | L4 |
| `backend/app/services/cost_model_engine.py` | Cost calculation | L4 |
| `backend/app/models/cost_records.py` | Cost models | L6 |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_analytics.*.yaml` | Capabilities |
| `design/l2_1/intents/AURORA_L2_INTENT_ANL-*.yaml` | Panel intents |

---

## 14. Implementation Status

**Date:** 2026-01-16

### Backend: Grade B+

| Component | Status |
|-----------|--------|
| Cost Recording | ✅ COMPLETE |
| Cost Attribution | ✅ COMPLETE |
| Cost Dashboards | ✅ COMPLETE |
| Anomaly Detection (M29) | ✅ COMPLETE |
| Budget Management | ✅ COMPLETE |
| M25 Escalation | ✅ COMPLETE |
| Usage Tracking | ❌ MISSING |
| Reporting | ❌ MISSING |
| Export | ❌ MISSING |

### Console: Grade D

| Component | Status |
|-----------|--------|
| Sidebar Domain | ❌ MISSING |
| Dedicated Page | ❌ MISSING |
| Overview Integration | ✅ EMBEDDED |
| Cost Panels | ✅ WORKING |
| Usage Panels | ❌ MISSING |

### Architecture: Grade C

| Component | Status |
|-----------|--------|
| Unified Facade | ❌ MISSING |
| Consistent Auth | ⚠️ FRAGMENTED |
| Cross-Domain Links | ⚠️ PARTIAL |
| SDSR Scenarios | ✅ 5/6 PASSING |
| Capability Registry | ✅ 5 OBSERVED |

---

## 15. Overall Assessment

| Aspect | Grade | Notes |
|--------|-------|-------|
| **Backend Implementation** | A- | Cost intelligence + unified facade |
| **Console Integration** | ⏸️ | Explicitly deferred (backend-first) |
| **API Architecture** | B+ | Unified facade implemented |
| **Cross-Domain** | C | One-way flow, bidirectional ready |
| **Usage Tracking** | B | Implemented via unified facade |
| **Reporting** | ⏸️ | Deferred |

**Resolution (2026-01-17):** Analytics is now a **declared backend domain** with a unified facade.

**Decision:** Backend-first implementation chosen.
- Analytics is a constitutional backend domain
- Console sidebar promotion requires separate amendment
- Reporting/export explicitly deferred

**What Was Fixed:**
1. ✅ "Usage Tracking = F" → Now implemented (read-only v1)
2. ✅ Fragmented APIs → Unified facade enforced
3. ✅ Hidden analytics → Now formally declared
4. ✅ Cross-domain blind spot → Bidirectional ready

**Explicit Non-Goals (v1):**
- ❌ Sidebar entry
- ❌ CSV / export
- ❌ Budget incidents
- ❌ Write-path ingestion
- ❌ Customer-visible dashboards

These come **after** usage truth is stable.
