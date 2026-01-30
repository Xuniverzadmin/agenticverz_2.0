# hoc_cus_analytics_L5_engines_cost_model_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/cost_model_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Cost modeling and risk estimation domain authority (System Truth)

## Intent

**Role:** Cost modeling and risk estimation domain authority (System Truth)
**Reference:** PIN-470, PIN-254 Phase B Fix
**Callers:** CostSimV2Adapter (L3), simulation endpoints

## Purpose

L4 Cost Model Engine - Domain Authority for Cost/Risk Estimation

---

## Functions

### `get_skill_coefficients(skill_id: str) -> Dict[str, float]`
- **Async:** No
- **Docstring:** Get cost model coefficients for a skill (L4 domain function).  Args:
- **Calls:** get

### `estimate_step_cost(step_index: int, skill_id: str, params: Dict[str, Any]) -> StepCostEstimate`
- **Async:** No
- **Docstring:** Estimate cost and latency for a single step (L4 domain function).  L3 adapters must NOT implement their own estimation logic.
- **Calls:** StepCostEstimate, get, get_skill_coefficients, len, min, split, startswith, str

### `calculate_cumulative_risk(risks: List[Dict[str, float]]) -> float`
- **Async:** No
- **Docstring:** Calculate cumulative risk from individual risk factors (L4 domain function).  Uses probability complement formula: 1 - prod(1 - p_i)
- **Calls:** values

### `check_feasibility(estimated_cost_cents: int, budget_cents: int, permission_gaps: List[str], cumulative_risk: float, risk_threshold: float) -> FeasibilityResult`
- **Async:** No
- **Docstring:** Check if a plan is feasible (L4 domain function).  L3 adapters must NOT implement feasibility logic.
- **Calls:** FeasibilityResult, len

### `classify_drift(v1_cost_cents: int, v2_cost_cents: int, v1_feasible: bool, v2_feasible: bool) -> DriftAnalysis`
- **Async:** No
- **Docstring:** Classify drift between V1 and V2 simulation results (L4 domain function).  L3 adapters must NOT implement drift classification.
- **Calls:** DriftAnalysis, abs, max, min, round

### `is_significant_risk(probability: float) -> bool`
- **Async:** No
- **Docstring:** Check if a risk factor is significant enough to report (L4 domain function).

## Classes

### `DriftVerdict(str, Enum)`
- **Docstring:** Classification of drift between V1 and V2 simulation results.

### `StepCostEstimate`
- **Docstring:** Enhanced step estimate with confidence (L4 domain output).
- **Class Variables:** step_index: int, skill_id: str, cost_cents: float, latency_ms: float, confidence: float, risk_factors: Dict[str, float]

### `FeasibilityResult`
- **Docstring:** Result of feasibility check (L4 domain output).
- **Class Variables:** feasible: bool, budget_sufficient: bool, has_permissions: bool, risk_acceptable: bool, cumulative_risk: float, reason: Optional[str]

### `DriftAnalysis`
- **Docstring:** Result of drift analysis between V1 and V2 (L4 domain output).
- **Class Variables:** verdict: DriftVerdict, drift_score: float, cost_delta_pct: float, feasibility_match: bool, details: Dict[str, Any]

## Attributes

- `logger` (line 36)
- `SKILL_COST_COEFFICIENTS: Dict[str, Dict[str, float]]` (line 47)
- `UNKNOWN_SKILL_COEFFICIENTS: Dict[str, float]` (line 115)
- `DRIFT_THRESHOLD_MATCH` (line 138)
- `DRIFT_THRESHOLD_MINOR` (line 139)
- `DRIFT_THRESHOLD_MAJOR` (line 140)
- `DEFAULT_RISK_THRESHOLD` (line 148)
- `SIGNIFICANT_RISK_THRESHOLD` (line 151)
- `CONFIDENCE_DEGRADATION_LONG_PROMPT` (line 154)
- `CONFIDENCE_DEGRADATION_VERY_LONG_PROMPT` (line 155)
- `__all__` (line 433)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

CostSimV2Adapter (L3), simulation endpoints

## Export Contract

```yaml
exports:
  functions:
    - name: get_skill_coefficients
      signature: "get_skill_coefficients(skill_id: str) -> Dict[str, float]"
    - name: estimate_step_cost
      signature: "estimate_step_cost(step_index: int, skill_id: str, params: Dict[str, Any]) -> StepCostEstimate"
    - name: calculate_cumulative_risk
      signature: "calculate_cumulative_risk(risks: List[Dict[str, float]]) -> float"
    - name: check_feasibility
      signature: "check_feasibility(estimated_cost_cents: int, budget_cents: int, permission_gaps: List[str], cumulative_risk: float, risk_threshold: float) -> FeasibilityResult"
    - name: classify_drift
      signature: "classify_drift(v1_cost_cents: int, v2_cost_cents: int, v1_feasible: bool, v2_feasible: bool) -> DriftAnalysis"
    - name: is_significant_risk
      signature: "is_significant_risk(probability: float) -> bool"
  classes:
    - name: DriftVerdict
      methods: []
    - name: StepCostEstimate
      methods: []
    - name: FeasibilityResult
      methods: []
    - name: DriftAnalysis
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
