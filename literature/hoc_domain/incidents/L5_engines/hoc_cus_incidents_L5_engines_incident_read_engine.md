# hoc_cus_incidents_L5_engines_incident_read_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/incident_read_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Incident domain read operations (L5 facade over L6 driver)

## Intent

**Role:** Incident domain read operations (L5 facade over L6 driver)
**Reference:** PIN-470, PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** customer_incidents_adapter.py (L3)

## Purpose

Incident Read Service (L4)

---

## Functions

### `get_incident_read_service(session: 'Session') -> IncidentReadService`
- **Async:** No
- **Docstring:** Factory function to get IncidentReadService instance.
- **Calls:** IncidentReadService

## Classes

### `IncidentReadService`
- **Docstring:** L4 service for incident read operations.
- **Methods:** __init__, list_incidents, get_incident, get_incident_events, count_incidents_since, get_last_incident

## Attributes

- `__all__` (line 150)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.incidents.L6_drivers.incident_read_driver` |
| L7 Model | `app.models.killswitch` |
| External | `sqlmodel` |

## Callers

customer_incidents_adapter.py (L3)

## Export Contract

```yaml
exports:
  functions:
    - name: get_incident_read_service
      signature: "get_incident_read_service(session: 'Session') -> IncidentReadService"
  classes:
    - name: IncidentReadService
      methods: [list_incidents, get_incident, get_incident_events, count_incidents_since, get_last_incident]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
