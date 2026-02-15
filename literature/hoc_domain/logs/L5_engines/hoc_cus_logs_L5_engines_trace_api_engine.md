# hoc_cus_logs_L5_engines_trace_api_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/trace_api_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Trace API orchestration over trace store capability.

## Intent

**Role:** Trace API orchestration (list/get/store/compare/delete/cleanup/idempotency)  
**Callers:** L4 logs_handler (`logs.traces_api`)

---

## Classes

### `TraceApiEngine`
- **Methods:** `list_traces`, `store_trace`, `get_trace`, `get_trace_by_root_hash`, `compare_traces`, `delete_trace`, `cleanup_old_traces`, `check_idempotency`

## Functions

### `get_trace_api_engine(trace_store: Any) -> TraceApiEngine`
- **Async:** No
- **Docstring:** None
- **Calls:** `TraceApiEngine`

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 | `app.hoc.cus.logs.L6_drivers.redact` |

## Callers

- L4 logs_handler (`logs.traces_api`)

## Export Contract

```yaml
exports:
  functions:
    - name: get_trace_api_engine
      signature: "get_trace_api_engine(trace_store: Any) -> TraceApiEngine"
  classes:
    - TraceApiEngine
```

## Evaluation Notes

- **Disposition:** KEEP
- **Rationale:** L4 traces API entrypoint for L2 trace routes (L2→L4→L5→L6)
