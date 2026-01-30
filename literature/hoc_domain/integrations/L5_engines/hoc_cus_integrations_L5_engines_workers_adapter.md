# hoc_cus_integrations_L5_engines_workers_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/workers_adapter.py` |
| Layer | L3 — Boundary Adapter |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Worker execution boundary adapter (L2 → L3 → L4)

## Intent

**Role:** Worker execution boundary adapter (L2 → L3 → L4)
**Reference:** PIN-258 Phase F-3 Workers Cluster
**Callers:** workers.py (L2)

## Purpose

Workers Boundary Adapter (L3)

---

## Functions

### `get_workers_adapter() -> WorkersAdapter`
- **Async:** No
- **Docstring:** Get the singleton WorkersAdapter instance.  This is the ONLY way L2 should obtain a workers adapter.
- **Calls:** WorkersAdapter

## Classes

### `WorkersAdapter`
- **Docstring:** Boundary adapter for worker operations.
- **Methods:** execute_worker, replay_execution, calculate_cost_cents, convert_brand_request

## Attributes

- `_workers_adapter_instance: Optional[WorkersAdapter]` (line 177)
- `__all__` (line 202)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.commands.worker_execution_command` |

## Callers

workers.py (L2)

## Export Contract

```yaml
exports:
  functions:
    - name: get_workers_adapter
      signature: "get_workers_adapter() -> WorkersAdapter"
  classes:
    - name: WorkersAdapter
      methods: [execute_worker, replay_execution, calculate_cost_cents, convert_brand_request]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
