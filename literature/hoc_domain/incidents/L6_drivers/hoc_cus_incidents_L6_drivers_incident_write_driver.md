# hoc_cus_incidents_L6_drivers_incident_write_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L6_drivers/incident_write_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for incident write operations

## Intent

**Role:** Data access for incident write operations
**Reference:** PIN-470, PIN-281, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** incident engines (L5)

## Purpose

Incident Write Driver (L6)

---

## Functions

### `get_incident_write_driver(session: Session) -> IncidentWriteDriver`
- **Async:** No
- **Docstring:** Factory function to get IncidentWriteDriver instance.
- **Calls:** IncidentWriteDriver

## Classes

### `IncidentWriteDriver`
- **Docstring:** L6 driver for incident write operations.
- **Methods:** __init__, update_incident_acknowledged, update_incident_resolved, create_incident_event, refresh_incident, insert_incident, update_run_incident_count, update_trace_incident_id, insert_prevention_record, insert_policy_proposal, fetch_suppressing_policy, fetch_incidents_by_run_id

## Attributes

- `__all__` (line 537)

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
    - name: get_incident_write_driver
      signature: "get_incident_write_driver(session: Session) -> IncidentWriteDriver"
  classes:
    - name: IncidentWriteDriver
      methods: [update_incident_acknowledged, update_incident_resolved, create_incident_event, refresh_incident, insert_incident, update_run_incident_count, update_trace_incident_id, insert_prevention_record, insert_policy_proposal, fetch_suppressing_policy, fetch_incidents_by_run_id]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
