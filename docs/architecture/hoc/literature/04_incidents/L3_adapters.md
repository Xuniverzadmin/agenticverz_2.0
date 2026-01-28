# Incidents — L3 Adapters (1 files)

**Domain:** incidents  
**Layer:** L3_adapters  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

---

## anomaly_bridge.py
**Path:** `backend/app/hoc/cus/incidents/L3_adapters/anomaly_bridge.py`  
**Layer:** L3_adapters | **Domain:** incidents | **Lines:** 351

**Docstring:** Anomaly-to-Incident Bridge

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostAnomalyFact` |  | Pure fact emitted by analytics when a cost anomaly is detected. |
| `AnomalyIncidentBridge` | __init__, ingest, _meets_severity_threshold, _is_suppressed, _check_existing_incident, _create_incident, _build_incident_insert_sql | Bridge that accepts cost anomaly facts and creates incidents. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_anomaly_incident_bridge` | `(session) -> AnomalyIncidentBridge` | no | Factory function to get AnomalyIncidentBridge instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `uuid` | uuid | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `decimal` | Decimal | no |
| `typing` | Optional | no |
| `app.errors.governance` | GovernanceError | no |
| `app.hoc.cus.incidents.L6_drivers.incident_write_driver` | IncidentWriteDriver, get_incident_write_driver | no |
| `app.metrics` | governance_incidents_created_total | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

### Constants
`INCIDENT_SEVERITY_THRESHOLD`, `ANOMALY_SEVERITY_MAP`, `ANOMALY_TRIGGER_TYPE_MAP`

### __all__ Exports
`CostAnomalyFact`, `AnomalyIncidentBridge`, `get_anomaly_incident_bridge`, `INCIDENT_SEVERITY_THRESHOLD`

---
