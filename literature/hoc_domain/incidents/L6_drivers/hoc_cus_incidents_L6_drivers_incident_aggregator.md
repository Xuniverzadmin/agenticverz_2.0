# hoc_cus_incidents_L6_drivers_incident_aggregator

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L6_drivers/incident_aggregator.py` |
| Layer | L6 — Domain Driver |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Incident aggregation persistence - pure data access

## Intent

**Role:** Incident aggregation persistence - pure data access
**Reference:** PIN-470, PIN-242 (Baseline Freeze), INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md — Violation I.3
**Callers:** L2 APIs, L5 workers

## Purpose

Incident Aggregation Driver - Prevents Incident Explosion Under Load

---

## Functions

### `create_incident_aggregator(config: Optional[IncidentAggregatorConfig]) -> IncidentAggregator`
- **Async:** No
- **Docstring:** Create an IncidentAggregator with canonical dependencies.  This is the ONLY sanctioned way to create an aggregator.
- **Calls:** IncidentAggregator

## Classes

### `IncidentAggregatorConfig`
- **Docstring:** Configuration for incident aggregation behavior (L6 persistence config only).
- **Class Variables:** aggregation_window_seconds: int, max_incidents_per_tenant_per_hour: int, max_related_calls_per_incident: int, incident_cooldown_seconds: int, auto_resolve_after_seconds: int

### `IncidentKey`
- **Docstring:** Grouping key for incident aggregation.
- **Methods:** __hash__, __eq__, from_event
- **Class Variables:** tenant_id: str, trigger_type: str, window_start: datetime

### `IncidentAggregator`
- **Docstring:** L6 Driver for intelligent incident aggregation.
- **Methods:** __init__, get_or_create_incident, _find_open_incident, _can_create_incident, _get_rate_limit_incident, _create_incident, _add_call_to_incident, _add_incident_event, resolve_stale_incidents, get_incident_stats

## Attributes

- `ClockFn` (line 69)
- `UuidFn` (line 70)
- `logger` (line 72)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Schema | `app.hoc.cus.incidents.L5_schemas.severity_policy` (PIN-507 Law 1) |
| L5 Engine | ~~`app.hoc.cus.incidents.L5_engines.incident_severity_engine`~~ REMOVED (PIN-507 Law 1) |
| L7 Model | `app.models.killswitch` |
| External | `app.utils.runtime`, `sqlalchemy`, `sqlmodel` |

## Callers

L2 APIs, L5 workers

## Export Contract

```yaml
exports:
  functions:
    - name: create_incident_aggregator
      signature: "create_incident_aggregator(config: Optional[IncidentAggregatorConfig]) -> IncidentAggregator"
  classes:
    - name: IncidentAggregatorConfig
      methods: []
    - name: IncidentKey
      methods: [from_event]
    - name: IncidentAggregator
      methods: [get_or_create_incident, resolve_stale_incidents, get_incident_stats]
```

## PIN-507 Law 1 Amendment (2026-02-01)

`IncidentSeverityEngine`, `SeverityConfig`, `generate_incident_title` import changed from `L5_engines.incident_severity_engine` → `L5_schemas.severity_policy`. Law 1: L6 must not reach up to L5 engines. Severity logic is pure stateless policy, canonically belonging in L5_schemas as a `*_policy.py` file. CI guard `check_l6_no_l5_engine_imports` prevents regression.

## Evaluation Notes

- **Disposition:** KEEP
- **Rationale:** Core L6 driver for incident aggregation. L6→L5 engine import remediated per PIN-507 Law 1.
