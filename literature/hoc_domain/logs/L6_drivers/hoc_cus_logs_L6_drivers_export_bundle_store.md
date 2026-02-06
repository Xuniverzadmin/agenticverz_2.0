# hoc_cus_logs_L6_drivers_export_bundle_store

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L6_drivers/export_bundle_store.py` |
| Layer | L6 — Domain Driver |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Database operations for export bundle data (incidents, runs, traces)

## Intent

**Role:** Database operations for export bundle data (incidents, runs, traces)
**Reference:** PIN-470, HOC_LAYER_TOPOLOGY_V1.md, LOGS_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** L3 ExportBundleAdapter

## Purpose

Export Bundle Store (L6)

---

## Functions

### `get_export_bundle_store() -> ExportBundleStore`
- **Async:** No
- **Docstring:** Get the singleton ExportBundleStore instance.
- **Calls:** ExportBundleStore

## Classes

### `IncidentSnapshot`
- **Docstring:** Immutable snapshot of incident.
- **Class Variables:** id: str, tenant_id: str, source_run_id: Optional[str], severity: Optional[str], policy_id: Optional[str], policy_name: Optional[str], violation_type: Optional[str], created_at: datetime

### `RunSnapshot`
- **Docstring:** Immutable snapshot of run.
- **Class Variables:** run_id: str, tenant_id: str, agent_id: Optional[str], goal: Optional[str], policy_snapshot_id: Optional[str], started_at: Optional[datetime], completed_at: Optional[datetime], termination_reason: Optional[str], total_cost_cents: Optional[int]

### `TraceSummarySnapshot`
- **Docstring:** Immutable snapshot of trace summary.
- **Class Variables:** trace_id: str, run_id: str, tenant_id: str, violation_step_index: Optional[int], violation_timestamp: Optional[datetime]

### `TraceStepSnapshot`
- **Docstring:** Immutable snapshot of trace step.
- **Class Variables:** step_index: int, timestamp: datetime, step_type: str, tokens: int, cost_cents: float, duration_ms: float, status: str, content_hash: Optional[str]

### `ExportBundleStore`
- **Docstring:** L6 Database Driver for export bundle data.
- **Methods:** __init__, trace_store, get_incident, get_run_by_run_id, get_trace_summary, get_trace_steps

## Attributes

- `_store_instance: ExportBundleStore | None` (line 224)
- `__all__` (line 235)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.db`, `app.traces.store`, `sqlmodel` |

## Callers

L3 ExportBundleAdapter

## Export Contract

```yaml
exports:
  functions:
    - name: get_export_bundle_store
      signature: "get_export_bundle_store() -> ExportBundleStore"
  classes:
    - name: IncidentSnapshot
      methods: []
    - name: RunSnapshot
      methods: []
    - name: TraceSummarySnapshot
      methods: []
    - name: TraceStepSnapshot
      methods: []
    - name: ExportBundleStore
      methods: [trace_store, get_incident, get_run_by_run_id, get_trace_summary, get_trace_steps]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
