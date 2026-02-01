# runtime_switch.py

**Path:** `backend/app/hoc/cus/hoc_spine/authority/runtime_switch.py`  
**Layer:** L4 — HOC Spine (Authority)  
**Component:** Authority

---

## Placement Card

```
File:            runtime_switch.py
Lives in:        authority/
Role:            Authority
Inbound:         ops_api.py, failure_mode_handler.py, health.py
Outbound:        app.hoc.cus.hoc_spine.services.time
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Module: runtime_switch
Violations:      none
```

## Purpose

Module: runtime_switch
Purpose: Provides runtime toggle for governance. Emergency kill switch.

Imports (Dependencies):
    - logging
    - datetime
    - threading (for atomic operations)

Exports (Provides):
    - is_governance_active() -> bool
    - disable_governance_runtime(reason, actor) -> None
    - enable_governance_runtime(actor) -> None
    - get_governance_state() -> GovernanceState
    - is_degraded_mode() -> bool (GAP-070)
    - enter_degraded_mode(reason, actor) -> None (GAP-070)
    - exit_degraded_mode(actor) -> None (GAP-070)

Wiring Points:
    - Called from: prevention_engine.py (check before enforcement)
    - Called from: runner.py (check before accepting new runs)
    - Called from: ops_api.py (manual toggle endpoint)
    - Emits: governance_state_changed event

Acceptance Criteria:
    - [x] AC-069-01: Governance active by default
    - [x] AC-069-02: Kill switch disables enforcement
    - [x] AC-069-03: Kill switch logs critical audit
    - [x] AC-069-04: Re-enable restores enforcement
    - [x] AC-069-05: OPS endpoint exists
    - [x] AC-069-06: Requires OPS permission
    - [x] AC-069-07: State visible in health
    - [x] AC-069-08: Thread-safe operations

## Import Analysis

**Spine-internal:**
- `app.hoc.cus.hoc_spine.services.time`

**External:**
- `app.events.subscribers`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `is_governance_active() -> bool`

Check if governance is currently active.

Returns:
    True if governance enforcement is active

### `is_degraded_mode() -> bool`

Check if system is in degraded mode (GAP-070).

Degraded mode:
- Governance is active
- New runs are blocked
- Existing runs complete with WARN

Returns:
    True if in degraded mode

### `disable_governance_runtime(reason: str, actor: str) -> None`

Emergency kill switch. Disables governance enforcement.

WARNING: This allows runs to bypass policy enforcement.
Use only for emergency incident response.

Args:
    reason: Why governance is being disabled
    actor: Who/what triggered the disable (user_id or "system")

### `enable_governance_runtime(actor: str) -> None`

Re-enable governance after emergency.

Args:
    actor: Who/what triggered the re-enable

### `enter_degraded_mode(reason: str, actor: str) -> None`

GAP-070: Enter degraded mode.

Degraded mode:
- Blocks new runs
- Existing runs complete with WARN
- Full audit emitted

Args:
    reason: Why entering degraded mode
    actor: Who/what triggered degraded mode

### `exit_degraded_mode(actor: str) -> None`

Exit degraded mode, return to normal operation.

Args:
    actor: Who/what triggered exit from degraded mode

### `get_governance_state() -> dict`

Get current governance state for health checks.

Returns:
    Dict with governance state details

### `reset_governance_state() -> None`

Reset governance state to defaults (for testing).

### `_emit_governance_event(event_type: str, reason: str, actor: str) -> None`

Emit governance state change event.

Args:
    event_type: Type of event (governance_disabled, governance_enabled, etc.)
    reason: Reason for the change
    actor: Who triggered the change

## Classes

### `GovernanceState`

Current governance state.

## Domain Usage

**Callers:** ops_api.py, failure_mode_handler.py, health.py

## Export Contract

```yaml
exports:
  functions:
    - name: is_governance_active
      signature: "is_governance_active() -> bool"
      consumers: ["orchestrator"]
    - name: is_degraded_mode
      signature: "is_degraded_mode() -> bool"
      consumers: ["orchestrator"]
    - name: disable_governance_runtime
      signature: "disable_governance_runtime(reason: str, actor: str) -> None"
      consumers: ["orchestrator"]
    - name: enable_governance_runtime
      signature: "enable_governance_runtime(actor: str) -> None"
      consumers: ["orchestrator"]
    - name: enter_degraded_mode
      signature: "enter_degraded_mode(reason: str, actor: str) -> None"
      consumers: ["orchestrator"]
    - name: exit_degraded_mode
      signature: "exit_degraded_mode(actor: str) -> None"
      consumers: ["orchestrator"]
    - name: get_governance_state
      signature: "get_governance_state() -> dict"
      consumers: ["orchestrator"]
    - name: reset_governance_state
      signature: "reset_governance_state() -> None"
      consumers: ["orchestrator"]
    - name: _emit_governance_event
      signature: "_emit_governance_event(event_type: str, reason: str, actor: str) -> None"
      consumers: ["orchestrator"]
  classes:
    - name: GovernanceState
      methods: []
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
    spine_internal: ['app.hoc.cus.hoc_spine.services.time']
    l7_model: []
    external: ['app.events.subscribers']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

