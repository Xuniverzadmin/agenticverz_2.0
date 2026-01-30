# hoc_cus_policies_L5_engines_policy_proposal_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/policy_proposal_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy proposal lifecycle engine - manages proposal state machine

## Intent

**Role:** Policy proposal lifecycle engine - manages proposal state machine
**Reference:** PIN-470, Phase 3B P3 Design-First
**Callers:** L2 policies API

## Purpose

Policy Proposal Engine (L5)

---

## Functions

### `generate_default_rule(policy_type: str, feedback_type: str) -> dict`
- **Async:** No
- **Docstring:** Generate a default rule template based on policy type.  PB-S4: These are SUGGESTIONS only. Human must review.

### `get_policy_proposal_engine(session: 'AsyncSession') -> PolicyProposalEngine`
- **Async:** No
- **Docstring:** Get a PolicyProposalEngine instance with drivers.
- **Calls:** PolicyProposalEngine, get_policy_proposal_read_driver, get_policy_proposal_write_driver

### `async check_proposal_eligibility(session: 'AsyncSession', tenant_id: Optional[UUID], feedback_type: Optional[str], threshold: int) -> list[dict]`
- **Async:** Yes
- **Docstring:** Backward-compatible wrapper for eligibility checking.
- **Calls:** check_proposal_eligibility, get_policy_proposal_engine

### `async create_policy_proposal(session: 'AsyncSession', proposal: PolicyProposalCreate) -> str`
- **Async:** Yes
- **Docstring:** Backward-compatible wrapper for proposal creation.
- **Calls:** create_proposal, get_policy_proposal_engine

### `async review_policy_proposal(session: 'AsyncSession', proposal_id: UUID, review: PolicyApprovalRequest) -> dict`
- **Async:** Yes
- **Docstring:** Backward-compatible wrapper for proposal review.
- **Calls:** get_policy_proposal_engine, review_proposal

### `async delete_policy_rule(session: 'AsyncSession', rule_id: str, tenant_id: str, deleted_by: str) -> bool`
- **Async:** Yes
- **Docstring:** Backward-compatible wrapper for rule deletion.
- **Calls:** delete_policy_rule, get_policy_proposal_engine

### `async get_proposal_summary(session: 'AsyncSession', tenant_id: Optional[UUID], status: Optional[str], limit: int) -> dict`
- **Async:** Yes
- **Docstring:** Backward-compatible wrapper for proposal summary.
- **Calls:** get_policy_proposal_engine, get_proposal_summary

## Classes

### `PolicyActivationBlockedError(Exception)`
- **Docstring:** GOV-POL-001: Raised when policy activation is blocked due to BLOCKING conflicts.
- **Methods:** __init__

### `PolicyDeletionBlockedError(Exception)`
- **Docstring:** GOV-POL-002: Raised when policy deletion is blocked due to dependents.
- **Methods:** __init__

### `PolicyProposalEngine`
- **Docstring:** L5 Domain Engine for policy proposal lifecycle management.
- **Methods:** __init__, check_proposal_eligibility, create_proposal, review_proposal, _create_policy_rule_from_proposal, delete_policy_rule, get_proposal_summary

## Attributes

- `logger` (line 61)
- `FEEDBACK_THRESHOLD_FOR_PROPOSAL` (line 96)
- `PROPOSAL_TYPES` (line 97)
- `__all__` (line 695)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.policies.L5_engines.policy_graph_engine` |
| L6 Driver | `app.hoc.cus.logs.L6_drivers.audit_ledger_service_async`, `app.hoc.cus.policies.L6_drivers.policy_proposal_read_driver`, `app.hoc.cus.policies.L6_drivers.policy_proposal_write_driver` |
| L7 Model | `app.models.audit_ledger`, `app.models.policy` |
| Cross-Domain | `app.hoc.cus.logs.L6_drivers.audit_ledger_service_async` |
| External | `app.hoc.hoc_spine.services.time`, `sqlalchemy.ext.asyncio` |

## Callers

L2 policies API

## Export Contract

```yaml
exports:
  functions:
    - name: generate_default_rule
      signature: "generate_default_rule(policy_type: str, feedback_type: str) -> dict"
    - name: get_policy_proposal_engine
      signature: "get_policy_proposal_engine(session: 'AsyncSession') -> PolicyProposalEngine"
    - name: check_proposal_eligibility
      signature: "async check_proposal_eligibility(session: 'AsyncSession', tenant_id: Optional[UUID], feedback_type: Optional[str], threshold: int) -> list[dict]"
    - name: create_policy_proposal
      signature: "async create_policy_proposal(session: 'AsyncSession', proposal: PolicyProposalCreate) -> str"
    - name: review_policy_proposal
      signature: "async review_policy_proposal(session: 'AsyncSession', proposal_id: UUID, review: PolicyApprovalRequest) -> dict"
    - name: delete_policy_rule
      signature: "async delete_policy_rule(session: 'AsyncSession', rule_id: str, tenant_id: str, deleted_by: str) -> bool"
    - name: get_proposal_summary
      signature: "async get_proposal_summary(session: 'AsyncSession', tenant_id: Optional[UUID], status: Optional[str], limit: int) -> dict"
  classes:
    - name: PolicyActivationBlockedError
      methods: []
    - name: PolicyDeletionBlockedError
      methods: []
    - name: PolicyProposalEngine
      methods: [check_proposal_eligibility, create_proposal, review_proposal, delete_policy_rule, get_proposal_summary]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
