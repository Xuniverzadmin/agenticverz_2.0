# hoc_cus_analytics_L6_drivers_analytics_read_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L6_drivers/analytics_read_driver.py` |
| Layer | L6 — Data Access Driver |
| Domain | analytics |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Analytics read data access operations

## Intent

**Role:** Analytics read data access operations
**Reference:** PIN-470, Phase-3B SQLAlchemy Extraction
**Callers:** analytics_facade.py (L5 engine)

## Purpose

Analytics Read Driver (L6 Data Access)

---

## Functions

### `get_analytics_read_driver(session: AsyncSession) -> AnalyticsReadDriver`
- **Async:** No
- **Docstring:** Get an AnalyticsReadDriver instance.
- **Calls:** AnalyticsReadDriver

## Classes

### `AnalyticsReadDriver`
- **Docstring:** L6 Driver for analytics read operations.
- **Methods:** __init__, fetch_cost_metrics, fetch_llm_usage, fetch_worker_execution, fetch_cost_spend, fetch_cost_by_model, fetch_cost_by_feature

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

analytics_facade.py (L5 engine)

## Export Contract

```yaml
exports:
  functions:
    - name: get_analytics_read_driver
      signature: "get_analytics_read_driver(session: AsyncSession) -> AnalyticsReadDriver"
  classes:
    - name: AnalyticsReadDriver
      methods: [fetch_cost_metrics, fetch_llm_usage, fetch_worker_execution, fetch_cost_spend, fetch_cost_by_model, fetch_cost_by_feature]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
