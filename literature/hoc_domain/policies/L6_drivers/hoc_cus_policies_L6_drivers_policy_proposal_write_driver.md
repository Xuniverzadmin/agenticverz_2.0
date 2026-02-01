# hoc_cus_policies_L6_drivers_policy_proposal_write_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/policy_proposal_write_driver.py` |
| Layer | L6 — Data Access Driver |
| Domain | policies |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Write operations for policy proposal engine

## Intent

**Role:** Write operations for policy proposal engine
**Reference:** PIN-470, Phase 3B P3 Design-First
**Callers:** L5 policy_proposal_engine

## Purpose

Policy Proposal Write Driver (L6)

---

## Functions

### `get_policy_proposal_write_driver(session: AsyncSession) -> PolicyProposalWriteDriver`
- **Async:** No
- **Docstring:** Factory function for PolicyProposalWriteDriver.
- **Calls:** PolicyProposalWriteDriver

## Classes

### `PolicyProposalWriteDriver`
- **Docstring:** Write operations for policy proposals.
- **Methods:** __init__, create_proposal, update_proposal_status, create_version, create_policy_rule, delete_policy_rule

## Attributes

- `__all__` (line 226)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.policy` |
| External | `app.hoc.cus.hoc_spine.services.time`, `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

L5 policy_proposal_engine

## Export Contract

```yaml
exports:
  functions:
    - name: get_policy_proposal_write_driver
      signature: "get_policy_proposal_write_driver(session: AsyncSession) -> PolicyProposalWriteDriver"
  classes:
    - name: PolicyProposalWriteDriver
      methods: [create_proposal, update_proposal_status, create_version, create_policy_rule, delete_policy_rule]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
