# hoc_cus_logs_L6_drivers_pg_store

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L6_drivers/pg_store.py` |
| Layer | L6 — Domain Driver |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

PostgreSQL trace storage

## Intent

**Role:** PostgreSQL trace storage
**Reference:** PIN-470, Trace System
**Callers:** trace store abstraction

## Purpose

PostgreSQL Trace Store for AOS
M8 Deliverable: Production-grade trace storage with PostgreSQL

---

## Functions

### `_status_to_level(status: str) -> str`
- **Async:** No
- **Docstring:** Derive log level from step status.  Mapping per PIN-378 (Canonical Logs System):
- **Calls:** isinstance, lower, str

### `get_postgres_trace_store() -> PostgresTraceStore`
- **Async:** No
- **Docstring:** Get singleton PostgreSQL trace store.
- **Calls:** PostgresTraceStore

## Classes

### `PostgresTraceStore`
- **Docstring:** PostgreSQL-based trace storage for production.
- **Methods:** __init__, _get_pool, close, start_trace, record_step, complete_trace, mark_trace_aborted, store_trace, get_trace, get_trace_by_root_hash, search_traces, list_traces, delete_trace, get_trace_count, cleanup_old_traces, check_idempotency_key

## Attributes

- `_pg_store: PostgresTraceStore | None` (line 761)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `asyncpg`, `models`, `redact` |

## Callers

trace store abstraction

## Export Contract

```yaml
exports:
  functions:
    - name: get_postgres_trace_store
      signature: "get_postgres_trace_store() -> PostgresTraceStore"
  classes:
    - name: PostgresTraceStore
      methods: [close, start_trace, record_step, complete_trace, mark_trace_aborted, store_trace, get_trace, get_trace_by_root_hash, search_traces, list_traces, delete_trace, get_trace_count, cleanup_old_traces, check_idempotency_key]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
