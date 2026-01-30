# hoc_models_costsim_cb

| Field | Value |
|-------|-------|
| Path | `backend/app/models/costsim_cb.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

CostSim circuit breaker models

## Intent

**Role:** CostSim circuit breaker models
**Reference:** CostSim
**Callers:** costsim/*

## Purpose

Pure SQLAlchemy models for async database access.

---

## Classes

### `CostSimCBStateModel(Base)`
- **Docstring:** Circuit breaker state for CostSim V2.
- **Methods:** to_dict

### `CostSimCBIncidentModel(Base)`
- **Docstring:** Incident records for circuit breaker trips.
- **Methods:** get_details, to_dict

### `CostSimProvenanceModel(Base)`
- **Docstring:** Provenance records for CostSim simulations.
- **Methods:** to_dict

### `CostSimCanaryReportModel(Base)`
- **Docstring:** Canary run reports for CostSim V2 validation.
- **Methods:** get_failure_reasons, get_artifact_paths, to_dict

### `CostSimAlertQueueModel(Base)`
- **Docstring:** Alert queue for reliable alert delivery.
- **Methods:** to_dict

## Attributes

- `Base` (line 38)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.dialects.postgresql`, `sqlalchemy.orm` |

## Callers

costsim/*

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: CostSimCBStateModel
      methods: [to_dict]
    - name: CostSimCBIncidentModel
      methods: [get_details, to_dict]
    - name: CostSimProvenanceModel
      methods: [to_dict]
    - name: CostSimCanaryReportModel
      methods: [get_failure_reasons, get_artifact_paths, to_dict]
    - name: CostSimAlertQueueModel
      methods: [to_dict]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
