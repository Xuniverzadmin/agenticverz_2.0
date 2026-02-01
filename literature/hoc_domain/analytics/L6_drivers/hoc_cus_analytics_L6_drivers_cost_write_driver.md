# hoc_cus_analytics_L6_drivers_cost_write_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L6_drivers/cost_write_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for cost write operations

## Intent

**Role:** Data access for cost write operations
**Reference:** PIN-470, PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** cost_write_engine.py (L5 engine)

## Purpose

Cost Write Driver (L6)

---

## Functions

### `get_cost_write_driver(session: Session) -> CostWriteDriver`
- **Async:** No
- **Docstring:** Factory function to get CostWriteDriver instance.
- **Calls:** CostWriteDriver

## Classes

### `CostWriteDriver`
- **Docstring:** L6 driver for cost write operations.
- **Methods:** __init__, create_feature_tag, update_feature_tag, create_cost_record, create_or_update_budget

## Attributes

- `__all__` (line 248)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.db`, `app.hoc.cus.hoc_spine.services.time`, `sqlmodel` |

## Callers

cost_write_engine.py (L5 engine)

## Export Contract

```yaml
exports:
  functions:
    - name: get_cost_write_driver
      signature: "get_cost_write_driver(session: Session) -> CostWriteDriver"
  classes:
    - name: CostWriteDriver
      methods: [create_feature_tag, update_feature_tag, create_cost_record, create_or_update_budget]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
