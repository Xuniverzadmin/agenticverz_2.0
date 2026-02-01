# hoc_cus_incidents_L5_engines_incident_severity_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/incident_severity_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Severity calculation and escalation decisions for incidents

## Intent

**Role:** Severity calculation and escalation decisions for incidents
**Reference:** PIN-470, INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md — Violation I.3
**Callers:** incident_aggregator.py (L6), incident engines

## Purpose

Incident Severity Engine (L4)

---

## Functions

### `generate_incident_title(trigger_type: str, trigger_value: str) -> str`
- **Async:** No
- **Docstring:** Generate human-readable incident title.  This is presentation logic but lives here because it's domain-specific.
- **Calls:** get

## Classes

### `SeverityConfig`
- **Docstring:** Configuration for severity decisions.
- **Methods:** default
- **Class Variables:** severity_thresholds: Dict[str, int]

### `IncidentSeverityEngine`
- **Docstring:** L4 Engine for incident severity decisions.
- **Methods:** __init__, get_initial_severity, calculate_severity_for_calls, should_escalate

## Attributes

- `TRIGGER_SEVERITY_MAP: Dict[str, str]` (line 75)
- `DEFAULT_SEVERITY` (line 83)
- `__all__` (line 212)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.killswitch` |

## Callers

incident_aggregator.py (L6), incident engines

## Export Contract

```yaml
exports:
  functions:
    - name: generate_incident_title
      signature: "generate_incident_title(trigger_type: str, trigger_value: str) -> str"
  classes:
    - name: SeverityConfig
      methods: [default]
    - name: IncidentSeverityEngine
      methods: [get_initial_severity, calculate_severity_for_calls, should_escalate]
```

## PIN-507 Law 1 Amendment (2026-02-01)

All severity logic moved to `incidents/L5_schemas/severity_policy.py`. This file is now a tombstone that re-exports for backward compatibility. Canonical import: `app.hoc.cus.incidents.L5_schemas.severity_policy`. Severity logic is pure stateless policy (no DB, no I/O) — it belongs in L5_schemas under the `*_policy.py` naming convention.

## Evaluation Notes

- **Disposition:** TOMBSTONE
- **Rationale:** Content moved to `incidents/L5_schemas/severity_policy.py` per PIN-507 Law 1. Re-exports retained for backward compat. Remove after cleansing cycle.
