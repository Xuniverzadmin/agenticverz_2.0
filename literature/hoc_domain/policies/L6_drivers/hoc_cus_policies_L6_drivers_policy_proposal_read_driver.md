# hoc_cus_policies_L6_drivers_policy_proposal_read_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/policy_proposal_read_driver.py` |
| Layer | L6 — Data Access Driver |
| Domain | policies |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Read operations for policy proposal engine

## Intent

**Role:** Read operations for policy proposal engine
**Reference:** PIN-470, Phase 3B P3 Design-First
**Callers:** L5 policy_proposal_engine

## Purpose

Policy Proposal Read Driver (L6)

---

## Functions

### `get_policy_proposal_read_driver(session: AsyncSession) -> PolicyProposalReadDriver`
- **Async:** No
- **Docstring:** Factory function for PolicyProposalReadDriver.
- **Calls:** PolicyProposalReadDriver

## Classes

### `PolicyProposalReadDriver`
- **Docstring:** Read operations for policy proposals.
- **Methods:** __init__, fetch_unacknowledged_feedback, fetch_proposal_by_id, fetch_proposal_status, count_versions_for_proposal, fetch_proposals, check_rule_exists, fetch_rule_by_id

## Attributes

- `__all__` (line 198)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.feedback`, `app.models.policy` |
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

L5 policy_proposal_engine

## Export Contract

```yaml
exports:
  functions:
    - name: get_policy_proposal_read_driver
      signature: "get_policy_proposal_read_driver(session: AsyncSession) -> PolicyProposalReadDriver"
  classes:
    - name: PolicyProposalReadDriver
      methods: [fetch_unacknowledged_feedback, fetch_proposal_by_id, fetch_proposal_status, count_versions_for_proposal, fetch_proposals, check_rule_exists, fetch_rule_by_id]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
