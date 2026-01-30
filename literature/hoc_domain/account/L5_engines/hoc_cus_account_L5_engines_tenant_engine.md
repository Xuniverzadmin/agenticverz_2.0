# hoc_cus_account_L5_engines_tenant_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/account/L5_engines/tenant_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | account |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Tenant domain engine - business logic for tenant operations

## Intent

**Role:** Tenant domain engine - business logic for tenant operations
**Reference:** PIN-470, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
**Callers:** L2 APIs, L5 workers

## Purpose

Tenant Engine (L5)

---

## Functions

### `get_tenant_engine(session: Session) -> TenantEngine`
- **Async:** No
- **Docstring:** Get a TenantEngine instance.
- **Calls:** TenantEngine

## Classes

### `TenantEngineError(Exception)`
- **Docstring:** Base exception for tenant engine errors.

### `QuotaExceededError(TenantEngineError)`
- **Docstring:** Raised when a quota limit is exceeded.
- **Methods:** __init__

### `TenantEngine`
- **Docstring:** L4 Engine for tenant business logic.
- **Methods:** __init__, create_tenant, get_tenant, get_tenant_by_slug, update_plan, suspend, create_membership_with_default, create_api_key, list_api_keys, revoke_api_key, check_run_quota, check_token_quota, increment_usage, _maybe_reset_daily_counter, record_usage, get_usage_summary, create_run, complete_run, list_runs

## Attributes

- `logger` (line 57)
- `__all__` (line 577)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.account.L6_drivers.tenant_driver` |
| L7 Model | `app.models.tenant` |
| External | `__future__`, `app.hoc.hoc_spine.services.time`, `sqlmodel` |

## Callers

L2 APIs, L5 workers

## Export Contract

```yaml
exports:
  functions:
    - name: get_tenant_engine
      signature: "get_tenant_engine(session: Session) -> TenantEngine"
  classes:
    - name: TenantEngineError
      methods: []
    - name: QuotaExceededError
      methods: []
    - name: TenantEngine
      methods: [create_tenant, get_tenant, get_tenant_by_slug, update_plan, suspend, create_membership_with_default, create_api_key, list_api_keys, revoke_api_key, check_run_quota, check_token_quota, increment_usage, record_usage, get_usage_summary, create_run, complete_run, list_runs]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
