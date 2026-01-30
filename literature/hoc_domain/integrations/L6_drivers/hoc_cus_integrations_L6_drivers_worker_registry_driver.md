# hoc_cus_integrations_L6_drivers_worker_registry_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L6_drivers/worker_registry_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Worker discovery, status queries, capability registry driver

## Intent

**Role:** Worker discovery, status queries, capability registry driver
**Reference:** PIN-470, PIN-242 (Baseline Freeze), ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** L5 engines, L2 APIs

## Purpose

Worker Registry Driver (L6)

---

## Functions

### `get_worker_registry_service(session: Session) -> WorkerRegistryService`
- **Async:** No
- **Docstring:** Get a WorkerRegistryService instance.
- **Calls:** WorkerRegistryService

## Classes

### `WorkerRegistryError(Exception)`
- **Docstring:** Base exception for worker registry errors.

### `WorkerNotFoundError(WorkerRegistryError)`
- **Docstring:** Raised when a worker is not found.

### `WorkerUnavailableError(WorkerRegistryError)`
- **Docstring:** Raised when a worker is not available.

### `WorkerRegistryService`
- **Docstring:** Service for worker registry operations.
- **Methods:** __init__, get_worker, get_worker_or_raise, list_workers, list_available_workers, is_worker_available, get_worker_details, get_worker_summary, list_worker_summaries, register_worker, update_worker_status, deprecate_worker, get_tenant_worker_config, set_tenant_worker_config, list_tenant_worker_configs, get_effective_worker_config, is_worker_enabled_for_tenant, get_workers_for_tenant

## Attributes

- `logger` (line 44)
- `__all__` (line 418)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.tenant` |
| External | `sqlmodel` |

## Callers

L5 engines, L2 APIs

## Export Contract

```yaml
exports:
  functions:
    - name: get_worker_registry_service
      signature: "get_worker_registry_service(session: Session) -> WorkerRegistryService"
  classes:
    - name: WorkerRegistryError
      methods: []
    - name: WorkerNotFoundError
      methods: []
    - name: WorkerUnavailableError
      methods: []
    - name: WorkerRegistryService
      methods: [get_worker, get_worker_or_raise, list_workers, list_available_workers, is_worker_available, get_worker_details, get_worker_summary, list_worker_summaries, register_worker, update_worker_status, deprecate_worker, get_tenant_worker_config, set_tenant_worker_config, list_tenant_worker_configs, get_effective_worker_config, is_worker_enabled_for_tenant, get_workers_for_tenant]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
