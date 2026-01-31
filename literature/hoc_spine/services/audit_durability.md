# audit_durability.py

**Path:** `backend/app/hoc/hoc_spine/services/audit_durability.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            audit_durability.py
Lives in:        services/
Role:            Services
Inbound:         ROK (L5), Facades (L4), AuditReconciler (L4)
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Module: durability
Violations:      none
```

## Purpose

Module: durability
Purpose: Enforce RAC durability before acknowledgment.

The rac_durability_enforce flag in GovernanceConfig controls whether
durability is strictly enforced before acknowledging audit operations.

When enabled:
    - Acks must be persisted to durable storage before being accepted
    - Expectations must be durably stored before run starts
    - In-memory-only mode raises RACDurabilityEnforcementError

This ensures audit contracts survive crashes and can be reconciled
even if workers fail.

Exports:
    - RACDurabilityEnforcementError: Raised when durability not satisfied
    - RACDurabilityChecker: Checks durability constraints
    - check_rac_durability: Quick helper function

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `check_rac_durability(enforcement_enabled: bool, durability_mode: str) -> DurabilityCheckResponse`

Quick helper to check RAC durability.

Args:
    enforcement_enabled: Whether rac_durability_enforce is True
    durability_mode: Current durability mode

Returns:
    DurabilityCheckResponse with status and metadata

### `ensure_rac_durability(operation: str, enforcement_enabled: bool, durability_mode: str) -> None`

Quick helper to ensure RAC durability or raise error.

Args:
    operation: Name of the operation being performed
    enforcement_enabled: Whether rac_durability_enforce is True
    durability_mode: Current durability mode

Raises:
    RACDurabilityEnforcementError: If enforcement enabled and not durable

## Classes

### `DurabilityCheckResult(str, Enum)`

Result of a durability check.

### `RACDurabilityEnforcementError(Exception)`

Raised when RAC durability enforcement fails.

This error indicates that an operation requiring durable storage
was attempted without durable backing store available.

#### Methods

- `__init__(message: str, operation: str, durability_mode: str, enforcement_enabled: bool)` — _No docstring._
- `to_dict() -> dict[str, Any]` — Convert to dictionary for logging/API responses.

### `DurabilityCheckResponse`

Response from a durability check.

#### Methods

- `to_dict() -> dict[str, Any]` — Convert to dictionary for API responses.

### `RACDurabilityChecker`

Checks and enforces RAC durability constraints.

GAP-050: Add durability checks to RAC.

The checker verifies that audit data is durably stored before
allowing acknowledgment operations when enforcement is enabled.

Usage:
    checker = RACDurabilityChecker(
        enforcement_enabled=True,
        durability_mode="REDIS",
    )

    # Before adding an ack
    checker.ensure_durable("add_ack")

    # Or check without raising
    response = checker.check()
    if not response.is_durable and response.enforcement_enabled:
        handle_durability_issue()

#### Methods

- `__init__(enforcement_enabled: bool, durability_mode: str)` — Initialize the durability checker.
- `from_governance_config(config: Any) -> 'RACDurabilityChecker'` — Create checker from GovernanceConfig.
- `from_audit_store(store: Any, enforcement_enabled: bool) -> 'RACDurabilityChecker'` — Create checker from AuditStore instance.
- `is_durable() -> bool` — Check if current mode is durable.
- `enforcement_enabled() -> bool` — Check if durability enforcement is enabled.
- `check() -> DurabilityCheckResponse` — Check durability status.
- `ensure_durable(operation: str) -> None` — Ensure durability or raise error.
- `should_allow_operation(operation: str) -> tuple[bool, str]` — Check if an operation should be allowed.

## Domain Usage

**Callers:** ROK (L5), Facades (L4), AuditReconciler (L4)

## Export Contract

```yaml
exports:
  functions:
    - name: check_rac_durability
      signature: "check_rac_durability(enforcement_enabled: bool, durability_mode: str) -> DurabilityCheckResponse"
      consumers: ["orchestrator"]
    - name: ensure_rac_durability
      signature: "ensure_rac_durability(operation: str, enforcement_enabled: bool, durability_mode: str) -> None"
      consumers: ["orchestrator"]
  classes:
    - name: DurabilityCheckResult
      methods: []
      consumers: ["orchestrator"]
    - name: RACDurabilityEnforcementError
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: DurabilityCheckResponse
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: RACDurabilityChecker
      methods:
        - from_governance_config
        - from_audit_store
        - is_durable
        - enforcement_enabled
        - check
        - ensure_durable
        - should_allow_operation
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
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

