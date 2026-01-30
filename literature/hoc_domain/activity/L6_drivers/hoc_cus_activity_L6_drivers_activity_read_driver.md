# hoc_cus_activity_L6_drivers_activity_read_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/activity/L6_drivers/activity_read_driver.py` |
| Layer | L6 — Data Access Driver |
| Domain | activity |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Activity read data access operations

## Intent

**Role:** Activity read data access operations
**Reference:** PIN-470, Phase-3B SQLAlchemy Extraction
**Callers:** activity_facade.py (L5 engine)

## Purpose

Activity Read Driver (L6 Data Access)

---

## Functions

### `get_activity_read_driver(session: AsyncSession) -> ActivityReadDriver`
- **Async:** No
- **Docstring:** Get an ActivityReadDriver instance.
- **Calls:** ActivityReadDriver

## Classes

### `ActivityReadDriver`
- **Docstring:** L6 Driver for activity read operations.
- **Methods:** __init__, count_runs, fetch_runs, fetch_run_detail, fetch_status_summary, fetch_runs_with_policy_context, fetch_at_risk_runs, fetch_metrics, fetch_threshold_signals

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

activity_facade.py (L5 engine)

## Export Contract

```yaml
exports:
  functions:
    - name: get_activity_read_driver
      signature: "get_activity_read_driver(session: AsyncSession) -> ActivityReadDriver"
  classes:
    - name: ActivityReadDriver
      methods: [count_runs, fetch_runs, fetch_run_detail, fetch_status_summary, fetch_runs_with_policy_context, fetch_at_risk_runs, fetch_metrics, fetch_threshold_signals]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
