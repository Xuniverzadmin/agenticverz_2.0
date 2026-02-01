# contract_engine.py

**Path:** `backend/app/hoc/cus/hoc_spine/authority/contracts/contract_engine.py`  
**Layer:** L4 — HOC Spine (Authority)  
**Component:** Authority

---

## Placement Card

```
File:            contract_engine.py
Lives in:        authority/
Role:            Authority
Inbound:         L3 (adapters), L2 (governance APIs)
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Part-2 Contract Service (L4)
Violations:      none
```

## Purpose

Part-2 Contract Service (L4)

Manages the System Contract state machine - the first stateful component
in the Part-2 governance workflow.

Responsibilities:
1. Create contracts from validated + eligible proposals
2. Enforce state machine transitions
3. Record transition history for audit
4. Enforce terminal state immutability

Invariants (from SYSTEM_CONTRACT_OBJECT.md):
- CONTRACT-001: Status transitions must follow state machine
- CONTRACT-002: APPROVED requires approved_by
- CONTRACT-003: ACTIVE requires job exists
- CONTRACT-004: COMPLETED requires audit_verdict = PASS
- CONTRACT-005: Terminal states are immutable
- CONTRACT-006: proposed_changes must validate schema
- CONTRACT-007: confidence_score range [0,1]

MAY_NOT ENFORCEMENT (PIN-291):
- MAY_NOT verdicts are mechanically un-overridable
- No constructor, method, or bypass can create contracts from MAY_NOT
- This is not a business rule; it is a system invariant

Reference: PIN-291, SYSTEM_CONTRACT_OBJECT.md, part2-design-v1

## Import Analysis

**L7 Models:**
- `app.models.contract`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `ContractState`

In-memory representation of contract state.

Used for state machine operations before persistence.

### `ContractStateMachine`

State machine for System Contract lifecycle.

Enforces:
- CONTRACT-001: Valid transitions only
- CONTRACT-002: APPROVED requires approved_by
- CONTRACT-003: ACTIVE requires job_id
- CONTRACT-004: COMPLETED requires audit_verdict = PASS
- CONTRACT-005: Terminal states are immutable

#### Methods

- `can_transition(from_status: ContractStatus, to_status: ContractStatus) -> bool` — Check if a transition is valid.
- `validate_transition(state: ContractState, to_status: ContractStatus, context: dict[str, Any]) -> None` — Validate a state transition, raising errors if invalid.
- `transition(state: ContractState, to_status: ContractStatus, reason: str, transitioned_by: str, context: Optional[dict[str, Any]]) -> ContractState` — Execute a state transition, returning new state.

### `ContractService`

Part-2 Contract Service (L4)

Manages System Contract lifecycle - the first stateful component
of the Part-2 governance workflow.

Key Properties:
- Consumes validator + eligibility outputs
- Enforces MAY_NOT mechanically (un-overridable)
- Implements state machine with invariants
- No execution logic (that's for Job Executor)

Reference: SYSTEM_CONTRACT_OBJECT.md, PIN-291

#### Methods

- `__init__(service_version: str)` — _No docstring._
- `version() -> str` — Return service version.
- `create_contract(issue_id: UUID, source: ContractSource, title: str, description: Optional[str], proposed_changes: dict[str, Any], affected_capabilities: list[str], risk_level: RiskLevel, validator_verdict: ValidatorVerdict, eligibility_verdict: EligibilityVerdict, created_by: str, expires_in_hours: int) -> ContractState` — Create a new System Contract from validated + eligible proposal.
- `approve(state: ContractState, approval: ContractApproval) -> ContractState` — Approve a contract (Founder Review Gate).
- `reject(state: ContractState, rejected_by: str, reason: str) -> ContractState` — Reject a contract.
- `activate(state: ContractState, job_id: UUID, activated_by: str) -> ContractState` — Activate a contract (start execution).
- `complete(state: ContractState, audit_reason: str, completed_by: str) -> ContractState` — Complete a contract (job succeeded + audit passed).
- `fail(state: ContractState, failure_reason: str, audit_verdict: AuditVerdict, failed_by: str) -> ContractState` — Fail a contract (job failed or audit failed).
- `expire(state: ContractState, expired_by: str) -> ContractState` — Expire a contract (TTL exceeded).
- `is_terminal(state: ContractState) -> bool` — Check if contract is in terminal state.
- `is_approved(state: ContractState) -> bool` — Check if contract is approved (including later states).
- `can_approve(state: ContractState) -> bool` — Check if contract can be approved.
- `get_valid_transitions(state: ContractState) -> frozenset[ContractStatus]` — Get valid transitions from current state.

## Domain Usage

**Callers:** L3 (adapters), L2 (governance APIs)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: ContractState
      methods: []
      consumers: ["orchestrator"]
    - name: ContractStateMachine
      methods:
        - can_transition
        - validate_transition
        - transition
      consumers: ["orchestrator"]
    - name: ContractService
      methods:
        - version
        - create_contract
        - approve
        - reject
        - activate
        - complete
        - fail
        - expire
        - is_terminal
        - is_approved
        - can_approve
        - get_valid_transitions
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: ['app.models.contract']
    external: []
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

