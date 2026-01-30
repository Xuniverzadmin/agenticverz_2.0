# hoc_cus_incidents_L6_drivers_recurrence_analysis_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L6_drivers/recurrence_analysis_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Database operations for recurrence analysis - pure data access

## Intent

**Role:** Database operations for recurrence analysis - pure data access
**Reference:** PIN-470, INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md — Violation I.2
**Callers:** recurrence_analysis_engine.py (L5)

## Purpose

Recurrence Analysis Driver (L6)

---

## Classes

### `RecurrenceGroupSnapshot`
- **Docstring:** Raw recurrence group data from database.
- **Class Variables:** category: str, resolution_method: Optional[str], total_occurrences: int, distinct_days: int, occurrences_per_day: float, first_occurrence: datetime, last_occurrence: datetime, recent_incident_ids: list[str]

### `RecurrenceAnalysisDriver`
- **Docstring:** L6 Database driver for recurrence analysis.
- **Methods:** __init__, fetch_recurrence_groups, fetch_recurrence_for_category

## Attributes

- `__all__` (line 210)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

recurrence_analysis_engine.py (L5)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: RecurrenceGroupSnapshot
      methods: []
    - name: RecurrenceAnalysisDriver
      methods: [fetch_recurrence_groups, fetch_recurrence_for_category]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
