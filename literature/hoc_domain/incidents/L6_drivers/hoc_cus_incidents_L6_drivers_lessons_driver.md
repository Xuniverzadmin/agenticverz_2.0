# hoc_cus_incidents_L6_drivers_lessons_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L6_drivers/lessons_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for lessons_learned operations

## Intent

**Role:** Data access for lessons_learned operations
**Reference:** PIN-470, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** LessonsLearnedEngine (L5)

## Purpose

Lessons Driver (L6)

---

## Functions

### `get_lessons_driver(session: Session) -> LessonsDriver`
- **Async:** No
- **Docstring:** Factory function to get LessonsDriver instance.
- **Calls:** LessonsDriver

## Classes

### `LessonsDriver`
- **Docstring:** L6 driver for lessons_learned operations.
- **Methods:** __init__, insert_lesson, fetch_lesson_by_id, fetch_lessons_list, fetch_lesson_stats, update_lesson_deferred, update_lesson_dismissed, update_lesson_converted, update_lesson_reactivated, fetch_debounce_count, fetch_expired_deferred, insert_policy_proposal_from_lesson

## Attributes

- `__all__` (line 646)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlmodel` |

## Callers

LessonsLearnedEngine (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_lessons_driver
      signature: "get_lessons_driver(session: Session) -> LessonsDriver"
  classes:
    - name: LessonsDriver
      methods: [insert_lesson, fetch_lesson_by_id, fetch_lessons_list, fetch_lesson_stats, update_lesson_deferred, update_lesson_dismissed, update_lesson_converted, update_lesson_reactivated, fetch_debounce_count, fetch_expired_deferred, insert_policy_proposal_from_lesson]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
