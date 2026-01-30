# hoc_cus_analytics_L5_engines_cost_anomaly_detector

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/cost_anomaly_detector.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Cost anomaly detection business logic (System Truth)

## Intent

**Role:** Cost anomaly detection business logic (System Truth)
**Reference:** PIN-470, PIN-240
**Callers:** tests, future background job

## Purpose

M29 Cost Anomaly Detector - Aligned Rules

---

## Functions

### `classify_severity(deviation_pct: float) -> AnomalySeverity`
- **Async:** No
- **Docstring:** Classify severity based on percentage deviation.  Plan alignment:

### `async run_anomaly_detection(session: Session, tenant_id: str) -> List[CostAnomaly]`
- **Async:** Yes
- **Docstring:** Run anomaly detection and persist results.
- **Calls:** CostAnomalyDetector, debug, detect_all, info, len, persist_anomalies

### `async run_anomaly_detection_with_facts(session: Session, tenant_id: str) -> dict`
- **Async:** Yes
- **Docstring:** Run anomaly detection and emit CostAnomalyFact for HIGH anomalies.  R1 RESOLUTION: Analytics no longer creates incidents directly.
- **Calls:** CostAnomalyFact, append, float, info, int, run_anomaly_detection, str

### `async run_anomaly_detection_with_governance(session: Session, tenant_id: str) -> dict`
- **Async:** Yes
- **Docstring:** DEPRECATED: Use run_anomaly_detection_with_facts + AnomalyIncidentBridge.  This function now emits facts and uses the bridge for incident creation.
- **Calls:** AnomalyIncidentBridge, append, ingest, run_anomaly_detection_with_facts

## Classes

### `AnomalyType(str, Enum)`
- **Docstring:** Cost anomaly types - minimal set.

### `AnomalySeverity(str, Enum)`
- **Docstring:** Aligned severity bands per plan.

### `DerivedCause(str, Enum)`
- **Docstring:** Deterministic cause derivation.

### `DetectedAnomaly`
- **Docstring:** A detected cost anomaly.
- **Class Variables:** anomaly_type: AnomalyType, severity: AnomalySeverity, entity_type: str, entity_id: Optional[str], current_value_cents: float, expected_value_cents: float, deviation_pct: float, message: str, breach_count: int, derived_cause: DerivedCause, metadata: dict

### `CostAnomalyDetector`
- **Docstring:** Detects cost anomalies with aligned rules.
- **Methods:** __init__, detect_all, detect_absolute_spikes, _detect_entity_spikes, _detect_tenant_spike, detect_sustained_drift, detect_budget_issues, _check_budget_threshold, _record_breach_and_get_consecutive_count, _reset_breach_history, _update_drift_tracking, _reset_drift_tracking, _derive_cause, _format_spike_message, persist_anomalies

## Attributes

- `logger` (line 57)
- `ABSOLUTE_SPIKE_THRESHOLD` (line 98)
- `CONSECUTIVE_INTERVALS_REQUIRED` (line 101)
- `SUSTAINED_DRIFT_THRESHOLD` (line 104)
- `DRIFT_DAYS_REQUIRED` (line 107)
- `SEVERITY_BANDS` (line 110)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.analytics.L6_drivers.cost_anomaly_driver` |
| External | `__future__`, `app.db`, `app.hoc.cus.incidents.L3_adapters.anomaly_bridge`, `sqlmodel` |

## Callers

tests, future background job

## Export Contract

```yaml
exports:
  functions:
    - name: classify_severity
      signature: "classify_severity(deviation_pct: float) -> AnomalySeverity"
    - name: run_anomaly_detection
      signature: "async run_anomaly_detection(session: Session, tenant_id: str) -> List[CostAnomaly]"
    - name: run_anomaly_detection_with_facts
      signature: "async run_anomaly_detection_with_facts(session: Session, tenant_id: str) -> dict"
    - name: run_anomaly_detection_with_governance
      signature: "async run_anomaly_detection_with_governance(session: Session, tenant_id: str) -> dict"
  classes:
    - name: AnomalyType
      methods: []
    - name: AnomalySeverity
      methods: []
    - name: DerivedCause
      methods: []
    - name: DetectedAnomaly
      methods: []
    - name: CostAnomalyDetector
      methods: [detect_all, detect_absolute_spikes, detect_sustained_drift, detect_budget_issues, persist_anomalies]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
