# hoc_cus_analytics_L6_drivers_leader

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L6_drivers/leader.py` |
| Layer | L6 — Domain Driver |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

CostSim Leader Election via PostgreSQL Advisory Locks

## Intent

**Role:** CostSim Leader Election via PostgreSQL Advisory Locks
**Reference:** PIN-470, M6 CostSim
**Callers:** canary.py, alert_worker.py (L5 engines)

## Purpose

Leader election using PostgreSQL advisory locks.

---

## Functions

### `async try_acquire_leader_lock(session: AsyncSession, lock_id: int) -> bool`
- **Async:** Yes
- **Docstring:** Try to acquire an advisory lock (non-blocking).  Uses pg_try_advisory_lock() which returns immediately with true/false.
- **Calls:** debug, execute, fetchone, info, text

### `async release_leader_lock(session: AsyncSession, lock_id: int) -> bool`
- **Async:** Yes
- **Docstring:** Explicitly release an advisory lock.  Usually not needed since locks are released when session closes,
- **Calls:** debug, execute, fetchone, info, text

### `async is_lock_held(session: AsyncSession, lock_id: int) -> bool`
- **Async:** Yes
- **Docstring:** Check if a lock is currently held by any session.  Note: This is informational only. The lock state could change
- **Calls:** execute, fetchone, text

### `async leader_election(lock_id: int, timeout_seconds: float) -> AsyncGenerator[bool, None]`
- **Async:** Yes
- **Decorators:** @asynccontextmanager
- **Docstring:** Context manager for leader election.  Alternative to LeaderContext class, using a function-based approach.
- **Calls:** AsyncSessionLocal, close, error, try_acquire_leader_lock, wait_for, warning

### `async with_leader_lock(lock_id: int, callback, *args, **kwargs)`
- **Async:** Yes
- **Docstring:** Execute callback only if we can acquire leadership.  Convenience function for fire-and-forget leader tasks.
- **Calls:** callback, leader_election

### `async with_canary_lock(callback, *args, **kwargs)`
- **Async:** Yes
- **Docstring:** Execute callback with canary runner lock.
- **Calls:** with_leader_lock

### `async with_alert_worker_lock(callback, *args, **kwargs)`
- **Async:** Yes
- **Docstring:** Execute callback with alert worker lock.
- **Calls:** with_leader_lock

### `async with_archiver_lock(callback, *args, **kwargs)`
- **Async:** Yes
- **Docstring:** Execute callback with provenance archiver lock.
- **Calls:** with_leader_lock

## Classes

### `LeaderContext`
- **Docstring:** Async context manager for leader election.
- **Methods:** __init__, __aenter__, __aexit__, is_leader

## Attributes

- `logger` (line 69)
- `LOCK_CANARY_RUNNER` (line 74)
- `LOCK_ALERT_WORKER` (line 75)
- `LOCK_PROVENANCE_ARCHIVER` (line 76)
- `LOCK_BASELINE_BACKFILL` (line 77)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.db_async`, `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

canary.py, alert_worker.py (L5 engines)

## Export Contract

```yaml
exports:
  functions:
    - name: try_acquire_leader_lock
      signature: "async try_acquire_leader_lock(session: AsyncSession, lock_id: int) -> bool"
    - name: release_leader_lock
      signature: "async release_leader_lock(session: AsyncSession, lock_id: int) -> bool"
    - name: is_lock_held
      signature: "async is_lock_held(session: AsyncSession, lock_id: int) -> bool"
    - name: leader_election
      signature: "async leader_election(lock_id: int, timeout_seconds: float) -> AsyncGenerator[bool, None]"
    - name: with_leader_lock
      signature: "async with_leader_lock(lock_id: int, callback, *args, **kwargs)"
    - name: with_canary_lock
      signature: "async with_canary_lock(callback, *args, **kwargs)"
    - name: with_alert_worker_lock
      signature: "async with_alert_worker_lock(callback, *args, **kwargs)"
    - name: with_archiver_lock
      signature: "async with_archiver_lock(callback, *args, **kwargs)"
  classes:
    - name: LeaderContext
      methods: [is_leader]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
