# hoc_models_execution_envelope

| Field | Value |
|-------|-------|
| Path | `backend/app/models/execution_envelope.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Execution envelope models for implicit authority hardening

## Intent

**Role:** Execution envelope models for implicit authority hardening
**Reference:** PIN-330
**Callers:** auth/execution_envelope.py, worker/*

## Purpose

Execution Envelope Database Models - PIN-330 Implicit Authority Hardening

---

## Classes

### `ExecutionEnvelopeModel(Base)`
- **Docstring:** Execution envelope for implicit authority hardening.
- **Methods:** to_dict

### `ExecutionEnvelopeStats(Base)`
- **Docstring:** Aggregate statistics for execution envelopes.
- **Methods:** to_dict

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.costsim_cb` |
| External | `sqlalchemy`, `sqlalchemy.dialects.postgresql` |

## Callers

auth/execution_envelope.py, worker/*

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: ExecutionEnvelopeModel
      methods: [to_dict]
    - name: ExecutionEnvelopeStats
      methods: [to_dict]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
