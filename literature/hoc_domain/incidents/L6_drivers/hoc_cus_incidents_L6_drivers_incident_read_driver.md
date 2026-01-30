# hoc_cus_incidents_L6_drivers_incident_read_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L6_drivers/incident_read_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for incident read operations

## Intent

**Role:** Data access for incident read operations
**Reference:** PIN-470, PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** incident engines (L5)

## Purpose

Incident Read Driver (L6)

---

## Functions

### `get_incident_read_driver(session: Session) -> IncidentReadDriver`
- **Async:** No
- **Docstring:** Factory function to get IncidentReadDriver instance.
- **Calls:** IncidentReadDriver

## Classes

### `IncidentReadDriver`
- **Docstring:** L6 driver for incident read operations.
- **Methods:** __init__, list_incidents, get_incident, get_incident_events, count_incidents_since, get_last_incident

## Attributes

- `__all__` (line 206)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.killswitch` |
| External | `sqlalchemy`, `sqlmodel` |

## Callers

incident engines (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_incident_read_driver
      signature: "get_incident_read_driver(session: Session) -> IncidentReadDriver"
  classes:
    - name: IncidentReadDriver
      methods: [list_incidents, get_incident, get_incident_events, count_incidents_since, get_last_incident]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
