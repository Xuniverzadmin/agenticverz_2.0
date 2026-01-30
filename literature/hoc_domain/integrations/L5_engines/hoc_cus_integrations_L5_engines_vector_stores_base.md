# hoc_cus_integrations_L5_engines_vector_stores_base

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/vector_stores_base.py` |
| Layer | L3 — Boundary Adapters |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Base class for vector store adapters

## Intent

**Role:** Base class for vector store adapters
**Reference:** GAP-144, GAP-145, GAP-146
**Callers:** Vector store adapter implementations

## Purpose

Vector Store Base Adapter

---

## Classes

### `VectorRecord`
- **Docstring:** A single vector record.
- **Methods:** to_dict
- **Class Variables:** id: str, vector: List[float], metadata: Dict[str, Any], text: Optional[str], namespace: Optional[str]

### `QueryResult`
- **Docstring:** Result of a vector similarity query.
- **Methods:** to_dict
- **Class Variables:** id: str, score: float, vector: Optional[List[float]], metadata: Dict[str, Any], text: Optional[str]

### `UpsertResult`
- **Docstring:** Result of an upsert operation.
- **Methods:** success
- **Class Variables:** upserted_count: int, upserted_ids: List[str], errors: List[Dict[str, Any]]

### `DeleteResult`
- **Docstring:** Result of a delete operation.
- **Methods:** success
- **Class Variables:** deleted_count: int, deleted_ids: List[str]

### `IndexStats`
- **Docstring:** Statistics about a vector index.
- **Methods:** to_dict
- **Class Variables:** total_vectors: int, dimension: int, index_fullness: Optional[float], namespaces: Optional[Dict[str, int]], metadata: Dict[str, Any]

### `VectorStoreAdapter(ABC)`
- **Docstring:** Abstract base class for vector store adapters.
- **Methods:** connect, disconnect, upsert, query, delete, get_stats, health_check, create_namespace, delete_namespace, list_namespaces

## Attributes

- `logger` (line 25)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

Vector store adapter implementations

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: VectorRecord
      methods: [to_dict]
    - name: QueryResult
      methods: [to_dict]
    - name: UpsertResult
      methods: [success]
    - name: DeleteResult
      methods: [success]
    - name: IndexStats
      methods: [to_dict]
    - name: VectorStoreAdapter
      methods: [connect, disconnect, upsert, query, delete, get_stats, health_check, create_namespace, delete_namespace, list_namespaces]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
