# hoc_cus_analytics_L6_drivers_prediction_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L6_drivers/prediction_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for prediction operations

## Intent

**Role:** Data access for prediction operations
**Reference:** PIN-470, Phase-2.5A Analytics Extraction
**Callers:** prediction.py (L5 engine)

## Purpose

Prediction Driver (L6)

---

## Functions

### `get_prediction_driver(session: AsyncSession) -> PredictionDriver`
- **Async:** No
- **Docstring:** Factory function to get PredictionDriver instance.
- **Calls:** PredictionDriver

## Classes

### `PredictionDriver`
- **Docstring:** L6 driver for prediction data access.
- **Methods:** __init__, fetch_failure_patterns, fetch_failed_runs, fetch_run_totals, fetch_cost_runs, fetch_predictions, insert_prediction

## Attributes

- `__all__` (line 316)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.feedback`, `app.models.prediction`, `app.models.tenant` |
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

prediction.py (L5 engine)

## Export Contract

```yaml
exports:
  functions:
    - name: get_prediction_driver
      signature: "get_prediction_driver(session: AsyncSession) -> PredictionDriver"
  classes:
    - name: PredictionDriver
      methods: [fetch_failure_patterns, fetch_failed_runs, fetch_run_totals, fetch_cost_runs, fetch_predictions, insert_prediction]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
