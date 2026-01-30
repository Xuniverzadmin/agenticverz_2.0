# hoc_cus_activity_L6_drivers_orphan_recovery

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/activity/L6_drivers/orphan_recovery.py` |
| Layer | L6 — Domain Driver |
| Domain | activity |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Orphan detection logic, PB-S2 truth guarantee

## Intent

**Role:** Orphan detection logic, PB-S2 truth guarantee
**Reference:** PIN-470, PIN-242 (Baseline Freeze)
**Callers:** L5 workers (startup), L7 ops scripts

## Purpose

_No module docstring._

---

## Functions

### `async detect_orphaned_runs(session: AsyncSession, threshold_minutes: int) -> list[WorkerRun]`
- **Async:** Yes
- **Docstring:** Detect runs that appear to be orphaned.  A run is orphaned if:
- **Calls:** all, asc, execute, in_, list, order_by, scalars, select, timedelta, utcnow, where

### `async mark_run_as_crashed(session: AsyncSession, run: WorkerRun, reason: str) -> bool`
- **Async:** Yes
- **Docstring:** Mark a run as crashed.  This is a factual status update, not a mutation of historical data.
- **Calls:** error, execute, info, isoformat, str, update, utcnow, values, where

### `async recover_orphaned_runs(threshold_minutes: Optional[int]) -> dict`
- **Async:** Yes
- **Docstring:** Main recovery function - called on startup.  Detects and marks all orphaned runs as crashed.
- **Calls:** append, detect_orphaned_runs, error, get_async_session, info, len, mark_run_as_crashed, str, warning

### `async get_crash_recovery_summary() -> dict`
- **Async:** Yes
- **Docstring:** Get a summary of crashed runs for operator visibility.  Returns counts and recent crashed runs for /ops dashboard.
- **Calls:** all, count, desc, execute, get_async_session, isoformat, limit, order_by, scalar, scalars, select, select_from, where

## Attributes

- `FEATURE_INTENT` (line 27)
- `RETRY_POLICY` (line 28)
- `logger` (line 59)
- `ORPHAN_THRESHOLD_MINUTES` (line 62)
- `RECOVERY_ENABLED` (line 63)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.tenant` |
| External | `app.db`, `app.infra`, `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

L5 workers (startup), L7 ops scripts

## Export Contract

```yaml
exports:
  functions:
    - name: detect_orphaned_runs
      signature: "async detect_orphaned_runs(session: AsyncSession, threshold_minutes: int) -> list[WorkerRun]"
    - name: mark_run_as_crashed
      signature: "async mark_run_as_crashed(session: AsyncSession, run: WorkerRun, reason: str) -> bool"
    - name: recover_orphaned_runs
      signature: "async recover_orphaned_runs(threshold_minutes: Optional[int]) -> dict"
    - name: get_crash_recovery_summary
      signature: "async get_crash_recovery_summary() -> dict"
  classes: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
