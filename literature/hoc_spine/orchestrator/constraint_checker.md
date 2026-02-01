# constraint_checker.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/constraint_checker.py`  
**Layer:** L4 — HOC Spine (Orchestrator)  
**Component:** Orchestrator

---

## Placement Card

```
File:            constraint_checker.py
Lives in:        orchestrator/
Role:            Orchestrator
Inbound:         worker/runtime/trace_collector.py, services/logging_service.py
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Module: constraint_checker
Violations:      none
```

## Purpose

Module: constraint_checker
Purpose: Enforce inspection constraints from MonitorConfig.

Inspection constraints are "negative capabilities" - they define what
a policy is NOT allowed to inspect or capture. Before any logging
operation, the runner/worker must check these constraints.

Constraint Fields (from MonitorConfig):
    - allow_prompt_logging: Can prompts be logged?
    - allow_response_logging: Can responses be logged?
    - allow_pii_capture: Can PII be captured?
    - allow_secret_access: Can secrets be accessed?

Exports:
    - InspectionOperation: Enum of operations requiring checks
    - InspectionConstraintViolation: Violation record
    - InspectionConstraintChecker: Main enforcement class
    - check_inspection_allowed: Quick helper function
    - get_constraint_violations: Get all violations

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `check_inspection_allowed(operation: InspectionOperation, allow_prompt_logging: bool, allow_response_logging: bool, allow_pii_capture: bool, allow_secret_access: bool) -> bool`

Quick helper to check if an operation is allowed.

Args:
    operation: The operation to check
    allow_prompt_logging: Whether prompts can be logged
    allow_response_logging: Whether responses can be logged
    allow_pii_capture: Whether PII can be captured
    allow_secret_access: Whether secrets can be accessed

Returns:
    True if operation is allowed, False otherwise

### `get_constraint_violations(operations: list[InspectionOperation], allow_prompt_logging: bool, allow_response_logging: bool, allow_pii_capture: bool, allow_secret_access: bool) -> list[dict[str, Any]]`

Get all constraint violations for a set of operations.

Args:
    operations: List of operations to check
    allow_prompt_logging: Whether prompts can be logged
    allow_response_logging: Whether responses can be logged
    allow_pii_capture: Whether PII can be captured
    allow_secret_access: Whether secrets can be accessed

Returns:
    List of violation dicts (empty if all allowed)

## Classes

### `InspectionOperation(str, Enum)`

Operations that require inspection constraint checks.

### `InspectionConstraintViolation`

Record of an inspection constraint violation.

Created when an operation is attempted that violates
the MonitorConfig inspection constraints.

#### Methods

- `to_dict() -> dict[str, Any]` — Convert to dictionary for API responses.

### `InspectionConstraintChecker`

Enforces inspection constraints from MonitorConfig.

This class checks whether logging and data capture operations
are allowed based on the MonitorConfig's inspection constraint
settings (negative capabilities).

GAP-033: Wire MonitorConfig flags to runner.

Usage:
    checker = InspectionConstraintChecker(monitor_config)
    if checker.is_allowed(InspectionOperation.LOG_PROMPT):
        # Log the prompt
    else:
        # Skip logging, constraint forbids it

#### Methods

- `__init__(allow_prompt_logging: bool, allow_response_logging: bool, allow_pii_capture: bool, allow_secret_access: bool)` — Initialize checker with constraint values.
- `from_monitor_config(config: Any) -> 'InspectionConstraintChecker'` — Create checker from a MonitorConfig instance.
- `from_snapshot(snapshot: dict[str, Any]) -> 'InspectionConstraintChecker'` — Create checker from a MonitorConfig snapshot dict.
- `is_allowed(operation: InspectionOperation) -> bool` — Check if an operation is allowed.
- `check(operation: InspectionOperation) -> Optional[InspectionConstraintViolation]` — Check an operation and return violation if not allowed.
- `check_all(operations: list[InspectionOperation]) -> list[InspectionConstraintViolation]` — Check multiple operations and return all violations.
- `get_allowed_operations() -> list[InspectionOperation]` — Get all allowed operations.
- `get_denied_operations() -> list[InspectionOperation]` — Get all denied operations.
- `to_dict() -> dict[str, Any]` — Convert constraints to dictionary.

## Domain Usage

**Callers:** worker/runtime/trace_collector.py, services/logging_service.py

## Export Contract

```yaml
exports:
  functions:
    - name: check_inspection_allowed
      signature: "check_inspection_allowed(operation: InspectionOperation, allow_prompt_logging: bool, allow_response_logging: bool, allow_pii_capture: bool, allow_secret_access: bool) -> bool"
      consumers: ["orchestrator"]
    - name: get_constraint_violations
      signature: "get_constraint_violations(operations: list[InspectionOperation], allow_prompt_logging: bool, allow_response_logging: bool, allow_pii_capture: bool, allow_secret_access: bool) -> list[dict[str, Any]]"
      consumers: ["orchestrator"]
  classes:
    - name: InspectionOperation
      methods: []
      consumers: ["orchestrator"]
    - name: InspectionConstraintViolation
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: InspectionConstraintChecker
      methods:
        - from_monitor_config
        - from_snapshot
        - is_allowed
        - check
        - check_all
        - get_allowed_operations
        - get_denied_operations
        - to_dict
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc.api.*"
    - "hoc_spine.adapters.*"
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

