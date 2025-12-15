# PIN-067: M13 Iterations Cost Calculator Fix

**Date:** 2025-12-14
**Status:** COMPLETE
**Version:** 1.0.1
**Category:** Bug Fix / Feature Enhancement

---

## Summary

Fixed critical bug in the cost simulator where the `iterations` field was ignored, causing incorrect cost predictions, duration estimates, and budget validation failures.

---

## Problem Statement

The cost calculator was calculating costs as if each step executed only once, regardless of the `iterations` value sent by the UI.

### Symptoms

| Input | Expected | Actual (Before Fix) |
|-------|----------|---------------------|
| `llm_invoke x10` | 50 cents | 5 cents |
| `llm_invoke x50 + email_send x10` | 260 cents | 6 cents |
| Budget check (cost=250, budget=100) | FAIL | PASS |

### Root Cause

1. `PlanStep` model did not define an `iterations` field
2. `CostSimulator.simulate()` did not multiply cost by iterations
3. Latency calculation did not account for iterations
4. Risk calculation did not compound with iterations

---

## Solution

### 1. API Schema Change (`app/api/runtime.py`)

Added `iterations` field to `PlanStep` model:

```python
class PlanStep(BaseModel):
    skill: str = Field(...)
    params: Dict[str, Any] = Field(default_factory=dict)
    iterations: int = Field(default=1, ge=1, le=100)
```

### 2. Cost Calculation Fix (`app/worker/simulate.py`)

Updated simulation loop to multiply by iterations:

```python
iterations = step.get("iterations", 1)
step_cost = estimate["cost_cents"] * iterations
step_latency = estimate["latency_ms"] * iterations
```

### 3. Risk Compounding

Risk now compounds with iterations using probability theory:

```python
# P(at least one failure) = 1 - (1-p)^n
compounded_risk = 1.0 - ((1.0 - base_risk) ** iterations)
```

### 4. Step Estimates Enhanced

Step results now include:
- `iterations` - number of iterations
- `base_cost_cents` - cost for single execution
- `cost_cents` - total cost (base * iterations)
- `base_latency_ms` - latency for single execution
- `latency_ms` - total latency (base * iterations)

---

## Files Changed

| File | Change |
|------|--------|
| `backend/app/api/runtime.py` | Added `iterations` field to `PlanStep`, updated plan conversion |
| `backend/app/worker/simulate.py` | Cost/latency multiplication, risk compounding |
| `docs/openapi.yaml` | Updated `PlanStep` schema |
| `tests/test_m13_iterations_cost.py` | 30 regression tests |

---

## Test Results

```
30 passed in 1.48s

TestIterationsCostCalculation: 4 passed
TestIterationsBudgetValidation: 4 passed
TestIterationsLatencyCalculation: 3 passed
TestIterationsRiskCompounding: 3 passed
TestIterationsEdgeCases: 3 passed
TestIterationsAPIModel: 6 passed
TestM13AcceptanceCriteria: 7 passed
```

---

## Acceptance Criteria Verification

| # | Criteria | Status |
|---|----------|--------|
| AC1 | Iterations multiply both cost and latency | PASS |
| AC2 | Budget fails when total cost > budget | PASS |
| AC3 | Per-step cost shows cost x iterations | PASS |
| AC4 | Predicted duration scales with iterations | PASS |
| AC5 | Cost for 50 LLM calls = 250 (not 5) | PASS |
| AC6 | Cost for 10 LLM + 10 email = 60 (not 6) | PASS |
| AC7 | Backend rejects invalid iterations (0, -1, >100) | PASS |

---

## Backward Compatibility

- **Fully backward compatible**
- Default `iterations=1` preserves existing behavior
- No migration required
- Old API calls work unchanged

---

## API Example

### Request

```json
POST /api/v1/runtime/simulate
{
  "plan": [
    {"skill": "llm_invoke", "params": {}, "iterations": 10},
    {"skill": "email_send", "params": {}, "iterations": 5}
  ],
  "budget_cents": 100
}
```

### Response

```json
{
  "feasible": true,
  "estimated_cost_cents": 55,
  "estimated_duration_ms": 22500,
  "budget_remaining_cents": 45,
  "step_estimates": [
    {
      "skill_id": "llm_invoke",
      "iterations": 10,
      "base_cost_cents": 5,
      "estimated_cost_cents": 50,
      "base_latency_ms": 2000,
      "estimated_latency_ms": 20000
    },
    {
      "skill_id": "email_send",
      "iterations": 5,
      "base_cost_cents": 1,
      "estimated_cost_cents": 5,
      "base_latency_ms": 500,
      "estimated_latency_ms": 2500
    }
  ]
}
```

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Iteration limit bypass | Hard cap at 100 in schema validation |
| Cost overflow | Integer math safe up to 100 * max_cost |
| UI desync | OpenAPI updated, frontend uses same schema |

---

## Deployment Notes

1. No database migration required
2. No environment variable changes
3. Deploy backend first, then frontend (if applicable)
4. Monitor `/metrics` for cost simulation metrics

---

## Related PINs

- PIN-033: M8-M14 Machine-Native Realignment Roadmap
- PIN-065: AOS System Reference

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2025-12-14 | Claude | Initial implementation and fix |
