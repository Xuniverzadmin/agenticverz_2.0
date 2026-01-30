# hoc_models_m10_recovery

| Field | Value |
|-------|-------|
| Path | `backend/app/models/m10_recovery.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

M10 recovery data models

## Intent

**Role:** M10 recovery data models
**Reference:** M10 Recovery
**Callers:** recovery services, workers

## Purpose

SQLAlchemy models for M10 Recovery Suggestion Engine.

---

## Classes

### `SuggestionInput(Base)`
- **Docstring:** Structured inputs that contributed to a recovery suggestion.
- **Methods:** to_dict

### `SuggestionAction(Base)`
- **Docstring:** Catalog of available recovery actions with templates.
- **Methods:** to_dict, matches_error, matches_skill

### `SuggestionProvenance(Base)`
- **Docstring:** Complete lineage of how a recovery suggestion was generated and processed.
- **Methods:** to_dict

## Attributes

- `Base` (line 43)
- `INPUT_TYPES` (line 290)
- `ACTION_TYPES` (line 299)
- `EVENT_TYPES` (line 310)
- `EXECUTION_STATUSES` (line 325)
- `__all__` (line 339)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.dialects.postgresql`, `sqlalchemy.orm`, `sqlalchemy.sql` |

## Callers

recovery services, workers

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: SuggestionInput
      methods: [to_dict]
    - name: SuggestionAction
      methods: [to_dict, matches_error, matches_skill]
    - name: SuggestionProvenance
      methods: [to_dict]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
