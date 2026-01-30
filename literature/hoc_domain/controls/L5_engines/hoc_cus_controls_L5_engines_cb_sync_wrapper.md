# hoc_cus_controls_L5_engines_cb_sync_wrapper

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L5_engines/cb_sync_wrapper.py` |
| Layer | L5 — Domain Engine |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Circuit breaker sync wrapper (thread-safe async bridge)

## Intent

**Role:** Circuit breaker sync wrapper (thread-safe async bridge)
**Reference:** PIN-470
**Callers:** sync middleware, legacy code

## Purpose

Thread-safe sync wrapper for async circuit breaker functions.

---

## Functions

### `_get_executor() -> concurrent.futures.ThreadPoolExecutor`
- **Async:** No
- **Docstring:** Get or create the shared thread pool executor.
- **Calls:** ThreadPoolExecutor

### `_run_async_in_thread(coro, timeout: float)`
- **Async:** No
- **Docstring:** Run an async coroutine in a separate thread with its own event loop.  This is safe to call from any context, including:
- **Calls:** _get_executor, close, new_event_loop, result, run_until_complete, set_event_loop, submit

### `is_v2_disabled_sync(timeout: float) -> bool`
- **Async:** No
- **Docstring:** Sync wrapper for is_v2_disabled().  Safe to call from any context. Runs the async function in a
- **Calls:** _run_async_in_thread, bool, error, get_running_loop, is_v2_disabled, run

### `get_state_sync(timeout: float)`
- **Async:** No
- **Docstring:** Sync wrapper for get_state().  Safe to call from any context.
- **Calls:** _run_async_in_thread, error, get_running_loop, get_state, run

### `shutdown_executor()`
- **Async:** No
- **Docstring:** Shutdown the thread pool executor gracefully.
- **Calls:** shutdown

## Attributes

- `logger` (line 48)
- `_executor: Optional[concurrent.futures.ThreadPoolExecutor]` (line 51)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.costsim.circuit_breaker_async`, `concurrent.futures` |

## Callers

sync middleware, legacy code

## Export Contract

```yaml
exports:
  functions:
    - name: is_v2_disabled_sync
      signature: "is_v2_disabled_sync(timeout: float) -> bool"
    - name: get_state_sync
      signature: "get_state_sync(timeout: float)"
    - name: shutdown_executor
      signature: "shutdown_executor()"
  classes: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
