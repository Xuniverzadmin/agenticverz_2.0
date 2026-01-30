# hoc_models_policy_precedence

| Field | Value |
|-------|-------|
| Path | `backend/app/models/policy_precedence.py` |
| Layer | L4 — Domain Engine |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Define policy precedence and conflict resolution strategies

## Intent

**Role:** Define policy precedence and conflict resolution strategies
**Reference:** POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-003
**Callers:** policy/arbitrator.py, api/policy_precedence.py

## Purpose

Policy Precedence Model

---

## Classes

### `ConflictStrategy(str, Enum)`
- **Docstring:** Strategy for resolving policy conflicts.

### `BindingMoment(str, Enum)`
- **Docstring:** When the policy becomes authoritative.

### `PolicyPrecedence(SQLModel)`
- **Docstring:** Policy precedence configuration for conflict resolution.
- **Methods:** to_snapshot
- **Class Variables:** id: Optional[int], policy_id: str, tenant_id: str, precedence: int, conflict_strategy: str, bind_at: str, failure_mode: str, created_at: datetime, updated_at: datetime

### `ArbitrationResult(BaseModel)`
- **Docstring:** Result of policy arbitration.
- **Class Variables:** policy_ids: list[str], precedence_order: list[int], effective_token_limit: Optional[int], effective_cost_limit_cents: Optional[int], effective_burn_rate_limit: Optional[float], effective_breach_action: str, conflicts_resolved: int, resolution_strategy: str, arbitration_timestamp: datetime, snapshot_hash: str

### `PolicyPrecedenceCreate(BaseModel)`
- **Docstring:** Request model for creating policy precedence.
- **Class Variables:** policy_id: str, precedence: int, conflict_strategy: ConflictStrategy, bind_at: BindingMoment, failure_mode: str

### `PolicyPrecedenceUpdate(BaseModel)`
- **Docstring:** Request model for updating policy precedence.
- **Class Variables:** precedence: Optional[int], conflict_strategy: Optional[ConflictStrategy], bind_at: Optional[BindingMoment], failure_mode: Optional[str]

### `PolicyPrecedenceResponse(BaseModel)`
- **Docstring:** Response model for policy precedence.
- **Class Variables:** policy_id: str, tenant_id: str, precedence: int, conflict_strategy: ConflictStrategy, bind_at: BindingMoment, failure_mode: str, created_at: datetime, updated_at: datetime

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic`, `sqlmodel` |

## Callers

policy/arbitrator.py, api/policy_precedence.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: ConflictStrategy
      methods: []
    - name: BindingMoment
      methods: []
    - name: PolicyPrecedence
      methods: [to_snapshot]
    - name: ArbitrationResult
      methods: []
    - name: PolicyPrecedenceCreate
      methods: []
    - name: PolicyPrecedenceUpdate
      methods: []
    - name: PolicyPrecedenceResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
