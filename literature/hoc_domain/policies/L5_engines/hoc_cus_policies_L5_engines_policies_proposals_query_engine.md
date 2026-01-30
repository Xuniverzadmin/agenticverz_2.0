# hoc_cus_policies_L5_engines_policies_proposals_query_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/policies_proposals_query_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Proposals query engine - read-only operations for policy proposals list

## Intent

**Role:** Proposals query engine - read-only operations for policy proposals list
**Reference:** PIN-470, Phase 3B P3 Design-First
**Callers:** L2 policies API

## Purpose

Proposals Query Engine (L5)

---

## Functions

### `get_proposals_query_engine(session: 'AsyncSession') -> ProposalsQueryEngine`
- **Async:** No
- **Docstring:** Get a ProposalsQueryEngine instance.
- **Calls:** ProposalsQueryEngine, get_proposals_read_driver

## Classes

### `PolicyRequestResult`
- **Docstring:** Pending policy request summary (ACT-O3).
- **Class Variables:** id: str, proposal_name: str, proposal_type: str, rationale: str, proposed_rule: dict[str, Any], status: str, created_at: datetime, triggering_feedback_count: int, days_pending: int

### `PolicyRequestsListResult`
- **Docstring:** Policy requests list response.
- **Class Variables:** items: list[PolicyRequestResult], total: int, pending_count: int, filters_applied: dict[str, Any]

### `PolicyRequestDetailResult`
- **Docstring:** Policy request detail response.
- **Class Variables:** id: str, proposal_name: str, proposal_type: str, rationale: str, proposed_rule: dict[str, Any], status: str, created_at: datetime, reviewed_at: Optional[datetime], reviewed_by: Optional[str], review_notes: Optional[str], effective_from: Optional[datetime], triggering_feedback_count: int, triggering_feedback_ids: list[str], days_pending: int

### `ProposalsQueryEngine`
- **Docstring:** L5 Query Engine for policy proposals.
- **Methods:** __init__, list_policy_requests, get_policy_request_detail, count_drafts

## Attributes

- `__all__` (line 216)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.policies.L6_drivers.proposals_read_driver` |
| External | `sqlalchemy.ext.asyncio` |

## Callers

L2 policies API

## Export Contract

```yaml
exports:
  functions:
    - name: get_proposals_query_engine
      signature: "get_proposals_query_engine(session: 'AsyncSession') -> ProposalsQueryEngine"
  classes:
    - name: PolicyRequestResult
      methods: []
    - name: PolicyRequestsListResult
      methods: []
    - name: PolicyRequestDetailResult
      methods: []
    - name: ProposalsQueryEngine
      methods: [list_policy_requests, get_policy_request_detail, count_drafts]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
