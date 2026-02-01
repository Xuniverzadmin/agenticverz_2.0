# hoc_cus_analytics_L5_engines_prediction

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/prediction.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Prediction generation and orchestration (advisory only)

## Intent

**Role:** Prediction generation and orchestration (advisory only)
**Reference:** PIN-470, Phase-2.5A Analytics Extraction, PIN-240
**Callers:** predictions API (read-side)

## Purpose

Prediction Service (PB-S5)

---

## Functions

### `async predict_failure_likelihood(driver: 'PredictionDriver', tenant_id: Optional[UUID], worker_id: Optional[str]) -> list[dict]`
- **Async:** Yes
- **Docstring:** Predict likelihood of failure for upcoming runs.  Phase-2.5A: Data fetching delegated to driver (L6).
- **Calls:** append, fetch_failed_runs, fetch_failure_patterns, fetch_run_totals, get, info, items, len, list, min, round, set, str, timedelta, utc_now

### `async predict_cost_overrun(driver: 'PredictionDriver', tenant_id: Optional[UUID], worker_id: Optional[str]) -> list[dict]`
- **Async:** Yes
- **Docstring:** Predict likelihood of cost overrun for upcoming runs.  Phase-2.5A: Data fetching delegated to driver (L6).
- **Calls:** append, fetch_cost_runs, info, items, len, min, round, sorted, str, sum, timedelta, utc_now

### `async emit_prediction(driver: 'PredictionDriver', tenant_id: str, prediction_type: str, subject_type: str, subject_id: str, confidence_score: float, prediction_value: dict, contributing_factors: list, notes: Optional[str], valid_until: Optional['datetime']) -> 'PredictionEvent'`
- **Async:** Yes
- **Docstring:** Emit a prediction event.  Phase-2.5A: Persistence delegated to driver (L6).
- **Calls:** info, insert_prediction, str, timedelta, utc_now

### `async run_prediction_cycle(tenant_id: Optional[UUID]) -> dict`
- **Async:** Yes
- **Docstring:** Run full prediction cycle.  Phase-2.5A: Data access delegated to driver (L6).
- **Calls:** append, emit_prediction, error, get_async_session, get_prediction_driver, predict_cost_overrun, predict_failure_likelihood, str

### `async get_prediction_summary(tenant_id: Optional[UUID], prediction_type: Optional[str], include_expired: bool, limit: int) -> dict`
- **Async:** Yes
- **Docstring:** Get prediction summary for ops visibility.  Phase-2.5A: Data fetching delegated to driver (L6).
- **Calls:** fetch_predictions, get, get_async_session, get_prediction_driver, isoformat, len, str, utc_now

## Attributes

- `logger` (line 68)
- `FAILURE_CONFIDENCE_THRESHOLD` (line 71)
- `COST_OVERRUN_THRESHOLD_PERCENT` (line 72)
- `PREDICTION_VALIDITY_HOURS` (line 73)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.analytics.L6_drivers.prediction_driver` |
| L7 Model | `app.models.prediction` |
| External | `app.db`, `app.hoc.cus.hoc_spine.services.time` |

## Callers

predictions API (read-side)

## Export Contract

```yaml
exports:
  functions:
    - name: predict_failure_likelihood
      signature: "async predict_failure_likelihood(driver: 'PredictionDriver', tenant_id: Optional[UUID], worker_id: Optional[str]) -> list[dict]"
    - name: predict_cost_overrun
      signature: "async predict_cost_overrun(driver: 'PredictionDriver', tenant_id: Optional[UUID], worker_id: Optional[str]) -> list[dict]"
    - name: emit_prediction
      signature: "async emit_prediction(driver: 'PredictionDriver', tenant_id: str, prediction_type: str, subject_type: str, subject_id: str, confidence_score: float, prediction_value: dict, contributing_factors: list, notes: Optional[str], valid_until: Optional['datetime']) -> 'PredictionEvent'"
    - name: run_prediction_cycle
      signature: "async run_prediction_cycle(tenant_id: Optional[UUID]) -> dict"
    - name: get_prediction_summary
      signature: "async get_prediction_summary(tenant_id: Optional[UUID], prediction_type: Optional[str], include_expired: bool, limit: int) -> dict"
  classes: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
