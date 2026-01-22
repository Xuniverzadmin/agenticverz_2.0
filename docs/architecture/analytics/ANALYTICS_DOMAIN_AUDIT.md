# Analytics Domain Audit

**Status:** ✅ LIVE (De Jure Console Domain)
**Last Updated:** 2026-01-22
**Reference:** PIN-411 (Unified Facades), PIN-463 (L4 Facade Pattern)

---

## Architecture Pattern

This domain follows the **L4 Facade Pattern** for data access:

| Layer | File | Role |
|-------|------|------|
| L2 API | `backend/app/api/aos_analytics.py` | HTTP handling, response formatting |
| L4 Facade | `backend/app/services/analytics_facade.py` | Business logic, tenant isolation |

**Data Flow:** `L1 (UI) → L2 (API) → L4 (Facade) → L6 (Database)`

**Key Rules:**
- L2 routes delegate to L4 facade (never direct SQL)
- Facade returns typed dataclasses (never ORM models)
- All operations are tenant-scoped

**Full Reference:** [PIN-463: L4 Facade Architecture Pattern](../../memory-pins/PIN-463-l4-facade-architecture-pattern.md), [LAYER_MODEL.md](../LAYER_MODEL.md)

---

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

## 3. L4 Domain Facade

### 3.1 Architecture Pattern

The Analytics domain uses a **Read-Only Facade Pattern** where L2 API endpoints delegate all data access to the L4 `AnalyticsFacade`:

```
┌─────────────────────┐
│   L2: analytics.py  │  (Endpoint handlers)
│   - Auth extraction │
│   - Request params  │
│   - Response mapping│
└──────────┬──────────┘
           │ await facade.method()
           ▼
┌─────────────────────┐
│  L4: AnalyticsFacade│  (Domain logic)
│   - SignalAdapter   │
│   - Reconciliation  │
│   - Result mapping  │
└──────────┬──────────┘
           │ session.execute()
           ▼
┌─────────────────────┐
│   L6: Database      │  (Data access)
└─────────────────────┘
```

### 3.2 Facade Entry Point

| Component | File | Pattern |
|-----------|------|---------|
| `AnalyticsFacade` | `backend/app/services/analytics_facade.py` | Singleton via `get_analytics_facade()` |

**Usage Pattern:**
```python
from app.services.analytics_facade import get_analytics_facade

facade = get_analytics_facade()
result = await facade.get_usage_statistics(session, tenant_id, ...)
```

### 3.3 Operations Provided

| Method | Purpose | Returns |
|--------|---------|---------|
| `get_usage_statistics()` | Usage statistics with time series | `UsageStatisticsResult` |
| `get_cost_statistics()` | Cost statistics with breakdowns | `CostStatisticsResult` |
| `get_status()` | Analytics domain capability status | `AnalyticsStatusResult` |

### 3.4 L2-to-L4 Result Type Mapping

All L4 facade methods return dataclass result types that L2 maps to Pydantic response models:

| L4 Result Type | L2 Response Model | Purpose |
|----------------|-------------------|---------|
| `UsageStatisticsResult` | `UsageStatisticsResponse` | Usage statistics |
| `TimeWindowResult` | `UsageWindow` / `TimeWindow` | Time window spec |
| `UsageTotalsResult` | `UsageTotals` | Usage totals |
| `UsageDataPointResult` | `UsageDataPoint` | Usage time series point |
| `SignalSourceResult` | `UsageSignals` / `CostSignals` | Signal metadata |
| `CostStatisticsResult` | `CostStatisticsResponse` | Cost statistics |
| `CostTotalsResult` | `CostTotals` | Cost totals |
| `CostDataPointResult` | `CostDataPoint` | Cost time series point |
| `CostByModelResult` | `CostByModel` | Cost by model breakdown |
| `CostByFeatureResult` | `CostByFeature` | Cost by feature breakdown |
| `AnalyticsStatusResult` | `AnalyticsStatusResponse` | Domain status |
| `TopicStatusResult` | `TopicStatus` | Topic capabilities |

### 3.5 Signal Adapters (L4 Owned)

The `SignalAdapter` class in the facade handles all data fetching from signal sources:

| Adapter | Source Table | Output |
|---------|--------------|--------|
| `fetch_cost_metrics` | cost_records | requests, tokens |
| `fetch_llm_usage` | runs | requests, tokens |
| `fetch_worker_execution` | aos_traces | compute_units |
| `fetch_cost_spend` | cost_records | spend_cents, requests, tokens |
| `fetch_cost_by_model` | cost_records | model breakdowns |
| `fetch_cost_by_feature` | cost_records | feature breakdowns |

### 3.6 Key Characteristics

- **Read-Only**: All facade methods are read operations (SELECT only)
- **Tenant-Scoped**: All queries filter by tenant_id
- **Signal Reconciliation**: Facade merges multiple signal sources
- **No State Mutation**: Facade does not write analytics data

---

## 4. API Routes

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
| AnalyticsFacade | `analytics_facade.py` | 829 | Unified facade with SignalAdapter |
| CostWriteService | `cost_write_service.py` | 181 | CRUD for tags, records, budgets |
| CostAnomalyDetector | `cost_anomaly_detector.py` | 1,100+ | M29 anomaly detection engine |
| CostModelEngine | `cost_model_engine.py` | 400+ | Cost calculation, token pricing |

**Note:** Signal Adapters (`fetch_cost_metrics`, `fetch_llm_usage`, etc.) are now in `analytics_facade.py` (see Section 3.5).

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

## 11. E2E Verification (2026-01-17)

### Test Environment

| Component | Value |
|-----------|-------|
| Backend | Docker (nova_agent_manager) |
| Database | Neon (production) |
| Tenant | `demo-tenant` |
| API Key | `DEMO_TENANT_API_KEY` (rotated 2026-01-17) |

### Endpoint Verification

| Endpoint | Status | Response |
|----------|--------|----------|
| `GET /api/v1/analytics/statistics/cost` | ✅ PASS | Real data returned |
| `GET /api/v1/analytics/statistics/cost/export.csv` | ✅ PASS | CSV with header + data |
| `GET /api/v1/analytics/statistics/cost/export.json` | ✅ PASS | JSON export |
| `GET /api/v1/analytics/_status` | ✅ PASS | Shows usage + cost topics |

### Sample Response (Cost Statistics)

```json
{
  "window": {"from": "2025-12-20T00:00:00Z", "to": "2025-12-28T23:59:59Z", "resolution": "day"},
  "totals": {
    "spend_cents": 4.0,
    "spend_usd": 0.04,
    "requests": 2,
    "input_tokens": 893,
    "output_tokens": 2085
  },
  "by_model": [{"model": "claude-sonnet-4-20250514", "pct_of_total": 100.0}],
  "by_feature": [{"feature_tag": "untagged", "pct_of_total": 100.0}],
  "signals": {"sources": ["cost_records"], "freshness_sec": 1952443}
}
```

### CSV Export Sample

```csv
timestamp,spend_cents,requests,input_tokens,output_tokens
2025-12-26,4.0,2,893,2085
```

### Status Endpoint Response

```json
{
  "domain": "analytics",
  "subdomains": ["statistics"],
  "topics": {
    "usage": {"read": true, "write": false, "signals_bound": 3},
    "cost": {"read": true, "write": false, "signals_bound": 1}
  }
}
```

---

## 12. Final State (Non-Negotiable Truth)

- Analytics **exists**
- Analytics is **visible**
- Usage is **implemented**
- Cost is **implemented** (E2E verified)
- Reporting **works** (E2E verified)
- Facade is **enforced**

No more "declared but missing".

---

## 13. Constitutional Reference

**Constitution:** `docs/contracts/ANALYTICS_DOMAIN_CONSTITUTION.md`

The Analytics Domain Constitution establishes governance invariants for:
- Signal source authority
- Export parity guarantees
- Tenant isolation
- API key governance
