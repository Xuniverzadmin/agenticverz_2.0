# hoc_cus_integrations_L5_engines_cus_integration_service

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/cus_integration_service.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Customer integration service - LLM BYOK, SDK, RAG management

## Intent

**Role:** Customer integration service - LLM BYOK, SDK, RAG management
**Reference:** SWEEP-03 Batch 3, PIN-468
**Callers:** integrations_facade.py

## Purpose

CusIntegrationService (SWEEP-03 Batch 3)

---

## Functions

### `get_cus_integration_service() -> CusIntegrationService`
- **Async:** No
- **Docstring:** Get the CusIntegrationService instance.  Returns:
- **Calls:** get_cus_integration_engine

## Attributes

- `__all__` (line 60)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.services.cus_integration_engine` |

## Callers

integrations_facade.py

## Export Contract

```yaml
exports:
  functions:
    - name: get_cus_integration_service
      signature: "get_cus_integration_service() -> CusIntegrationService"
  classes: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
