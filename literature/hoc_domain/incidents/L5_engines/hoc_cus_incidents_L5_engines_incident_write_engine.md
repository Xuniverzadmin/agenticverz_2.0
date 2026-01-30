# hoc_cus_incidents_L5_engines_incident_write_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/incident_write_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Incident domain write operations with audit (L5 facade over L6 driver)

## Intent

**Role:** Incident domain write operations with audit (L5 facade over L6 driver)
**Reference:** PIN-470, PIN-281, PIN-413, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** customer_incidents_adapter.py (L3)

## Purpose

Incident Write Service (L4)

---

## Functions

### `get_incident_write_service(session: 'Session') -> IncidentWriteService`
- **Async:** No
- **Docstring:** Factory function to get IncidentWriteService instance.
- **Calls:** IncidentWriteService

## Classes

### `IncidentWriteService`
- **Docstring:** L4 service for incident write operations.
- **Methods:** __init__, acknowledge_incident, resolve_incident, manual_close_incident

## Attributes

- `__all__` (line 300)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.logs.L5_engines.audit_ledger_service` |
| L6 Driver | `app.hoc.cus.incidents.L6_drivers.incident_write_driver` |
| L7 Model | `app.models.audit_ledger`, `app.models.killswitch` |
| Cross-Domain | `app.hoc.cus.logs.L5_engines.audit_ledger_service` |
| External | `sqlmodel` |

## Callers

customer_incidents_adapter.py (L3)

## Export Contract

```yaml
exports:
  functions:
    - name: get_incident_write_service
      signature: "get_incident_write_service(session: 'Session') -> IncidentWriteService"
  classes:
    - name: IncidentWriteService
      methods: [acknowledge_incident, resolve_incident, manual_close_incident]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
