# hoc_cus_controls_L6_drivers_scoped_execution

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L6_drivers/scoped_execution.py` |
| Layer | L6 — Domain Driver |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Pre-execution gate, scope enforcement

## Intent

**Role:** Pre-execution gate, scope enforcement
**Reference:** PIN-470, PIN-242 (Baseline Freeze)
**Callers:** L2 APIs (recovery actions), L5 workers

## Purpose

M6: Scoped Execution Context Service (P2FC-4)

---

## Functions

### `get_scope_store() -> ScopeStore`
- **Async:** No
- **Docstring:** Get the global scope store.

### `async create_recovery_scope(incident_id: str, action: str, intent: str, max_cost_usd: float, max_attempts: int, ttl_seconds: int, target_agents: Optional[List[str]], created_by: str) -> Dict[str, Any]`
- **Async:** Yes
- **Docstring:** Create a bound execution scope for recovery action.  This is the gate step (Step A2 in test script).
- **Calls:** create_scope, get_scope_store, to_dict

### `async execute_with_scope(scope_id: str, action: str, incident_id: str, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]`
- **Async:** Yes
- **Docstring:** Execute a recovery action within a valid scope.  This enforces all P2FC-4 gates:
- **Calls:** ScopeActionMismatch, ScopeExhausted, ScopeExpired, ScopeIncidentMismatch, ScopeNotFound, ScopedExecutionRequired, can_execute, consume, get_scope, get_scope_store, info, isoformat, lower, max, now

### `async validate_scope_required(incident_id: str, action: str) -> None`
- **Async:** Yes
- **Docstring:** Validate that execution without scope should fail.  Called by /recovery/execute when no scope_id provided.
- **Calls:** ScopedExecutionRequired

### `requires_scoped_execution(risk_threshold: RiskClass)`
- **Async:** No
- **Docstring:** Decorator to enforce scoped pre-execution for risky recovery actions.  Usage:
- **Calls:** ScopedExecutionRequired, func, get, index, isinstance, pop, wraps

### `async test_recovery_scope(action_id: str, action_name: str, action_type: str, risk_class: str, parameters: Dict[str, Any], scope_type: str, scope_fraction: float) -> Dict[str, Any]`
- **Async:** Yes
- **Docstring:** Test a recovery action in scoped execution.  Returns dict with execution result for API response.
- **Calls:** ExecutionScope, RecoveryAction, RiskClass, ScopedExecutionContext, execute

## Classes

### `RiskClass(str, Enum)`
- **Docstring:** Risk classification for recovery actions.

### `ExecutionScope(str, Enum)`
- **Docstring:** Type of scoped execution.

### `ScopedExecutionResult`
- **Docstring:** Result of a scoped execution test.
- **Class Variables:** success: bool, cost_delta_cents: int, failure_count: int, policy_violations: List[str], execution_hash: str, duration_ms: int, scope_coverage: float, samples_tested: int, details: Dict[str, Any]

### `RecoveryAction`
- **Docstring:** A recovery action to be tested in scoped execution.
- **Class Variables:** id: str, name: str, risk_class: RiskClass, action_type: str, parameters: Dict[str, Any], target_agents: List[str], timeout_ms: int

### `ScopedExecutionContext`
- **Docstring:** M6 Scoped Execution primitive.
- **Methods:** __init__, execute, _dry_run_validate, _execute_scoped, _estimate_cost, _elapsed_ms, _compute_hash

### `ScopedExecutionRequired(Exception)`
- **Docstring:** Raised when a MEDIUM+ risk action is attempted without scoped pre-execution.

### `ScopeNotFound(Exception)`
- **Docstring:** Raised when a scope ID does not exist.

### `ScopeExhausted(Exception)`
- **Docstring:** Raised when a scope has been fully consumed.

### `ScopeExpired(Exception)`
- **Docstring:** Raised when a scope has expired.

### `ScopeActionMismatch(Exception)`
- **Docstring:** Raised when action does not match scope's allowed actions.

### `ScopeIncidentMismatch(Exception)`
- **Docstring:** Raised when execution targets a different incident than scope.

### `BoundExecutionScope`
- **Docstring:** A bound execution scope that gates recovery actions.
- **Methods:** is_valid, can_execute, consume, to_dict
- **Class Variables:** scope_id: str, incident_id: str, allowed_actions: List[str], max_cost_usd: float, max_attempts: int, expires_at: datetime, intent: str, target_agents: List[str], created_at: datetime, created_by: str, attempts_used: int, cost_used_usd: float, status: str, execution_log: List[Dict[str, Any]]

### `ScopeStore`
- **Docstring:** Thread-safe in-memory store for execution scopes.
- **Methods:** __new__, create_scope, get_scope, get_scopes_for_incident, revoke_scope, cleanup_expired
- **Class Variables:** _instance: Optional['ScopeStore']

## Attributes

- `logger` (line 63)
- `_scope_store` (line 496)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__` |

## Callers

L2 APIs (recovery actions), L5 workers

## Export Contract

```yaml
exports:
  functions:
    - name: get_scope_store
      signature: "get_scope_store() -> ScopeStore"
    - name: create_recovery_scope
      signature: "async create_recovery_scope(incident_id: str, action: str, intent: str, max_cost_usd: float, max_attempts: int, ttl_seconds: int, target_agents: Optional[List[str]], created_by: str) -> Dict[str, Any]"
    - name: execute_with_scope
      signature: "async execute_with_scope(scope_id: str, action: str, incident_id: str, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]"
    - name: validate_scope_required
      signature: "async validate_scope_required(incident_id: str, action: str) -> None"
    - name: requires_scoped_execution
      signature: "requires_scoped_execution(risk_threshold: RiskClass)"
    - name: test_recovery_scope
      signature: "async test_recovery_scope(action_id: str, action_name: str, action_type: str, risk_class: str, parameters: Dict[str, Any], scope_type: str, scope_fraction: float) -> Dict[str, Any]"
  classes:
    - name: RiskClass
      methods: []
    - name: ExecutionScope
      methods: []
    - name: ScopedExecutionResult
      methods: []
    - name: RecoveryAction
      methods: []
    - name: ScopedExecutionContext
      methods: [execute]
    - name: ScopedExecutionRequired
      methods: []
    - name: ScopeNotFound
      methods: []
    - name: ScopeExhausted
      methods: []
    - name: ScopeExpired
      methods: []
    - name: ScopeActionMismatch
      methods: []
    - name: ScopeIncidentMismatch
      methods: []
    - name: BoundExecutionScope
      methods: [is_valid, can_execute, consume, to_dict]
    - name: ScopeStore
      methods: [create_scope, get_scope, get_scopes_for_incident, revoke_scope, cleanup_expired]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
