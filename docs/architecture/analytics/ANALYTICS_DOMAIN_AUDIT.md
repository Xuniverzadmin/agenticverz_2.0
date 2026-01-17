# Analytics Domain Audit

**Status:** ✅ LIVE (De Jure Console Domain)
**Last Updated:** 2026-01-17
**Reference:** PIN-411 (Unified Facades), Analytics Domain Declaration v1

> **HARD COMMIT (2026-01-17):** Analytics is now a first-class, visible console domain.
> - Domain: Analytics (6th primary domain)
> - Subdomain: Statistics
> - Topic v1: Usage (first truth-producing topic)
> - **Topic v2: Cost (spend tracking with breakdowns)**
> - Unified Facade: `/api/v1/analytics/*`
> - Console sidebar: ✅ LIVE
> - Reporting/export: ✅ LIVE (CSV/JSON)

---

## 0. Domain Characteristics

> **Analytics is a LIVE console domain with a unified facade and export capabilities.**

**Question Analytics Answers:** "How much am I spending and where?"

**Object Family:**
- Costs (attributed spend)
- Usage (consumption metrics)
- Budgets (limits and thresholds)
- Anomalies (unusual patterns)

**Architecture Status:**
- Backend: ✅ PRODUCTION READY
- Console Integration: ✅ LIVE (6th sidebar domain)
- Unified Facade: ✅ IMPLEMENTED (`/api/v1/analytics/*`)
- Export: ✅ LIVE (CSV/JSON)

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
| **Console Sidebar** | ✅ LIVE | 6th primary domain |
| **Reporting/Export** | ✅ LIVE | CSV and JSON export endpoints |
| **Cross-Domain Integration** | ⚠️ PARTIAL | One-way to Overview, no bidirectional |

---

## 2. Domain Status (Constitutional)

### Backend Domain Declaration

| Layer | Status |
|-------|--------|
| Domain existence | ✅ LIVE |
| Subdomain | ✅ Statistics |
| Topic v1 | ✅ Usage |
| Console sidebar | ✅ LIVE (6th domain) |
| Reporting/export | ✅ LIVE (CSV/JSON) |
| Facade API | ✅ IMPLEMENTED |

### Customer Console Sidebar

| Domain | Position | Status |
|--------|----------|--------|
| Overview | 1 | FROZEN |
| Activity | 2 | FROZEN |
| Incidents | 3 | FROZEN |
| Policies | 4 | FROZEN |
| Logs | 5 | FROZEN |
| **Analytics** | **6** | **LIVE** |
| Account | 7 | FROZEN |
| Connectivity | 8 | FROZEN |

---

## 3. API Routes

### Unified Facade (v1) - LIVE

**File:** `backend/app/api/analytics.py`
**Base Path:** `/api/v1/analytics`

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/analytics/statistics/usage` | GET | Usage statistics (time series) | ✅ LIVE |
| `/api/v1/analytics/statistics/usage/export.csv` | GET | CSV export | ✅ LIVE |
| `/api/v1/analytics/statistics/usage/export.json` | GET | JSON export | ✅ LIVE |
| `/api/v1/analytics/statistics/cost` | GET | Cost statistics (spend + breakdowns) | ✅ LIVE |
| `/api/v1/analytics/statistics/cost/export.csv` | GET | Cost CSV export | ✅ LIVE |
| `/api/v1/analytics/statistics/cost/export.json` | GET | Cost JSON export | ✅ LIVE |
| `/api/v1/analytics/_status` | GET | Capability probe | ✅ LIVE |
| `/api/v1/analytics/health` | GET | Internal health check | ✅ LIVE |

### Usage Endpoint Contract

```
GET /api/v1/analytics/statistics/usage
Query: from, to, resolution (hour|day), scope (org|project|env)
Response: { window, totals, series, signals }
```

### Cost Endpoint Contract

```
GET /api/v1/analytics/statistics/cost
Query: from, to, resolution (hour|day), scope (org|project|env)
Response: { window, totals, series, by_model, by_feature, signals }
```

### Export Endpoint Contract (Usage CSV)

```
GET /api/v1/analytics/statistics/usage/export.csv
Header: timestamp,requests,compute_units,tokens
Content-Type: text/csv
```

### Export Endpoint Contract (Cost CSV)

```
GET /api/v1/analytics/statistics/cost/export.csv
Header: timestamp,spend_cents,requests,input_tokens,output_tokens
Content-Type: text/csv
```

### OpenAPI Specification

**File:** `docs/api/analytics_openapi_v1.yaml`

### Signal Reconciliation Rules

**File:** `docs/architecture/analytics/SIGNAL_RECONCILIATION_RULES_V1.md`

---

## 4. Console Routing

### Routes

| Path | Component | Purpose |
|------|-----------|---------|
| `/precus/analytics` | AnalyticsPage | Landing page (usage summary) |
| `/precus/analytics/statistics/usage` | UsagePage | Detailed usage table |
| `/precus/analytics/statistics/cost` | CostPage | Cost statistics with breakdowns |

### Sidebar Hierarchy

```
Analytics (bar-chart icon)
 └─ Statistics
     ├─ Usage
     └─ Cost
```

---

## 5. Capability Registry

**Total Capabilities:** 11
**Status:** 10 OBSERVED, 1 DEPRECATED

| Capability | Endpoint | Panel ID | Status |
|------------|----------|----------|--------|
| `analytics.usage` | `/api/v1/analytics/statistics/usage` | ANL-STAT-USG-O1 | OBSERVED |
| `analytics.usage.export.csv` | `/api/v1/analytics/statistics/usage/export.csv` | ANL-STAT-USG-O2 | OBSERVED |
| `analytics.usage.export.json` | `/api/v1/analytics/statistics/usage/export.json` | ANL-STAT-USG-O2 | OBSERVED |
| `analytics.cost` | `/api/v1/analytics/statistics/cost` | ANL-STAT-CST-O1 | OBSERVED |
| `analytics.cost.export.csv` | `/api/v1/analytics/statistics/cost/export.csv` | ANL-STAT-CST-O1 | OBSERVED |
| `analytics.cost.export.json` | `/api/v1/analytics/statistics/cost/export.json` | ANL-STAT-CST-O1 | OBSERVED |
| `analytics.tenant_usage` | `/api/v1/tenant/usage` | ANL-USG-SUM-O1 | DEPRECATED |
| `analytics.cost_summary` | `/cost/dashboard` | ANL-CST-SUM-O1 | OBSERVED |
| `analytics.cost_by_actor` | `/cost/by-user` | ANL-CST-ACT-O1 | OBSERVED |
| `analytics.cost_by_model` | `/cost/by-model` | ANL-CST-MOD-O1 | OBSERVED |
| `analytics.anomaly_detection` | `/cost/anomalies` | ANL-CST-ANM-O1 | OBSERVED |

---

## 6. Database Schema

### Tables (Migrations 046, 047)

| Table | Purpose | Status |
|-------|---------|--------|
| `cost_records` | Cost attribution records | ✅ ACTIVE |
| `cost_budgets` | Budget definitions | ✅ ACTIVE |
| `cost_anomalies` | Detected anomalies | ✅ ACTIVE |
| `feature_tags` | Feature tag registry | ✅ ACTIVE |
| `cost_snapshots` | Historical baselines (M27) | ✅ ACTIVE |

### Signal Sources for Usage

| Signal | Table | Semantic |
|--------|-------|----------|
| `cost_records` | cost_records | Token consumption |
| `llm.usage` | runs | LLM execution count |
| `worker.execution` | aos_traces | Worker execution count |
| `gateway.metrics` | (derived) | API request count |

---

## 7. Services (L4 Domain Engine)

| Service | File | Lines | Role |
|---------|------|-------|------|
| CostWriteService | `cost_write_service.py` | 181 | CRUD for tags, records, budgets |
| CostAnomalyDetector | `cost_anomaly_detector.py` | 1,100+ | M29 anomaly detection engine |
| CostModelEngine | `cost_model_engine.py` | 400+ | Cost calculation, token pricing |

### Signal Adapters (analytics.py)

| Adapter | Source | Output |
|---------|--------|--------|
| `fetch_cost_metrics` | cost_records | requests, tokens |
| `fetch_llm_usage` | runs | requests, tokens |
| `fetch_worker_execution` | aos_traces | compute_units |
| `fetch_gateway_metrics` | (derived) | requests |

---

## 8. Coverage Summary

```
Backend Implementation:       98% COMPLETE
  - Cost Recording:           ✅ COMPLETE
  - Cost Dashboards:          ✅ COMPLETE
  - Cost Statistics:          ✅ LIVE (via facade)
  - Anomaly Detection:        ✅ COMPLETE
  - Budget Management:        ✅ COMPLETE
  - Usage Tracking:           ✅ IMPLEMENTED (v1)
  - Reporting/Export:         ✅ LIVE (CSV/JSON for Usage + Cost)

Console Integration:          90% COMPLETE
  - Sidebar Domain:           ✅ LIVE
  - Landing Page:             ✅ LIVE
  - Usage Page:               ✅ LIVE
  - Cost Page:                ✅ LIVE
  - Export Buttons:           ✅ LIVE
  - Overview Panels:          ✅ EMBEDDED

API Architecture:             98% COMPLETE
  - Unified Facade:           ✅ IMPLEMENTED
  - Export Endpoints:         ✅ LIVE (Usage + Cost)
  - Cost Endpoints:           ✅ LIVE
  - Consistent Auth:          ✅ UNIFIED (via facade)
  - Cross-Domain Links:       ⚠️ PARTIAL

Lifecycle Operations:         65% COMPLETE
  - Create:                   ✅ IMPLEMENTED
  - Read:                     ✅ IMPLEMENTED (Usage + Cost)
  - Update:                   ⚠️ PARTIAL (tags only)
  - Delete/Archive:           ⏸️ DEFERRED
  - Reconcile:                ✅ IMPLEMENTED
  - Export:                   ✅ LIVE
```

---

## 9. Implementation Files

### Backend

| File | Purpose | Status |
|------|---------|--------|
| `backend/app/api/analytics.py` | Unified facade API | ✅ LIVE |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_analytics.usage.yaml` | Capability registration | ✅ LIVE |
| `docs/api/analytics_openapi_v1.yaml` | OpenAPI specification | ✅ LIVE |
| `docs/architecture/analytics/SIGNAL_RECONCILIATION_RULES_V1.md` | Reconciliation rules | ✅ LIVE |

### Frontend

| File | Purpose | Status |
|------|---------|--------|
| `website/app-shell/src/contracts/ui_projection_types.ts` | Analytics DomainName | ✅ LIVE |
| `website/app-shell/src/components/layout/ProjectionSidebar.tsx` | Analytics icon (BarChart2) | ✅ LIVE |
| `website/app-shell/src/pages/domains/DomainPage.tsx` | AnalyticsPage export | ✅ LIVE |
| `website/app-shell/src/pages/analytics/UsagePage.tsx` | Usage page component | ✅ LIVE |
| `website/app-shell/src/pages/analytics/CostPage.tsx` | Cost page component | ✅ LIVE |
| `website/app-shell/src/routes/index.tsx` | Analytics routes | ✅ LIVE |
| `design/l2_1/ui_contract/ui_projection_lock.json` | Analytics domain in projection | ✅ LIVE |

---

## 10. Overall Assessment

| Aspect | Old Grade | New Grade | Notes |
|--------|-----------|-----------|-------|
| **Backend Implementation** | A- | A | Unified facade + export |
| **Console Integration** | D | **B** | Visible sidebar domain |
| **Usage Tracking** | F | **B+** | Read v1 + export |
| **Reporting** | F | **B** | CSV/JSON live |
| **API Architecture** | C | **B+** | Unified facade enforced |

**Resolution (2026-01-17):** Analytics is now a **live console domain**.

**What Was Delivered:**
1. ✅ Analytics is 6th sidebar domain (visible)
2. ✅ Usage statistics with time window controls
3. ✅ CSV and JSON export endpoints
4. ✅ Signal reconciliation rules documented
5. ✅ OpenAPI specification locked
6. ✅ Landing page with usage summary
7. ✅ Usage page with table and export buttons

**What This Forces:**
- Analytics can now be sold, reviewed, audited
- Usage is customer-visible truth
- Cost intelligence can no longer hide behind Overview
- Future incidents/export automation has a home
- **Prevents rollback** into "embedded but invisible"

---

## 11. Final State (Non-Negotiable Truth)

- Analytics **exists**
- Analytics is **visible**
- Usage is **implemented**
- Reporting **works**
- Facade is **enforced**

No more "declared but missing".
