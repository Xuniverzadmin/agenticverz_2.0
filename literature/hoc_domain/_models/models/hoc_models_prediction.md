# hoc_models_prediction

| Field | Value |
|-------|-------|
| Path | `backend/app/models/prediction.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Prediction data models

## Intent

**Role:** Prediction data models
**Reference:** C2 Prediction
**Callers:** predictions/*

## Purpose

Prediction Event Models (PB-S5)

---

## Classes

### `PredictionEvent(Base)`
- **Docstring:** Prediction event record - advisory only, zero side-effects.

### `PredictionEventCreate(BaseModel)`
- **Docstring:** Input model for creating prediction events.
- **Class Variables:** tenant_id: str, prediction_type: str, subject_type: str, subject_id: str, confidence_score: float, prediction_value: dict, contributing_factors: list, expires_at: datetime, notes: Optional[str]

### `PredictionEventResponse(BaseModel)`
- **Docstring:** Output model for prediction events.
- **Class Variables:** id: UUID, tenant_id: str, prediction_type: str, subject_type: str, subject_id: str, confidence_score: float, prediction_value: dict, contributing_factors: list, expires_at: datetime, created_at: datetime, is_advisory: bool, notes: Optional[str]

## Attributes

- `Base` (line 37)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic`, `sqlalchemy`, `sqlalchemy.dialects.postgresql`, `sqlalchemy.orm`, `sqlalchemy.sql` |

## Callers

predictions/*

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: PredictionEvent
      methods: []
    - name: PredictionEventCreate
      methods: []
    - name: PredictionEventResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
