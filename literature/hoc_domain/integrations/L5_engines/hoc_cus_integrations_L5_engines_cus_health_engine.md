# hoc_cus_integrations_L5_engines_cus_health_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/cus_health_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Health checking engine for customer LLM integrations

## Intent

**Role:** Health checking engine for customer LLM integrations
**Reference:** PIN-470, docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md
**Callers:** cus_integration_service.py, scheduled health checks

## Purpose

Customer Health Engine

---

## Classes

### `CusHealthService`
- **Docstring:** Service for health checking customer LLM integrations.
- **Methods:** __init__, check_health, _perform_health_check, check_all_integrations, get_health_summary, _calculate_overall_health

## Attributes

- `logger` (line 66)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.cus_models` |
| External | `app.db`, `app.hoc.cus.hoc_spine.services.cus_credential_service`, `httpx`, `sqlmodel` |

## Callers

cus_integration_service.py, scheduled health checks

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: CusHealthService
      methods: [check_health, check_all_integrations, get_health_summary]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
