# transaction_coordinator.py

**Path:** `backend/app/hoc/hoc_spine/drivers/transaction_coordinator.py`  
**Layer:** L4 — HOC Spine (Driver)  
**Component:** Drivers

---

## Placement Card

```
File:            transaction_coordinator.py
Lives in:        drivers/
Role:            Drivers
Inbound:         ROK (L5), RunRunner (L5)
Outbound:        app.hoc.hoc_spine.schemas.rac_models, app.hoc.hoc_spine.services.audit_store, app.hoc.hoc_spine.orchestrator.run_governance_facade
Transaction:     OWNS COMMIT
Cross-domain:    none
Purpose:         Transaction Coordinator for Cross-Domain Writes
Violations:      none
```

## Purpose

Transaction Coordinator for Cross-Domain Writes

This module provides atomic transaction coordination for run completion,
ensuring that ALL domain updates succeed or NONE persist.

Problem Addressed (FIX-001):
- Incident/policy/trace writes are independent
- Partial failure causes inconsistent state
- Events published before all operations complete

Solution:
- Wrap all domain operations in single transaction boundary
- Track which operations succeeded for rollback
- Publish events ONLY after successful commit

Architecture:

    ┌──────────────────────────────────────────────────────────────────┐
    │              Transaction Coordinator (L4)                        │
    ├──────────────────────────────────────────────────────────────────┤
    │  TRANSACTION FLOW:                                               │
    │  1. Begin transaction                                            │
    │  2. Create incident (via IncidentFacade)                         │
    │  3. Create policy evaluation (via GovernanceFacade)              │
    │  4. Complete trace (via TraceFacade)                             │
    │  5. Commit transaction                                           │
    │  6. Publish events (post-commit only)                            │
    │                                                                  │
    │  ON FAILURE:                                                     │
    │  • Rollback transaction                                          │
    │  • No events published                                           │
    │  • Raise TransactionFailed with context                          │
    │                                                                  │
    │  INVARIANTS:                                                     │
    │  • Events ONLY after successful commit                           │
    │  • Partial state is never visible                                │
    │  • All domain operations use facades (layer compliance)          │
    └──────────────────────────────────────────────────────────────────┘

Usage:

    from app.hoc.hoc_spine.drivers.transaction_coordinator import (
        RunCompletionTransaction,
        get_transaction_coordinator,
    )

    coordinator = get_transaction_coordinator()
    result = coordinator.execute(
        run_id=run_id,
        tenant_id=tenant_id,
        run_status="succeeded",
        agent_id=agent_id,
    )

## Import Analysis

**Spine-internal:**
- `app.hoc.hoc_spine.schemas.rac_models`
- `app.hoc.hoc_spine.services.audit_store`
- `app.hoc.hoc_spine.orchestrator.run_governance_facade`

**External:**
- `sqlmodel`
- `app.db`
- `app.events`

## Transaction Boundary

- **Commits:** YES
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_transaction_coordinator() -> RunCompletionTransaction`

Get the singleton transaction coordinator instance.

Returns:
    RunCompletionTransaction instance

### `create_transaction_coordinator(publisher) -> RunCompletionTransaction`

Create a new transaction coordinator instance.

Use this for testing or when you need a fresh instance.

Args:
    publisher: Optional event publisher

Returns:
    RunCompletionTransaction instance

## Classes

### `TransactionPhase(str, Enum)`

Phases of transaction execution.

### `TransactionFailed(Exception)`

Raised when cross-domain transaction fails.

#### Methods

- `__init__(message: str, phase: TransactionPhase, partial_results: Optional[Dict[str, Any]], cause: Optional[Exception])` — _No docstring._

### `DomainResult`

Result from a single domain operation.

#### Methods

- `to_dict() -> Dict[str, Any]` — Serialize for logging/events.

### `TransactionResult`

Result of a successful cross-domain transaction.

#### Methods

- `is_complete() -> bool` — Check if transaction completed successfully.
- `all_domains_succeeded() -> bool` — Check if all domain operations succeeded.
- `to_dict() -> Dict[str, Any]` — Serialize for logging/events.

### `RollbackAction`

Describes a rollback action for a domain operation.

### `RunCompletionTransaction`

Atomic cross-domain transaction for run completion.

Ensures either ALL domain updates succeed or NONE persist.
Events published ONLY after commit succeeds.

Layer: L4 (Domain Logic)
Callers: ROK (L5), RunRunner (L5)

#### Methods

- `__init__(publisher)` — Initialize transaction coordinator.
- `execute(run_id: str, tenant_id: str, run_status: str, agent_id: Optional[str], error_code: Optional[str], error_message: Optional[str], trace_id: Optional[str], is_synthetic: bool, synthetic_scenario_id: Optional[str], skip_events: bool) -> TransactionResult` — Execute cross-domain updates atomically.
- `_create_incident(session: Session, run_id: str, tenant_id: str, run_status: str, agent_id: Optional[str], error_code: Optional[str], error_message: Optional[str], is_synthetic: bool, synthetic_scenario_id: Optional[str]) -> None` — Create incident within transaction.
- `_create_policy_evaluation(session: Session, run_id: str, tenant_id: str, run_status: str, is_synthetic: bool, synthetic_scenario_id: Optional[str]) -> None` — Create policy evaluation within transaction.
- `_complete_trace(session: Session, run_id: str, trace_id: str, run_status: str) -> None` — Complete trace within transaction.
- `_publish_events(run_id: str, run_status: str) -> None` — Publish events ONLY after successful commit.
- `_execute_rollback() -> None` — Execute rollback actions in reverse order.
- `_emit_rollback_ack(run_id: str, domain: str, action_name: str, result_id: Optional[str], rollback_error: Optional[str]) -> None` — Emit a DomainAck marking an action as rolled back.
- `_rollback_incident(incident_id: str) -> None` — Rollback incident creation (soft-delete or mark as rolled_back).
- `_rollback_policy(policy_id: str) -> None` — Rollback policy evaluation (soft-delete or mark as rolled_back).

## Domain Usage

**Callers:** ROK (L5), RunRunner (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_transaction_coordinator
      signature: "get_transaction_coordinator() -> RunCompletionTransaction"
      consumers: ["orchestrator"]
    - name: create_transaction_coordinator
      signature: "create_transaction_coordinator(publisher) -> RunCompletionTransaction"
      consumers: ["orchestrator"]
  classes:
    - name: TransactionPhase
      methods: []
      consumers: ["orchestrator"]
    - name: TransactionFailed
      methods:
      consumers: ["orchestrator"]
    - name: DomainResult
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: TransactionResult
      methods:
        - is_complete
        - all_domains_succeeded
        - to_dict
      consumers: ["orchestrator"]
    - name: RollbackAction
      methods: []
      consumers: ["orchestrator"]
    - name: RunCompletionTransaction
      methods:
        - execute
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.services.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: ['app.hoc.hoc_spine.schemas.rac_models', 'app.hoc.hoc_spine.services.audit_store', 'app.hoc.hoc_spine.orchestrator.run_governance_facade']
    l7_model: []
    external: ['sqlmodel', 'app.db', 'app.events']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

