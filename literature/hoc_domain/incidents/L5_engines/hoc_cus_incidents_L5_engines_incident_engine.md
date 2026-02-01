# hoc_cus_incidents_L5_engines_incident_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/incident_engine.py` |
| Layer | L5 — Domain Engine (System Truth) |
| Domain | incidents |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Incident creation decision-making (domain logic)

## Intent

**Role:** Incident creation decision-making (domain logic)
**Reference:** PIN-470, PIN-370, PIN-468 (Phase-2.5A L4/L6 Segregation)
**Callers:** Worker runtime, API endpoints

## Purpose

Incident Engine (L4 Domain Logic)

---

## Functions

### `_get_lessons_learned_engine()`
- **Async:** No
- **Docstring:** Get the LessonsLearnedEngine singleton (lazy import).
- **Calls:** get_lessons_learned_engine

### `get_incident_engine() -> IncidentEngine`
- **Async:** No
- **Docstring:** Get or create singleton incident engine instance.
- **Calls:** IncidentEngine

## Classes

### `IncidentEngine`
- **Docstring:** L4 Domain Engine for incident creation.
- **Methods:** __init__, _get_driver, _check_policy_suppression, _write_prevention_record, create_incident_for_run, create_incident_for_failed_run, _maybe_create_policy_proposal, _generate_title, check_and_create_incident, create_incident_for_all_runs, _extract_error_code, get_incidents_for_run

## Attributes

- `logger` (line 84)
- `INCIDENT_OUTCOME_SUCCESS` (line 120)
- `INCIDENT_OUTCOME_FAILURE` (line 121)
- `INCIDENT_OUTCOME_BLOCKED` (line 122)
- `INCIDENT_OUTCOME_ABORTED` (line 123)
- `SEVERITY_NONE` (line 126)
- `FAILURE_SEVERITY_MAP` (line 129)
- `FAILURE_CATEGORY_MAP` (line 148)
- `_incident_engine: Optional[IncidentEngine]` (line 897)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.policies.L5_engines.lessons_engine` |
| L6 Driver | `app.hoc.cus.incidents.L6_drivers.incident_write_driver` |
| Cross-Domain | `app.hoc.cus.policies.L5_engines.lessons_engine` |
| External | `app.hoc.cus.hoc_spine.services.time`, `sqlalchemy`, `sqlalchemy.orm`, `sqlmodel` |

## Callers

Worker runtime, API endpoints

## Export Contract

```yaml
exports:
  functions:
    - name: get_incident_engine
      signature: "get_incident_engine() -> IncidentEngine"
  classes:
    - name: IncidentEngine
      methods: [create_incident_for_run, create_incident_for_failed_run, check_and_create_incident, create_incident_for_all_runs, get_incidents_for_run]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
