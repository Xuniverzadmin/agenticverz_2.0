# hoc_cus_analytics_L6_drivers_cost_anomaly_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L6_drivers/cost_anomaly_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for cost anomaly detection operations

## Intent

**Role:** Data access for cost anomaly detection operations
**Reference:** PIN-470, Phase-2.5A Analytics Extraction
**Callers:** cost_anomaly_detector.py (L5 engine)

## Purpose

Cost Anomaly Driver (L6)

---

## Functions

### `get_cost_anomaly_driver(session: Session) -> CostAnomalyDriver`
- **Async:** No
- **Docstring:** Factory function to get CostAnomalyDriver instance.
- **Calls:** CostAnomalyDriver

## Classes

### `CostAnomalyDriver`
- **Docstring:** L6 driver for cost anomaly detection data access.
- **Methods:** __init__, fetch_entity_baseline, fetch_entity_today_spend, fetch_tenant_baseline, fetch_tenant_today_spend, fetch_rolling_avg, fetch_baseline_avg, fetch_daily_spend, fetch_monthly_spend, fetch_breach_exists_today, insert_breach_history, fetch_consecutive_breaches, fetch_drift_tracking, update_drift_tracking, insert_drift_tracking, reset_drift_tracking, fetch_retry_comparison, fetch_prompt_comparison, fetch_feature_concentration, fetch_request_comparison

## Attributes

- `__all__` (line 989)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlmodel` |

## Callers

cost_anomaly_detector.py (L5 engine)

## Export Contract

```yaml
exports:
  functions:
    - name: get_cost_anomaly_driver
      signature: "get_cost_anomaly_driver(session: Session) -> CostAnomalyDriver"
  classes:
    - name: CostAnomalyDriver
      methods: [fetch_entity_baseline, fetch_entity_today_spend, fetch_tenant_baseline, fetch_tenant_today_spend, fetch_rolling_avg, fetch_baseline_avg, fetch_daily_spend, fetch_monthly_spend, fetch_breach_exists_today, insert_breach_history, fetch_consecutive_breaches, fetch_drift_tracking, update_drift_tracking, insert_drift_tracking, reset_drift_tracking, fetch_retry_comparison, fetch_prompt_comparison, fetch_feature_concentration, fetch_request_comparison]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
