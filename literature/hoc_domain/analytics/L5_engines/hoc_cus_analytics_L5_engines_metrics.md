# hoc_cus_analytics_L5_engines_metrics

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/metrics.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

CostSim V2 Prometheus metrics (drift detection, circuit breaker)

## Intent

**Role:** CostSim V2 Prometheus metrics (drift detection, circuit breaker)
**Reference:** PIN-470
**Callers:** sandbox, canary engines

## Purpose

Prometheus metrics for CostSim V2 drift detection.

---

## Functions

### `get_metrics() -> CostSimMetrics`
- **Async:** No
- **Docstring:** Get the global CostSim metrics instance.
- **Calls:** CostSimMetrics

### `get_alert_rules() -> str`
- **Async:** No
- **Docstring:** Get Prometheus alert rules YAML.

## Classes

### `CostSimMetrics`
- **Docstring:** Prometheus metrics for CostSim V2.
- **Methods:** __init__, _init_metrics, record_drift, record_cost_delta, record_schema_error, record_simulation_duration, record_simulation, set_circuit_breaker_state, record_provenance_log, record_canary_run, set_kl_divergence, record_cb_disabled, record_cb_enabled, record_cb_incident, set_alert_queue_depth, record_alert_send_failure, record_auto_recovery, set_consecutive_failures

## Attributes

- `logger` (line 50)
- `DRIFT_SCORE_BUCKETS` (line 54)
- `COST_DELTA_BUCKETS` (line 55)
- `DURATION_BUCKETS` (line 56)
- `_metrics: Optional[CostSimMetrics]` (line 482)
- `ALERT_RULES_YAML` (line 494)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.costsim.config`, `prometheus_client` |

## Callers

sandbox, canary engines

## Export Contract

```yaml
exports:
  functions:
    - name: get_metrics
      signature: "get_metrics() -> CostSimMetrics"
    - name: get_alert_rules
      signature: "get_alert_rules() -> str"
  classes:
    - name: CostSimMetrics
      methods: [record_drift, record_cost_delta, record_schema_error, record_simulation_duration, record_simulation, set_circuit_breaker_state, record_provenance_log, record_canary_run, set_kl_divergence, record_cb_disabled, record_cb_enabled, record_cb_incident, set_alert_queue_depth, record_alert_send_failure, record_auto_recovery, set_consecutive_failures]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
