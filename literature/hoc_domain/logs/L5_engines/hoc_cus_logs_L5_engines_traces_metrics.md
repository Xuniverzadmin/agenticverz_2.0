# hoc_cus_logs_L5_engines_traces_metrics

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/traces_metrics.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Trace metrics collection (Prometheus)

## Intent

**Role:** Trace metrics collection (Prometheus)
**Reference:** PIN-470, Trace System
**Callers:** trace store

## Purpose

Prometheus Metrics for AOS Traces API

---

## Functions

### `get_traces_metrics() -> TracesMetrics`
- **Async:** No
- **Docstring:** Get or create global traces metrics instance.
- **Calls:** TracesMetrics

### `instrument_trace_request(operation: str)`
- **Async:** No
- **Docstring:** Decorator to instrument trace API endpoints.
- **Calls:** func, get, get_traces_metrics, measure_request, wraps

### `instrument_replay_check(func: Callable) -> Callable`
- **Async:** No
- **Docstring:** Decorator to instrument replay enforcement.
- **Calls:** func, get, get_traces_metrics, getattr, record_replay_enforcement, str, wraps

### `instrument_parity_check(func: Callable) -> Callable`
- **Async:** No
- **Docstring:** Decorator to instrument parity checks.
- **Calls:** func, get, get_traces_metrics, getattr, record_parity_check, wraps

## Classes

### `TracesMetrics`
- **Docstring:** Centralized metrics manager for traces API.
- **Methods:** __init__, measure_request, record_trace_stored, record_replay_enforcement, record_idempotency_check, record_parity_check, measure_storage

## Attributes

- `logger` (line 39)
- `TRACE_LATENCY_HISTOGRAM` (line 87)
- `TRACE_REQUESTS_COUNTER` (line 98)
- `TRACE_PARITY_GAUGE` (line 108)
- `REPLAY_ENFORCEMENT_COUNTER` (line 114)
- `IDEMPOTENCY_COUNTER` (line 124)
- `TRACE_STEPS_HISTOGRAM` (line 130)
- `TRACE_SIZE_HISTOGRAM` (line 141)
- `PARITY_FAILURES_COUNTER` (line 152)
- `TRACE_STORAGE_LATENCY` (line 159)
- `_traces_metrics: Optional[TracesMetrics]` (line 232)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `prometheus_client` |

## Callers

trace store

## Export Contract

```yaml
exports:
  functions:
    - name: get_traces_metrics
      signature: "get_traces_metrics() -> TracesMetrics"
    - name: instrument_trace_request
      signature: "instrument_trace_request(operation: str)"
    - name: instrument_replay_check
      signature: "instrument_replay_check(func: Callable) -> Callable"
    - name: instrument_parity_check
      signature: "instrument_parity_check(func: Callable) -> Callable"
  classes:
    - name: TracesMetrics
      methods: [measure_request, record_trace_stored, record_replay_enforcement, record_idempotency_check, record_parity_check, measure_storage]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
