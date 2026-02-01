# rac_models.py

**Path:** `backend/app/hoc/cus/hoc_spine/schemas/rac_models.py`  
**Layer:** L4 — HOC Spine (Schema)  
**Component:** Schemas

---

## Placement Card

```
File:            rac_models.py
Lives in:        schemas/
Role:            Schemas
Inbound:         L4 drivers (transaction_coordinator), L5 engines (audit_store, reconciler)
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Runtime Audit Contract (RAC) Models
Violations:      none
```

## Purpose

Runtime Audit Contract (RAC) Models

These models define the data structures for the audit system:

- AuditExpectation: Declares what action MUST happen for a run
- DomainAck: Reports that an action has completed
- ReconciliationResult: Result of comparing expectations vs acks

Design Principles:
1. Immutable after creation (expectations are contracts)
2. UUID-based for correlation across domains
3. Serializable for Redis storage
4. Type-safe with enums for domains and actions

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `create_run_expectations(run_id: UUID, run_timeout_ms: int, grace_period_ms: int) -> List[AuditExpectation]`

Create the standard set of expectations for a run.

This is called by ROK at T0 (run creation) to declare
what MUST happen during run execution.

Args:
    run_id: The run ID
    run_timeout_ms: Expected run duration
    grace_period_ms: Grace period after run timeout

Returns:
    List of AuditExpectation objects

### `create_domain_ack(run_id: UUID, domain: AuditDomain, action: AuditAction, result_id: Optional[str], error: Optional[str], **metadata: Any) -> DomainAck`

Create a domain acknowledgment.

This is called by facades after completing domain operations.

Args:
    run_id: The run ID
    domain: Which domain performed the action
    action: What action was performed
    result_id: ID of created entity (e.g., incident_id)
    error: Error message if action failed
    **metadata: Additional context

Returns:
    DomainAck object

## Classes

### `AuditStatus(str, Enum)`

Status of an audit expectation.

### `AuditDomain(str, Enum)`

Domains that participate in the audit contract.

### `AuditAction(str, Enum)`

Actions that can be expected/acked.

### `AuditExpectation`

An expectation that an action MUST happen for a run.

Created at run start (T0) by ROK, one per expected domain action.
The finalize_run expectation is the liveness guarantee.

Attributes:
    id: Unique expectation ID
    run_id: The run this expectation belongs to
    domain: Which domain should perform the action
    action: What action is expected
    status: Current status (PENDING -> ACKED | MISSING | FAILED)
    deadline_ms: Time allowed for ack (from creation)
    created_at: When this expectation was created
    acked_at: When the ack was received (if any)
    metadata: Additional context (e.g., expected result type)

#### Methods

- `to_dict() -> Dict[str, Any]` — Serialize for storage.
- `from_dict(data: Dict[str, Any]) -> 'AuditExpectation'` — Deserialize from storage.
- `key() -> Tuple[str, str]` — Return (domain, action) tuple for set operations.

### `AckStatus(str, Enum)`

Status of a domain acknowledgment.

### `DomainAck`

Acknowledgment that a domain action has completed.

Emitted by facades after successful domain operations.
Matched against expectations during reconciliation.

Attributes:
    id: Unique ack ID
    run_id: The run this ack belongs to
    domain: Which domain performed the action
    action: What action was performed
    status: Status of the ack (SUCCESS, FAILED, ROLLED_BACK)
    result_id: ID of the created entity (e.g., incident_id)
    error: Error message if action failed
    rolled_back: True if this action was rolled back (audit trail)
    rollback_reason: Why the action was rolled back
    created_at: When this ack was created
    metadata: Additional context (e.g., execution time)

#### Methods

- `is_success() -> bool` — Check if this ack represents a successful action.
- `is_rolled_back() -> bool` — Check if this action was rolled back.
- `to_dict() -> Dict[str, Any]` — Serialize for storage.
- `from_dict(data: Dict[str, Any]) -> 'DomainAck'` — Deserialize from storage.
- `key() -> Tuple[str, str]` — Return (domain, action) tuple for set operations.

### `ReconciliationResult`

Result of reconciling expectations against acknowledgments.

Produced by AuditReconciler after comparing what was expected
vs what actually happened.

Attributes:
    run_id: The run that was reconciled
    status: Overall status (COMPLETE, INCOMPLETE, STALE)
    missing_actions: Actions expected but not acked
    drift_actions: Actions acked but not expected
    failed_actions: Actions acked with errors
    stale_run: True if finalize_run was never acked
    reconciled_at: When reconciliation was performed
    expectations_count: Total expectations
    acks_count: Total acks received

#### Methods

- `is_clean() -> bool` — Check if reconciliation found no issues.
- `has_missing() -> bool` — Check if there are missing actions.
- `has_drift() -> bool` — Check if there are unexpected actions.
- `to_dict() -> Dict[str, Any]` — Serialize for logging/storage.

## Domain Usage

**Callers:** L4 drivers (transaction_coordinator), L5 engines (audit_store, reconciler)

## Export Contract

```yaml
exports:
  functions:
    - name: create_run_expectations
      signature: "create_run_expectations(run_id: UUID, run_timeout_ms: int, grace_period_ms: int) -> List[AuditExpectation]"
      consumers: ["orchestrator"]
    - name: create_domain_ack
      signature: "create_domain_ack(run_id: UUID, domain: AuditDomain, action: AuditAction, result_id: Optional[str], error: Optional[str], **metadata: Any) -> DomainAck"
      consumers: ["orchestrator"]
  classes:
    - name: AuditStatus
      methods: []
      consumers: ["orchestrator"]
    - name: AuditDomain
      methods: []
      consumers: ["orchestrator"]
    - name: AuditAction
      methods: []
      consumers: ["orchestrator"]
    - name: AuditExpectation
      methods:
        - to_dict
        - from_dict
        - key
      consumers: ["orchestrator"]
    - name: AckStatus
      methods: []
      consumers: ["orchestrator"]
    - name: DomainAck
      methods:
        - is_success
        - is_rolled_back
        - to_dict
        - from_dict
        - key
      consumers: ["orchestrator"]
    - name: ReconciliationResult
      methods:
        - is_clean
        - has_missing
        - has_drift
        - to_dict
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: []
    l7_model: []
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

