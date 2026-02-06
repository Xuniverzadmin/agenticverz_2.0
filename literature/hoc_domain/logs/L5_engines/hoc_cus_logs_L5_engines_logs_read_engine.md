# hoc_cus_logs_L5_engines_logs_read_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/logs_read_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Logs/Traces domain read operations (L5)

## Intent

**Role:** Logs/Traces domain read operations (L5)
**Reference:** PIN-470, PIN-281 (L3 Adapter Closure - PHASE 1)
**Callers:** customer_logs_adapter.py (L3)

## Purpose

Logs Read Engine (L5)

---

## Functions

### `get_logs_read_service() -> LogsReadService`
- **Async:** No
- **Docstring:** Factory function to get LogsReadService instance.  This is the ONLY way L3 should obtain a logs read service.
- **Calls:** LogsReadService

## Classes

### `LogsReadService`
- **Docstring:** L4 service for logs/trace read operations.
- **Methods:** __init__, _get_store, search_traces, get_trace, get_trace_count, get_trace_by_root_hash, list_traces

## Attributes

- `_logs_read_service: Optional[LogsReadService]` (line 197)
- `__all__` (line 212)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.traces.models`, `app.traces.pg_store` |

## Callers

customer_logs_adapter.py (L3)

## Export Contract

```yaml
exports:
  functions:
    - name: get_logs_read_service
      signature: "get_logs_read_service() -> LogsReadService"
  classes:
    - name: LogsReadService
      methods: [search_traces, get_trace, get_trace_count, get_trace_by_root_hash, list_traces]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
