# hoc_models_policy

| Field | Value |
|-------|-------|
| Path | `backend/app/models/policy.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Policy data models (DB tables)

## Intent

**Role:** Policy data models (DB tables)
**Reference:** Policy System
**Callers:** policy/*

## Purpose

Policy Proposal Models (PB-S4)

---

## Classes

### `PolicyProposal(Base)`
- **Docstring:** Policy proposal record - recommendation without enforcement.

### `PolicyVersion(Base)`
- **Docstring:** Policy version record - append-only history.

### `PolicyProposalCreate(BaseModel)`
- **Docstring:** Input model for creating policy proposals.
- **Class Variables:** tenant_id: str, proposal_name: str, proposal_type: str, rationale: str, proposed_rule: dict, triggering_feedback_ids: list[str]

### `PolicyProposalResponse(BaseModel)`
- **Docstring:** Output model for policy proposals.
- **Class Variables:** id: UUID, tenant_id: str, proposal_name: str, proposal_type: str, rationale: str, proposed_rule: dict, triggering_feedback_ids: list, status: str, created_at: datetime, reviewed_at: Optional[datetime], reviewed_by: Optional[str], effective_from: Optional[datetime]

### `PolicyApprovalRequest(BaseModel)`
- **Docstring:** Input model for approving/rejecting a policy proposal.
- **Class Variables:** action: str, reviewed_by: str, review_notes: Optional[str], effective_from: Optional[datetime]

### `PolicyVersionResponse(BaseModel)`
- **Docstring:** Output model for policy versions.
- **Class Variables:** id: UUID, proposal_id: UUID, version: int, rule_snapshot: dict, is_current: bool, created_at: datetime, created_by: Optional[str], change_reason: Optional[str]

## Attributes

- `Base` (line 37)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic`, `sqlalchemy`, `sqlalchemy.dialects.postgresql`, `sqlalchemy.orm`, `sqlalchemy.sql` |

## Callers

policy/*

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: PolicyProposal
      methods: []
    - name: PolicyVersion
      methods: []
    - name: PolicyProposalCreate
      methods: []
    - name: PolicyProposalResponse
      methods: []
    - name: PolicyApprovalRequest
      methods: []
    - name: PolicyVersionResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
