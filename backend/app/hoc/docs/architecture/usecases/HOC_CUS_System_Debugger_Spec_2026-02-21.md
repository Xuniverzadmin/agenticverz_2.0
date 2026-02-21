# HOC_CUS_System_Debugger_Spec_2026-02-21

**Created:** 2026-02-21
**Task:** T7 — Debugger Design
**Status:** DONE

---

## 1. Objective

Define operator debugger slice spec for triage, replay, and root-cause analysis. Map to stagetest runtime and release operations.

---

## 2. Debugger Concept

The System Debugger is an operator-facing diagnostic surface that enables:
1. **Triage** — Quickly identify what failed, where, and for which tenant
2. **Replay** — Re-execute a request or trace with deterministic inputs
3. **Root-cause** — Trace a failure from L2 API → L4 handler → L5 engine → L6 driver

---

## 3. Debugger Slice Model

### 3.1 Slice Definition

A **debugger slice** is a complete snapshot of a request's execution across all HOC layers:

```json
{
  "slice_id": "uuid",
  "correlation_id": "request-correlation-id",
  "timestamp": "2026-02-21T19:00:00Z",
  "tenant_id": "tenant_123",
  "auth_plane": "HUMAN",
  "request": {
    "method": "GET",
    "path": "/hoc/api/cus/incidents/list",
    "query_params": {"status": "active"},
    "auth_context_type": "HumanAuthContext"
  },
  "layers": [
    {
      "layer": "L2",
      "file": "incidents/incidents_public.py",
      "operation": "list_active_incidents",
      "duration_ms": 45,
      "status": "success"
    },
    {
      "layer": "L4",
      "file": "handlers/incidents_handler.py",
      "operation": "incidents.list_active",
      "duration_ms": 40,
      "status": "success"
    },
    {
      "layer": "L5",
      "file": "incidents/L5_engines/incident_engine.py",
      "method": "list_active",
      "duration_ms": 35,
      "status": "success"
    },
    {
      "layer": "L6",
      "file": "incidents/L6_drivers/incident_driver.py",
      "method": "fetch_active_incidents",
      "duration_ms": 30,
      "status": "success",
      "db_query": "SELECT ... FROM incidents WHERE status='active' AND tenant_id=?"
    }
  ],
  "outcome": {
    "status_code": 200,
    "total_duration_ms": 50,
    "rows_returned": 12
  }
}
```

### 3.2 Slice Collection Modes

| Mode | Trigger | Overhead | Retention |
|------|---------|----------|-----------|
| Always-on (sampled) | Every Nth request (configurable, default N=100) | LOW | 24 hours |
| On-error | Any request returning 4xx/5xx | NONE (only on error) | 7 days |
| On-demand | Operator flag `X-Debug-Slice: true` | MODERATE | Until read |
| Replay | Manual replay of a trace | MODERATE | Until read |

---

## 4. Triage Interface

### 4.1 Triage Query Endpoints (Proposed)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/hoc/api/debug/slices` | List recent slices (filtered by tenant, status, time range) |
| GET | `/hoc/api/debug/slices/{slice_id}` | Get full slice detail |
| GET | `/hoc/api/debug/errors` | List recent errors grouped by type + domain |
| GET | `/hoc/api/debug/slow` | List slowest operations (P99 outliers) |

### 4.2 Triage Workflow

```
1. Alert fires: "HOCHighErrorRate in incidents domain"
2. Operator queries: GET /hoc/api/debug/errors?domain=incidents&since=5m
3. Response shows: 15 errors, all "db_timeout" in L6 driver
4. Operator drills: GET /hoc/api/debug/slices/{slice_id} for a sample error
5. Slice shows: L6 driver query took 30,001ms (timeout at 30s)
6. Root cause identified: Missing index on incidents.status column
```

---

## 5. Replay Capability

### 5.1 Replay Model

Replay re-executes a captured request with the same inputs to verify:
- **Determinism** — same inputs produce same outputs (or identify drift)
- **Fix verification** — after a fix, replay confirms the error is resolved
- **Regression detection** — replay historical traces after deployments

### 5.2 Existing Replay Infrastructure

| Component | File | Status |
|-----------|------|--------|
| Trace storage | `logs/L5_engines/trace_api_engine.py` | Operational |
| Determinism validation | Root hash + step hashes | Operational |
| Mismatch detection | `logs/L5_engines/trace_mismatch_engine.py` | Operational |
| Replay L2 endpoints | `logs/traces.py:538-644` (compare), `804-937` (report/resolve) | Operational |

### 5.3 Replay Extension for Debugger

The existing trace replay system (UC-MON) provides the foundation. Extensions needed:

1. **Request replay** — capture full request (headers, body, query params) for re-execution
2. **Snapshot inputs** — capture L5 engine input state for isolated replay
3. **Diff visualization** — side-by-side comparison of original vs replay execution

---

## 6. Stagetest Runtime Mapping

### 6.1 Stagetest Integration

| Stagetest Feature | Debugger Use |
|-------------------|-------------|
| `GET /hoc/api/stagetest/runs` | List stagetest execution runs |
| `GET /hoc/api/stagetest/cases` | Individual test case results |
| `GET /hoc/api/stagetest/snapshots` | API response snapshots for comparison |

### 6.2 Release Operations Mapping

| Release Operation | Debugger Support |
|-------------------|-----------------|
| Pre-deploy validation | Run stagetest suite, capture slices for all endpoints |
| Post-deploy verification | Replay pre-deploy traces, compare outputs |
| Rollback decision | Compare error rates before/after deployment via slice analysis |
| Incident investigation | Query slices by time window + affected tenant |

---

## 7. Implementation Priority

| Priority | Component | Depends On |
|----------|-----------|-----------|
| P0 | Correlation ID propagation (T6 standard) | T6 |
| P0 | Error slice collection (on-error mode) | Correlation ID |
| P1 | Triage query endpoints | Error slices |
| P1 | Always-on sampled collection | Correlation ID |
| P2 | On-demand debug flag | Sampled collection |
| P2 | Request replay capability | Trace system (existing) |
| P3 | Diff visualization | Replay capability |

---

## 8. Access Control

| Endpoint | Access |
|----------|--------|
| `/hoc/api/debug/*` | Founder-only (`FounderAuthContext`) |
| Slice data | Tenant-scoped (operator sees all tenants) |
| Replay execution | Founder-only, audit-logged |
| On-demand flag (`X-Debug-Slice`) | Founder-only (validated at gateway) |
