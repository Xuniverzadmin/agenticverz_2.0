# hoc_cus_policies_L5_engines_lessons_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/lessons_engine.py` |
| Layer | L5 — Domain Engine (System Truth) |
| Domain | policies |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Lessons learned creation and management (domain logic)

## Intent

**Role:** Lessons learned creation and management (domain logic)
**Reference:** PIN-470, PIN-411, PIN-468, POLICIES_DOMAIN_AUDIT.md Section 11
**Callers:** IncidentEngine, Worker runtime, API endpoints

## Purpose

Lessons Learned Engine (L4 Domain Logic)

---

## Functions

### `is_valid_transition(from_status: str, to_status: str) -> bool`
- **Async:** No
- **Docstring:** Check if a state transition is valid.
- **Calls:** get, set

### `get_threshold_band(utilization: float) -> str`
- **Async:** No
- **Docstring:** Get the threshold band for a utilization percentage.

### `get_lessons_learned_engine() -> LessonsLearnedEngine`
- **Async:** No
- **Docstring:** Get the singleton LessonsLearnedEngine instance.
- **Calls:** LessonsLearnedEngine

## Classes

### `LessonsLearnedEngine`
- **Docstring:** L4 Domain Engine for lesson creation and management.
- **Methods:** __init__, _get_driver, detect_lesson_from_failure, detect_lesson_from_near_threshold, detect_lesson_from_critical_success, emit_near_threshold, emit_critical_success, list_lessons, get_lesson, convert_lesson_to_draft, defer_lesson, dismiss_lesson, get_lesson_stats, reactivate_deferred_lesson, _is_debounced, _create_lesson, _generate_failure_description, _generate_failure_proposed_action, get_expired_deferred_lessons, reactivate_expired_deferred_lessons

## Attributes

- `logger` (line 74)
- `LESSONS_CREATION_FAILED` (line 80)
- `LESSON_TYPE_FAILURE` (line 91)
- `LESSON_TYPE_NEAR_THRESHOLD` (line 92)
- `LESSON_TYPE_CRITICAL_SUCCESS` (line 93)
- `LESSON_STATUS_PENDING` (line 95)
- `LESSON_STATUS_CONVERTED` (line 96)
- `LESSON_STATUS_DEFERRED` (line 97)
- `LESSON_STATUS_DISMISSED` (line 98)
- `VALID_TRANSITIONS: dict[str, set[str]]` (line 111)
- `SEVERITY_CRITICAL` (line 127)
- `SEVERITY_HIGH` (line 128)
- `SEVERITY_MEDIUM` (line 129)
- `SEVERITY_LOW` (line 130)
- `SEVERITY_NONE` (line 131)
- `NEAR_THRESHOLD_PERCENT` (line 141)
- `DEBOUNCE_WINDOW_HOURS` (line 142)
- `THRESHOLD_BANDS` (line 146)
- `_lessons_engine: Optional[LessonsLearnedEngine]` (line 1072)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.incidents.L6_drivers.lessons_driver` |
| Cross-Domain | `app.hoc.cus.incidents.L6_drivers.lessons_driver` |
| External | `app.hoc.cus.hoc_spine.services.time`, `prometheus_client`, `sqlalchemy`, `sqlalchemy.orm`, `sqlmodel` |

## Callers

IncidentEngine, Worker runtime, API endpoints

## Export Contract

```yaml
exports:
  functions:
    - name: is_valid_transition
      signature: "is_valid_transition(from_status: str, to_status: str) -> bool"
    - name: get_threshold_band
      signature: "get_threshold_band(utilization: float) -> str"
    - name: get_lessons_learned_engine
      signature: "get_lessons_learned_engine() -> LessonsLearnedEngine"
  classes:
    - name: LessonsLearnedEngine
      methods: [detect_lesson_from_failure, detect_lesson_from_near_threshold, detect_lesson_from_critical_success, emit_near_threshold, emit_critical_success, list_lessons, get_lesson, convert_lesson_to_draft, defer_lesson, dismiss_lesson, get_lesson_stats, reactivate_deferred_lesson, get_expired_deferred_lessons, reactivate_expired_deferred_lessons]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
