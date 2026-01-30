# hoc_cus_incidents_L5_engines_incident_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/incident_driver.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Incident Domain Engine - Internal orchestration for incident operations

## Intent

**Role:** Incident Domain Engine - Internal orchestration for incident operations
**Reference:** PIN-470, FACADE_CONSOLIDATION_PLAN.md, PIN-454 (RAC)
**Callers:** worker runtime, governance services, transaction coordinator

## Purpose

Incident Domain Driver (INTERNAL)

---

## Functions

### `get_incident_driver(db_url: Optional[str]) -> IncidentDriver`
- **Async:** No
- **Docstring:** Get the incident driver instance.  This is the recommended way to access incident operations from
- **Calls:** IncidentDriver

## Classes

### `IncidentDriver`
- **Docstring:** Driver for Incident domain operations (INTERNAL).
- **Methods:** __init__, _engine, check_and_create_incident, create_incident_for_run, _emit_ack, get_incidents_for_run

## Attributes

- `logger` (line 52)
- `RAC_ENABLED` (line 55)
- `_driver_instance: Optional[IncidentDriver]` (line 252)
- `IncidentFacade` (line 278)
- `get_incident_facade` (line 279)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.incidents.L5_engines.incident_engine` |
| External | `app.hoc.hoc_spine.schemas.rac_models`, `app.hoc.hoc_spine.services.audit_store` |

## Callers

worker runtime, governance services, transaction coordinator

## Export Contract

```yaml
exports:
  functions:
    - name: get_incident_driver
      signature: "get_incident_driver(db_url: Optional[str]) -> IncidentDriver"
  classes:
    - name: IncidentDriver
      methods: [check_and_create_incident, create_incident_for_run, get_incidents_for_run]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
