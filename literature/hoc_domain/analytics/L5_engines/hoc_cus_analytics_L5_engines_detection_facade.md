# hoc_cus_analytics_L5_engines_detection_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/detection_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Detection Facade - Centralized access to anomaly detection operations

## Intent

**Role:** Detection Facade - Centralized access to anomaly detection operations
**Reference:** PIN-470, GAP-102 (Anomaly Detection API)
**Callers:** L2 detection.py API, SDK, Worker

## Purpose

Detection Facade (L5 Domain Engine)

---

## Functions

### `get_detection_facade() -> DetectionFacade`
- **Async:** No
- **Docstring:** Get the detection facade instance.  This is the recommended way to access detection operations
- **Calls:** DetectionFacade

## Classes

### `DetectionType(str, Enum)`
- **Docstring:** Types of anomaly detection.

### `AnomalyStatus(str, Enum)`
- **Docstring:** Anomaly resolution status.

### `DetectionResult`
- **Docstring:** Result of a detection run.
- **Methods:** to_dict
- **Class Variables:** success: bool, detection_type: str, anomalies_detected: int, anomalies_created: int, incidents_created: int, tenant_id: str, run_at: str, error: Optional[str]

### `AnomalyInfo`
- **Docstring:** Anomaly information.
- **Methods:** to_dict
- **Class Variables:** id: str, tenant_id: str, detection_type: str, anomaly_type: str, severity: str, status: str, entity_type: str, entity_id: Optional[str], current_value: float, expected_value: float, deviation_pct: float, message: str, derived_cause: Optional[str], incident_id: Optional[str], detected_at: str, resolved_at: Optional[str], metadata: Dict[str, Any]

### `DetectionStatusInfo`
- **Docstring:** Detection engine status.
- **Methods:** to_dict
- **Class Variables:** healthy: bool, engines: Dict[str, Dict[str, Any]], last_run: Optional[str], next_scheduled_run: Optional[str]

### `DetectionFacade`
- **Docstring:** Facade for anomaly detection operations.
- **Methods:** __init__, cost_detector, run_detection, _run_cost_detection, list_anomalies, get_anomaly, resolve_anomaly, acknowledge_anomaly, get_detection_status

## Attributes

- `logger` (line 64)
- `_facade_instance: Optional[DetectionFacade]` (line 543)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.analytics.L5_engines.cost_anomaly_detector` |

## Callers

L2 detection.py API, SDK, Worker

## Export Contract

```yaml
exports:
  functions:
    - name: get_detection_facade
      signature: "get_detection_facade() -> DetectionFacade"
  classes:
    - name: DetectionType
      methods: []
    - name: AnomalyStatus
      methods: []
    - name: DetectionResult
      methods: [to_dict]
    - name: AnomalyInfo
      methods: [to_dict]
    - name: DetectionStatusInfo
      methods: [to_dict]
    - name: DetectionFacade
      methods: [cost_detector, run_detection, list_anomalies, get_anomaly, resolve_anomaly, acknowledge_anomaly, get_detection_status]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
