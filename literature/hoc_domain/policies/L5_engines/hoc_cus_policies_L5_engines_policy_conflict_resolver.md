# hoc_cus_policies_L5_engines_policy_conflict_resolver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/policy_conflict_resolver.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Resolve conflicts when multiple policies trigger different actions (pure logic)

## Intent

**Role:** Resolve conflicts when multiple policies trigger different actions (pure logic)
**Reference:** PIN-470, GAP-068
**Callers:** prevention_engine.py

## Purpose

Module: conflict_resolver
Purpose: Defines explicit rules for resolving policy conflicts.

---

## Functions

### `resolve_policy_conflict(actions: List[PolicyAction], strategy: ConflictResolutionStrategy) -> ResolvedAction`
- **Async:** No
- **Docstring:** Resolve conflict when multiple policies trigger.  Implements INV-005: Policy Conflict Determinism
- **Calls:** ResolvedAction, get, info, len, set, sorted, upper

### `create_conflict_log(run_id: str, resolved: ResolvedAction, strategy: ConflictResolutionStrategy) -> PolicyConflictLog`
- **Async:** No
- **Docstring:** Create audit log entry for conflict resolution.  Args:
- **Calls:** PolicyConflictLog, isoformat, now

### `get_action_severity(action: str) -> int`
- **Async:** No
- **Docstring:** Get the severity level for an action.  Args:
- **Calls:** get, upper

### `is_more_restrictive(action_a: str, action_b: str) -> bool`
- **Async:** No
- **Docstring:** Check if action_a is more restrictive than action_b.  Args:
- **Calls:** get_action_severity

## Classes

### `ActionSeverity(IntEnum)`
- **Docstring:** Action severity for conflict resolution. Higher = more restrictive.

### `ConflictResolutionStrategy(str, Enum)`
- **Docstring:** Resolution strategy for policy conflicts.

### `PolicyAction`
- **Docstring:** A triggered policy action.
- **Class Variables:** policy_id: str, policy_name: str, action: str, precedence: int, reason: str

### `ResolvedAction`
- **Docstring:** Result of conflict resolution.
- **Class Variables:** winning_action: str, winning_policy_id: Optional[str], resolution_reason: str, all_triggered: List[PolicyAction], conflict_detected: bool

### `PolicyConflictLog`
- **Docstring:** Audit log entry for conflict resolution.
- **Class Variables:** run_id: str, triggered_policies: List[str], winning_policy: Optional[str], winning_action: str, resolution_strategy: str, timestamp: str

## Attributes

- `logger` (line 63)
- `ACTION_SEVERITY` (line 121)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

prevention_engine.py

## Export Contract

```yaml
exports:
  functions:
    - name: resolve_policy_conflict
      signature: "resolve_policy_conflict(actions: List[PolicyAction], strategy: ConflictResolutionStrategy) -> ResolvedAction"
    - name: create_conflict_log
      signature: "create_conflict_log(run_id: str, resolved: ResolvedAction, strategy: ConflictResolutionStrategy) -> PolicyConflictLog"
    - name: get_action_severity
      signature: "get_action_severity(action: str) -> int"
    - name: is_more_restrictive
      signature: "is_more_restrictive(action_a: str, action_b: str) -> bool"
  classes:
    - name: ActionSeverity
      methods: []
    - name: ConflictResolutionStrategy
      methods: []
    - name: PolicyAction
      methods: []
    - name: ResolvedAction
      methods: []
    - name: PolicyConflictLog
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
