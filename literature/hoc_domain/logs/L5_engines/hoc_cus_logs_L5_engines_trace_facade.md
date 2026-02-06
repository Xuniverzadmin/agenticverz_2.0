# hoc_cus_logs_L5_engines_trace_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/trace_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Trace Domain Facade - Centralized access to trace operations with RAC acks

## Intent

**Role:** Trace Domain Facade - Centralized access to trace operations with RAC acks
**Reference:** PIN-470, PIN-454 (Cross-Domain Orchestration Audit)
**Callers:** L5 runner/observability guard (via dependency injection), API routes

## Purpose

Trace Domain Facade (L5 Domain Engine)

---

## Functions

### `get_trace_facade(trace_store) -> TraceFacade`
- **Async:** No
- **Docstring:** Get the trace facade singleton.  Args:
- **Calls:** TraceFacade

## Classes

### `TraceFacade`
- **Docstring:** Facade for trace domain operations.
- **Methods:** __init__, _store, start_trace, complete_trace, add_step, _emit_ack

## Attributes

- `logger` (line 48)
- `RAC_ENABLED` (line 51)
- `_facade_instance: Optional[TraceFacade]` (line 281)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.hoc.cus.hoc_spine.services.audit_store`, `app.services.audit.models`, `app.telemetry.trace_store` |

## Callers

L5 runner/observability guard (via dependency injection), API routes

## Export Contract

```yaml
exports:
  functions:
    - name: get_trace_facade
      signature: "get_trace_facade(trace_store) -> TraceFacade"
  classes:
    - name: TraceFacade
      methods: [start_trace, complete_trace, add_step]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
