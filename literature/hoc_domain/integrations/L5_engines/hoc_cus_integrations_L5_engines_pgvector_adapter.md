# hoc_cus_integrations_L5_engines_pgvector_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/pgvector_adapter.py` |
| Layer | L3 — Boundary Adapters |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

PGVector production adapter

## Intent

**Role:** PGVector production adapter
**Reference:** GAP-146 (PGVector Production Adapter)
**Callers:** RetrievalMediator, IndexingExecutor

## Purpose

PGVector Production Adapter (GAP-146)

---

## Classes

### `PGVectorAdapter(VectorStoreAdapter)`
- **Docstring:** PGVector production adapter.
- **Methods:** __init__, connect, disconnect, upsert, query, delete, get_stats, create_namespace, delete_namespace, list_namespaces

## Attributes

- `logger` (line 35)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `asyncpg`, `base` |

## Callers

RetrievalMediator, IndexingExecutor

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: PGVectorAdapter
      methods: [connect, disconnect, upsert, query, delete, get_stats, create_namespace, delete_namespace, list_namespaces]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
