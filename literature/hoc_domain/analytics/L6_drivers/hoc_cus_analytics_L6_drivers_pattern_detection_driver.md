# hoc_cus_analytics_L6_drivers_pattern_detection_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L6_drivers/pattern_detection_driver.py` |
| Layer | L6 — Data Access Driver |
| Domain | analytics |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Pattern detection data access operations

## Intent

**Role:** Pattern detection data access operations
**Reference:** PIN-470, Phase-3B SQLAlchemy Extraction
**Callers:** pattern_detection.py (L5 engine)

## Purpose

Pattern Detection Driver (L6 Data Access)

---

## Functions

### `get_pattern_detection_driver(session: AsyncSession) -> PatternDetectionDriver`
- **Async:** No
- **Docstring:** Get a PatternDetectionDriver instance.
- **Calls:** PatternDetectionDriver

## Classes

### `PatternDetectionDriver`
- **Docstring:** L6 Driver for pattern detection data operations.
- **Methods:** __init__, fetch_failed_runs, fetch_completed_runs_with_costs, insert_feedback, fetch_feedback_records

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.feedback`, `app.models.tenant` |
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

pattern_detection.py (L5 engine)

## Export Contract

```yaml
exports:
  functions:
    - name: get_pattern_detection_driver
      signature: "get_pattern_detection_driver(session: AsyncSession) -> PatternDetectionDriver"
  classes:
    - name: PatternDetectionDriver
      methods: [fetch_failed_runs, fetch_completed_runs_with_costs, insert_feedback, fetch_feedback_records]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
