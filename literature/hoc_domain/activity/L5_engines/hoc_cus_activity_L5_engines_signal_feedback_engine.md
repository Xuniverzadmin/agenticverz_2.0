# hoc_cus_activity_L5_engines_signal_feedback_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/activity/L5_engines/signal_feedback_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | activity |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Signal feedback engine for acknowledging/suppressing signals

## Intent

**Role:** Signal feedback engine for acknowledging/suppressing signals
**Reference:** PIN-470, Activity Domain
**Callers:** activity_facade.py

## Purpose

Signal feedback engine for user interactions with signals.

---

## Classes

### `AcknowledgeResult`
- **Docstring:** Result of acknowledging a signal.
- **Class Variables:** signal_id: str, acknowledged: bool, acknowledged_at: datetime, acknowledged_by: Optional[str], message: str

### `SuppressResult`
- **Docstring:** Result of suppressing a signal.
- **Class Variables:** signal_id: str, suppressed: bool, suppressed_at: datetime, suppressed_by: Optional[str], suppressed_until: Optional[datetime], reason: Optional[str], message: str

### `SignalFeedbackStatus`
- **Docstring:** Current feedback status for a signal.
- **Class Variables:** acknowledged: bool, acknowledged_by: Optional[str], acknowledged_at: Optional[datetime], suppressed: bool, suppressed_until: Optional[datetime]

### `SignalFeedbackService`
- **Docstring:** Service for managing user feedback on signals.
- **Methods:** __init__, acknowledge_signal, suppress_signal, get_signal_feedback_status, get_bulk_signal_feedback

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.hoc.cus.hoc_spine.services.time` |

## Callers

activity_facade.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: AcknowledgeResult
      methods: []
    - name: SuppressResult
      methods: []
    - name: SignalFeedbackStatus
      methods: []
    - name: SignalFeedbackService
      methods: [acknowledge_signal, suppress_signal, get_signal_feedback_status, get_bulk_signal_feedback]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
