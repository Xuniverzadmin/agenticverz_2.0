# hoc_cus_policies_L5_engines_plan_generation_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/plan_generation_engine.py` |
| Layer | L4 — Domain Engine (System Truth) |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Plan generation (domain logic)

## Intent

**Role:** Plan generation (domain logic)
**Reference:** PIN-257 Phase R-2 (L5→L4 Violation Fix)
**Callers:** API endpoints (L2), run creation flow

## Purpose

Domain engine for plan generation.

---

## Functions

### `generate_plan_for_run(agent_id: str, goal: str, run_id: str) -> PlanGenerationResult`
- **Async:** No
- **Docstring:** Convenience function to generate a plan for a run.  This is the L4 entry point for plan generation. It should be called
- **Calls:** PlanGenerationContext, PlanGenerationEngine, generate, get_budget_tracker, get_status

## Classes

### `PlanGenerationContext`
- **Docstring:** Context for plan generation.
- **Class Variables:** agent_id: str, goal: str, run_id: str, agent_budget_cents: int

### `PlanGenerationResult`
- **Docstring:** Result of plan generation.
- **Class Variables:** plan: Dict[str, Any], plan_json: str, steps: List[Dict[str, Any]], context_summary: Optional[str], memory_snippet_count: int, validation_valid: bool, validation_warnings: List[str]

### `PlanGenerationEngine`
- **Docstring:** L4 Domain Engine for plan generation.
- **Methods:** __init__, generate

## Attributes

- `logger` (line 40)
- `__all__` (line 252)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.memory`, `app.planners`, `app.skills`, `app.utils.budget_tracker`, `app.utils.plan_inspector` |

## Callers

API endpoints (L2), run creation flow

## Export Contract

```yaml
exports:
  functions:
    - name: generate_plan_for_run
      signature: "generate_plan_for_run(agent_id: str, goal: str, run_id: str) -> PlanGenerationResult"
  classes:
    - name: PlanGenerationContext
      methods: []
    - name: PlanGenerationResult
      methods: []
    - name: PlanGenerationEngine
      methods: [generate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
