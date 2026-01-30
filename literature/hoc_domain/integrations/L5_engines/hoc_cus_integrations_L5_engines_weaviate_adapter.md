# hoc_cus_integrations_L5_engines_weaviate_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/weaviate_adapter.py` |
| Layer | L3 — Boundary Adapters |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Weaviate vector store adapter

## Intent

**Role:** Weaviate vector store adapter
**Reference:** GAP-145 (Weaviate Vector Store Adapter)
**Callers:** RetrievalMediator, IndexingExecutor

## Purpose

Weaviate Vector Store Adapter (GAP-145)

---

## Classes

### `WeaviateAdapter(VectorStoreAdapter)`
- **Docstring:** Weaviate vector store adapter.
- **Methods:** __init__, connect, _create_collection, disconnect, upsert, query, _build_filter, delete, get_stats, create_namespace, delete_namespace, list_namespaces

## Attributes

- `logger` (line 35)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `base`, `weaviate`, `weaviate.auth` |

## Callers

RetrievalMediator, IndexingExecutor

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: WeaviateAdapter
      methods: [connect, disconnect, upsert, query, delete, get_stats, create_namespace, delete_namespace, list_namespaces]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
