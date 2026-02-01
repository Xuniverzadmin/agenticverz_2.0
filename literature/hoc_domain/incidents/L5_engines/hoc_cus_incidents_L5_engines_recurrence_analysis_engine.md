# hoc_cus_incidents_L5_engines_recurrence_analysis_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/recurrence_analysis_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Analyze recurring incident patterns (business logic)

## Intent

**Role:** Analyze recurring incident patterns (business logic)
**Reference:** PIN-470, docs/architecture/incidents/INCIDENTS_DOMAIN_SQL.md#9-hist-o3
**Callers:** Incidents API (L2), incidents_facade.py (L5)

## Purpose

Recurrence Analysis Service (L4 Engine)

---

## Classes

### `RecurrenceGroup`
- **Docstring:** A group of recurring incidents.
- **Class Variables:** category: str, resolution_method: str | None, total_occurrences: int, distinct_days: int, occurrences_per_day: float, first_occurrence: datetime, last_occurrence: datetime, recent_incident_ids: list[str]

### `RecurrenceResult`
- **Docstring:** Result of recurrence analysis.
- **Class Variables:** groups: list[RecurrenceGroup], baseline_days: int, total_recurring: int, generated_at: datetime

### `RecurrenceAnalysisService`
- **Docstring:** Analyze recurring incident patterns.
- **Methods:** __init__, analyze_recurrence, get_recurrence_for_category, _snapshot_to_group

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.incidents.L6_drivers.recurrence_analysis_driver` |
| External | `app.hoc.cus.hoc_spine.services.time`, `sqlalchemy.ext.asyncio` |

## Callers

Incidents API (L2), incidents_facade.py (L5)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: RecurrenceGroup
      methods: []
    - name: RecurrenceResult
      methods: []
    - name: RecurrenceAnalysisService
      methods: [analyze_recurrence, get_recurrence_for_category]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
