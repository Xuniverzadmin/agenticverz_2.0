# hoc_cus_integrations_L5_engines_pinecone_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/pinecone_adapter.py` |
| Layer | L3 — Boundary Adapters |
| Domain | integrations |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Pinecone vector store adapter

## Intent

**Role:** Pinecone vector store adapter
**Reference:** GAP-144 (Pinecone Vector Store Adapter)
**Callers:** RetrievalMediator, IndexingExecutor

## Purpose

Pinecone Vector Store Adapter (GAP-144)

---

## Classes

### `PineconeAdapter(VectorStoreAdapter)`
- **Docstring:** Pinecone vector store adapter.
- **Methods:** __init__, connect, disconnect, upsert, query, delete, get_stats, create_namespace, delete_namespace, list_namespaces

## Attributes

- `logger` (line 37)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `base`, `pinecone` |

## Callers

RetrievalMediator, IndexingExecutor

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: PineconeAdapter
      methods: [connect, disconnect, upsert, query, delete, get_stats, create_namespace, delete_namespace, list_namespaces]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
