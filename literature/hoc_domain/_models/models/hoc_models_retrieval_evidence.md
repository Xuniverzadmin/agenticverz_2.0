# hoc_models_retrieval_evidence

| Field | Value |
|-------|-------|
| Path | `backend/app/models/retrieval_evidence.py` |
| Layer | L4 — Domain Engines |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Audit log model for mediated data access

## Intent

**Role:** Audit log model for mediated data access
**Reference:** GAP-058
**Callers:** RetrievalMediator (GAP-065), export services

## Purpose

Module: retrieval_evidence
Purpose: Audit log for every mediated data access.

---

## Functions

### `utc_now() -> datetime`
- **Async:** No
- **Docstring:** Return current UTC time with timezone info.
- **Calls:** now

### `generate_uuid() -> str`
- **Async:** No
- **Docstring:** Generate a new UUID string.
- **Calls:** str, uuid4

## Classes

### `RetrievalEvidence(SQLModel)`
- **Docstring:** Audit record for mediated data access.
- **Methods:** is_complete, doc_count
- **Class Variables:** id: str, tenant_id: str, run_id: str, plane_id: str, connector_id: str, action: str, query_hash: str, doc_ids: List[str], token_count: int, policy_snapshot_id: Optional[str], requested_at: datetime, completed_at: Optional[datetime], duration_ms: Optional[int], created_at: datetime

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.dialects.postgresql`, `sqlmodel` |

## Callers

RetrievalMediator (GAP-065), export services

## Export Contract

```yaml
exports:
  functions:
    - name: utc_now
      signature: "utc_now() -> datetime"
    - name: generate_uuid
      signature: "generate_uuid() -> str"
  classes:
    - name: RetrievalEvidence
      methods: [is_complete, doc_count]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
