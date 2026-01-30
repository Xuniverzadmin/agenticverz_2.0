# hoc_models_feedback

| Field | Value |
|-------|-------|
| Path | `backend/app/models/feedback.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Feedback data models

## Intent

**Role:** Feedback data models
**Reference:** Feedback System
**Callers:** feedback API, services

## Purpose

Pattern Feedback Models (PB-S3)

---

## Classes

### `PatternFeedback(Base)`
- **Docstring:** Pattern feedback record - observation without action.

### `PatternFeedbackCreate(BaseModel)`
- **Docstring:** Input model for creating pattern feedback.
- **Class Variables:** tenant_id: str, pattern_type: str, severity: str, description: str, signature: Optional[str], provenance: list[str], occurrence_count: int, time_window_minutes: Optional[int], threshold_used: Optional[str], metadata: Optional[dict]

### `PatternFeedbackResponse(BaseModel)`
- **Docstring:** Output model for pattern feedback.
- **Class Variables:** id: UUID, tenant_id: str, pattern_type: str, severity: str, description: str, signature: Optional[str], provenance: list, occurrence_count: int, time_window_minutes: Optional[int], detected_at: datetime, acknowledged: bool, acknowledged_at: Optional[datetime]

## Attributes

- `Base` (line 34)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic`, `sqlalchemy`, `sqlalchemy.dialects.postgresql`, `sqlalchemy.orm`, `sqlalchemy.sql` |

## Callers

feedback API, services

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: PatternFeedback
      methods: []
    - name: PatternFeedbackCreate
      methods: []
    - name: PatternFeedbackResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
