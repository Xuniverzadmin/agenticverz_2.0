# hoc_cus_controls_L5_engines_budget_enforcement_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L5_engines/budget_enforcement_engine.py` |
| Layer | L4 — Domain Engine (System Truth) |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Budget enforcement decision-making (domain logic)

## Intent

**Role:** Budget enforcement decision-making (domain logic)
**Reference:** PIN-257 Phase R-3 (L5→L4 Violation Fix)
**Callers:** Background tasks, API endpoints

## Purpose

Domain engine for budget enforcement decisions.

---

## Functions

### `emit_budget_halt_decision(run_id: str, budget_limit_cents: int, budget_consumed_cents: int, step_cost_cents: int, completed_steps: int, total_steps: int, tenant_id: str) -> bool`
- **Async:** No
- **Docstring:** Convenience function to emit a budget enforcement decision.  This is the L4 entry point for budget enforcement decision emission.
- **Calls:** BudgetEnforcementEngine, emit_decision_for_halt

### `async process_pending_budget_decisions() -> int`
- **Async:** Yes
- **Docstring:** Process all pending budget halt decisions.  This function is intended to be called by a background task at startup
- **Calls:** BudgetEnforcementEngine, process_pending_halts

## Classes

### `BudgetEnforcementEngine`
- **Docstring:** L4 Domain Engine for budget enforcement decisions.
- **Methods:** __init__, emit_decision_for_halt, process_pending_halts, _parse_budget_from_error

## Attributes

- `logger` (line 38)
- `__all__` (line 337)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.controls.L6_drivers.budget_enforcement_driver` |
| External | `app.contracts.decisions` |

## Callers

Background tasks, API endpoints

## Export Contract

```yaml
exports:
  functions:
    - name: emit_budget_halt_decision
      signature: "emit_budget_halt_decision(run_id: str, budget_limit_cents: int, budget_consumed_cents: int, step_cost_cents: int, completed_steps: int, total_steps: int, tenant_id: str) -> bool"
    - name: process_pending_budget_decisions
      signature: "async process_pending_budget_decisions() -> int"
  classes:
    - name: BudgetEnforcementEngine
      methods: [emit_decision_for_halt, process_pending_halts]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
