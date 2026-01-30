# hoc_cus_activity_L6_drivers_run_signal_service

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/activity/L6_drivers/run_signal_service.py` |
| Layer | L6 — Domain Driver |
| Domain | activity |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

RunSignalService - updates run risk levels based on threshold signals

## Intent

**Role:** RunSignalService - updates run risk levels based on threshold signals
**Reference:** SWEEP-03
**Callers:** threshold_driver.py, llm_threshold_driver.py

## Purpose

RunSignalService (L6 Driver)

---

## Classes

### `RunSignalService`
- **Docstring:** Service for updating run risk levels based on threshold signals.
- **Methods:** __init__, update_risk_level, get_risk_level

## Attributes

- `logger` (line 47)
- `SIGNAL_TO_RISK_LEVEL` (line 56)
- `DEFAULT_RISK_LEVEL` (line 64)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy` |

## Callers

threshold_driver.py, llm_threshold_driver.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: RunSignalService
      methods: [update_risk_level, get_risk_level]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
