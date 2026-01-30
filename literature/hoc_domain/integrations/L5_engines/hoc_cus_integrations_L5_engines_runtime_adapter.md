# hoc_cus_integrations_L5_engines_runtime_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/runtime_adapter.py` |
| Layer | L3 — Boundary Adapter (Translation) |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Translate API requests into runtime domain commands

## Intent

**Role:** Translate API requests into runtime domain commands
**Reference:** PIN-258 Phase F-3 Runtime Cluster
**Callers:** runtime.py (L2)

## Purpose

Runtime Boundary Adapter (L3)

---

## Functions

### `get_runtime_adapter() -> RuntimeAdapter`
- **Async:** No
- **Docstring:** Factory function to get RuntimeAdapter instance.  This is the entry point for L2 to get the adapter.
- **Calls:** RuntimeAdapter

## Classes

### `RuntimeAdapter`
- **Docstring:** L3 Boundary Adapter for runtime operations.
- **Methods:** __init__, query, get_supported_queries, describe_skill, list_skills, get_skill_descriptors, get_resource_contract, get_capabilities

## Attributes

- `logger` (line 55)
- `__all__` (line 212)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.commands.runtime_command` |

## Callers

runtime.py (L2)

## Export Contract

```yaml
exports:
  functions:
    - name: get_runtime_adapter
      signature: "get_runtime_adapter() -> RuntimeAdapter"
  classes:
    - name: RuntimeAdapter
      methods: [query, get_supported_queries, describe_skill, list_skills, get_skill_descriptors, get_resource_contract, get_capabilities]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
