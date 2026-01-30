# hoc_cus_policies_L5_engines_limits_simulation_service

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/limits_simulation_service.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Limits simulation service - pre-execution limit checks

## Intent

**Role:** Limits simulation service - pre-execution limit checks
**Reference:** SWEEP-03 Batch 2, PIN-LIM-04
**Callers:** simulate.py

## Purpose

LimitsSimulationService (SWEEP-03 Batch 2)

---

## Functions

### `get_limits_simulation_service(session: 'AsyncSession') -> LimitsSimulationService`
- **Async:** No
- **Docstring:** Get the LimitsSimulationService instance.  Args:
- **Calls:** get_limits_simulation_engine

## Attributes

- `LimitsSimulationService` (line 54)
- `__all__` (line 73)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.services.limits.simulation_engine`, `sqlalchemy.ext.asyncio` |

## Callers

simulate.py

## Export Contract

```yaml
exports:
  functions:
    - name: get_limits_simulation_service
      signature: "get_limits_simulation_service(session: 'AsyncSession') -> LimitsSimulationService"
  classes: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
