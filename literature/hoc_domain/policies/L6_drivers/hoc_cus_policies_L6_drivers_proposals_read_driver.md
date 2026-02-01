# hoc_cus_policies_L6_drivers_proposals_read_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/proposals_read_driver.py` |
| Layer | L6 — Data Access Driver |
| Domain | policies |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Read operations for policy proposals (list view)

## Intent

**Role:** Read operations for policy proposals (list view)
**Reference:** PIN-470, Phase 3B P3 Design-First
**Callers:** L5 policies_proposals_query_engine

## Purpose

Proposals Read Driver (L6)

---

## Functions

### `get_proposals_read_driver(session: AsyncSession) -> ProposalsReadDriver`
- **Async:** No
- **Docstring:** Factory function for ProposalsReadDriver.
- **Calls:** ProposalsReadDriver

## Classes

### `ProposalsReadDriver`
- **Docstring:** Read operations for policy proposals (list view).
- **Methods:** __init__, fetch_proposals, fetch_proposal_by_id, count_draft_proposals

## Attributes

- `__all__` (line 202)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.policy` |
| External | `app.hoc.cus.hoc_spine.services.time`, `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

L5 policies_proposals_query_engine

## Export Contract

```yaml
exports:
  functions:
    - name: get_proposals_read_driver
      signature: "get_proposals_read_driver(session: AsyncSession) -> ProposalsReadDriver"
  classes:
    - name: ProposalsReadDriver
      methods: [fetch_proposals, fetch_proposal_by_id, count_draft_proposals]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
