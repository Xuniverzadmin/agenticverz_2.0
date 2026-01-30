# hoc_cus_policies_L5_engines_kernel

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/kernel.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Mandatory execution kernel - single choke point for all EXECUTE power

## Intent

**Role:** Mandatory execution kernel - single choke point for all EXECUTE power
**Reference:** PIN-470, PIN-337
**Callers:** HTTP handlers, CLI dispatchers, SDK wrappers, workers, AUTO_EXECUTE

## Purpose

ExecutionKernel - PIN-337 Governance Enforcement Infrastructure

---

## Functions

### `get_enforcement_mode(capability_id: str) -> EnforcementMode`
- **Async:** No
- **Docstring:** Get enforcement mode for a capability.  Args:
- **Calls:** get

### `set_enforcement_mode(capability_id: str, mode: EnforcementMode) -> None`
- **Async:** No
- **Docstring:** Set enforcement mode for a capability.  This is CONFIG-DRIVEN, not code-driven.
- **Calls:** info

## Classes

### `EnforcementMode(str, Enum)`
- **Docstring:** Enforcement mode for capability execution.

### `InvocationContext`
- **Docstring:** Context for an execution invocation.
- **Class Variables:** subject: str, tenant_id: str, account_id: Optional[str], project_id: Optional[str], invocation_id: str, timestamp: str, request_id: Optional[str], client_ip: Optional[str], user_agent: Optional[str], metadata: dict[str, Any]

### `ExecutionResult`
- **Docstring:** Result of an execution through the kernel.
- **Class Variables:** success: bool, result: Any, error: Optional[Exception], invocation_id: str, capability_id: str, execution_vector: str, enforcement_mode: EnforcementMode, started_at: str, completed_at: str, duration_ms: float, envelope_emitted: bool, envelope_id: Optional[str]

### `ExecutionKernel`
- **Docstring:** Mandatory execution kernel - single choke point for all EXECUTE power.
- **Methods:** invoke, invoke_async, _emit_envelope, _record_invocation_start, _record_invocation_complete, is_known_capability, get_known_capabilities
- **Class Variables:** _KNOWN_CAPABILITIES: set[str]

## Attributes

- `logger` (line 45)
- `T` (line 47)
- `_ENFORCEMENT_CONFIG: dict[str, EnforcementMode]` (line 69)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.auth.execution_envelope` |

## Callers

HTTP handlers, CLI dispatchers, SDK wrappers, workers, AUTO_EXECUTE

## Export Contract

```yaml
exports:
  functions:
    - name: get_enforcement_mode
      signature: "get_enforcement_mode(capability_id: str) -> EnforcementMode"
    - name: set_enforcement_mode
      signature: "set_enforcement_mode(capability_id: str, mode: EnforcementMode) -> None"
  classes:
    - name: EnforcementMode
      methods: []
    - name: InvocationContext
      methods: []
    - name: ExecutionResult
      methods: []
    - name: ExecutionKernel
      methods: [invoke, invoke_async, is_known_capability, get_known_capabilities]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
