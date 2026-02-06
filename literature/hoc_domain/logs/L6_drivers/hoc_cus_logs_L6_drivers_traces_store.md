# hoc_cus_logs_L6_drivers_traces_store

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L6_drivers/traces_store.py` |
| Layer | L6 — Domain Driver |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Trace store abstraction

## Intent

**Role:** Trace store abstraction
**Reference:** PIN-470, Trace System
**Callers:** services, workers

## Purpose

Trace Storage for AOS
M6 Deliverable: Run traces with correlation IDs

---

## Functions

### `generate_correlation_id() -> str`
- **Async:** No
- **Docstring:** Generate a unique correlation ID for tracing.
- **Calls:** str, uuid4

### `generate_run_id() -> str`
- **Async:** No
- **Docstring:** Generate a unique run ID.
- **Calls:** uuid4

## Classes

### `TraceStore(ABC)`
- **Docstring:** Abstract base class for trace storage.
- **Methods:** start_trace, record_step, complete_trace, get_trace, list_traces, delete_trace

### `SQLiteTraceStore(TraceStore)`
- **Docstring:** SQLite-based trace storage.
- **Methods:** __init__, _init_db, _get_conn, start_trace, record_step, complete_trace, get_trace, list_traces, delete_trace, get_trace_count, cleanup_old_traces, search_traces, get_trace_by_root_hash, find_matching_traces, update_trace_determinism

### `InMemoryTraceStore(TraceStore)`
- **Docstring:** In-memory trace storage for testing.
- **Methods:** __init__, start_trace, record_step, complete_trace, get_trace, list_traces, delete_trace

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `models`, `sqlite3` |

## Callers

services, workers

## Export Contract

```yaml
exports:
  functions:
    - name: generate_correlation_id
      signature: "generate_correlation_id() -> str"
    - name: generate_run_id
      signature: "generate_run_id() -> str"
  classes:
    - name: TraceStore
      methods: [start_trace, record_step, complete_trace, get_trace, list_traces, delete_trace]
    - name: SQLiteTraceStore
      methods: [start_trace, record_step, complete_trace, get_trace, list_traces, delete_trace, get_trace_count, cleanup_old_traces, search_traces, get_trace_by_root_hash, find_matching_traces, update_trace_determinism]
    - name: InMemoryTraceStore
      methods: [start_trace, record_step, complete_trace, get_trace, list_traces, delete_trace]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
