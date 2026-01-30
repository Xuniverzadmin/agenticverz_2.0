# hoc_cus_controls_L5_schemas_simulation

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L5_schemas/simulation.py` |
| Layer | L5 — Domain Schema |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Limit simulation request/response schemas

## Intent

**Role:** Limit simulation request/response schemas
**Reference:** PIN-LIM-04
**Callers:** api/limits/simulate.py, services/limits/simulation_service.py

## Purpose

Limit Simulation Schemas (PIN-LIM-04)

---

## Classes

### `SimulationDecision(str, Enum)`
- **Docstring:** Simulation outcome decision.

### `MessageCode(str, Enum)`
- **Docstring:** Standardized message codes (no free-text messages).

### `LimitSimulationRequest(BaseModel)`
- **Docstring:** Request model for limit simulation (pre-execution check).
- **Class Variables:** tenant_id: Optional[str], worker_id: Optional[str], estimated_tokens: int, estimated_cost_cents: Optional[int], run_count: int, concurrency_delta: int, feature_id: Optional[str], user_id: Optional[str], project_id: Optional[str]

### `LimitCheckResult(BaseModel)`
- **Docstring:** Result of a single limit check.
- **Class Variables:** limit_id: Optional[str], limit_type: str, limit_name: str, current_value: Decimal, limit_value: Decimal, projected_value: Decimal, enforcement: str, decision: SimulationDecision, message_code: MessageCode

### `HeadroomInfo(BaseModel)`
- **Docstring:** Remaining headroom before hitting limits.
- **Class Variables:** tokens: int, cost_cents: int, runs: int, concurrent_runs: int

### `LimitWarning(BaseModel)`
- **Docstring:** Warning for soft limit approaching.
- **Class Variables:** limit_id: Optional[str], limit_type: str, message_code: MessageCode, current_percent: float

### `LimitSimulationResponse(BaseModel)`
- **Docstring:** Response model for limit simulation.
- **Class Variables:** decision: SimulationDecision, blocking_limit_id: Optional[str], blocking_limit_type: Optional[str], blocking_message_code: Optional[MessageCode], warnings: list[LimitWarning], headroom: HeadroomInfo, checks: list[LimitCheckResult], overrides_applied: list[str]

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic` |

## Callers

api/limits/simulate.py, services/limits/simulation_service.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: SimulationDecision
      methods: []
    - name: MessageCode
      methods: []
    - name: LimitSimulationRequest
      methods: []
    - name: LimitCheckResult
      methods: []
    - name: HeadroomInfo
      methods: []
    - name: LimitWarning
      methods: []
    - name: LimitSimulationResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
