# hoc_cus_analytics_L5_engines_sandbox

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/sandbox.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

CostSim V2 sandbox routing (V1/V2 comparison, shadow mode)

## Intent

**Role:** CostSim V2 sandbox routing (V1/V2 comparison, shadow mode)
**Reference:** PIN-470
**Callers:** cost simulation API

## Purpose

Sandbox routing layer for CostSim V1 vs V2.

---

## Functions

### `async simulate_with_sandbox(plan: List[Dict[str, Any]], budget_cents: int, allowed_skills: Optional[List[str]], tenant_id: Optional[str], run_id: Optional[str]) -> SandboxResult`
- **Async:** Yes
- **Docstring:** Convenience function for sandbox simulation.  Args:
- **Calls:** CostSimSandbox, simulate

### `get_sandbox(budget_cents: int, tenant_id: Optional[str]) -> CostSimSandbox`
- **Async:** No
- **Docstring:** Get a sandbox instance.  Note: For tenant isolation, always create a new instance
- **Calls:** CostSimSandbox

## Classes

### `SandboxResult`
- **Docstring:** Result from sandbox routing.
- **Methods:** production_result
- **Class Variables:** v1_result: SimulationResult, v2_result: Optional[V2SimulationResult], comparison: Optional[ComparisonResult], sandbox_enabled: bool, v2_error: Optional[str]

### `CostSimSandbox`
- **Docstring:** Sandbox router for CostSim V1 vs V2.
- **Methods:** __init__, _get_v2_adapter, simulate, _log_comparison

## Attributes

- `logger` (line 50)
- `_sandbox_instance: Optional[CostSimSandbox]` (line 274)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.costsim.circuit_breaker_async`, `app.costsim.config`, `app.costsim.models`, `app.costsim.v2_adapter`, `app.worker.simulate` |

## Callers

cost simulation API

## Export Contract

```yaml
exports:
  functions:
    - name: simulate_with_sandbox
      signature: "async simulate_with_sandbox(plan: List[Dict[str, Any]], budget_cents: int, allowed_skills: Optional[List[str]], tenant_id: Optional[str], run_id: Optional[str]) -> SandboxResult"
    - name: get_sandbox
      signature: "get_sandbox(budget_cents: int, tenant_id: Optional[str]) -> CostSimSandbox"
  classes:
    - name: SandboxResult
      methods: [production_result]
    - name: CostSimSandbox
      methods: [simulate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
