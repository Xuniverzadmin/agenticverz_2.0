# hoc_cus_incidents_L5_engines_anomaly_bridge

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/anomaly_bridge.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Anomaly-to-Incident bridge (incidents-owned, not analytics)

## Intent

**Role:** Anomaly-to-Incident bridge (incidents-owned, not analytics)
**Reference:** R1 Resolution — Analytics Authority Boundary
**Callers:** Orchestrators that process CostAnomalyFact from analytics

## Purpose

Anomaly-to-Incident Bridge

---

## Functions

### `get_anomaly_incident_bridge(session) -> AnomalyIncidentBridge`
- **Async:** No
- **Docstring:** Factory function to get AnomalyIncidentBridge instance.
- **Calls:** AnomalyIncidentBridge

## Classes

### `CostAnomalyFact`
- **Docstring:** Pure fact emitted by analytics when a cost anomaly is detected.
- **Class Variables:** tenant_id: str, anomaly_id: str, anomaly_type: str, severity: str, current_value_cents: int, expected_value_cents: int, entity_type: Optional[str], entity_id: Optional[str], deviation_pct: float, confidence: float, observed_at: datetime, metadata: dict

### `AnomalyIncidentBridge`
- **Docstring:** Bridge that accepts cost anomaly facts and creates incidents.
- **Methods:** __init__, ingest, _meets_severity_threshold, _is_suppressed, _check_existing_incident, _create_incident, _build_incident_insert_sql

## Attributes

- `logger` (line 55)
- `INCIDENT_SEVERITY_THRESHOLD` (line 93)
- `ANOMALY_SEVERITY_MAP` (line 96)
- `ANOMALY_TRIGGER_TYPE_MAP` (line 104)
- `__all__` (line 346)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.incidents.L6_drivers.incident_write_driver` |
| External | `app.errors.governance`, `app.metrics`, `sqlalchemy` |

## Callers

Orchestrators that process CostAnomalyFact from analytics

## Export Contract

```yaml
exports:
  functions:
    - name: get_anomaly_incident_bridge
      signature: "get_anomaly_incident_bridge(session) -> AnomalyIncidentBridge"
  classes:
    - name: CostAnomalyFact
      methods: []
    - name: AnomalyIncidentBridge
      methods: [ingest]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
