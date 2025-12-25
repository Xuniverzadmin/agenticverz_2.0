# PIN-172: Phase 5A - Budget Enforcement

**Status:** IN PROGRESS
**Category:** Contracts / Implementation
**Created:** 2025-12-25
**Updated:** 2025-12-25
**Milestone:** Post-M28 Behavioral Changes

---

## Executive Summary

Phase 5A implements hard budget enforcement - the first behavioral change after contract freeze. When budget mode is declared as "hard" in PRE-RUN and acknowledged by the customer, execution must halt when the limit is reached.

---

## Prerequisites (ALL COMPLETE)

| Prerequisite | Status |
|--------------|--------|
| Phase 4 complete | COMPLETE |
| Contracts frozen (`contracts-stable-v1`) | COMPLETE |
| Customer visibility validated | COMPLETE |
| Founder timeline validated | COMPLETE |

---

## Phase 5A Objective (Singular)

> **When budget mode = hard, execution must halt when the limit is reached.**

Nothing more. No other behavioral changes allowed.

---

## Step 1: Choke Point Identification (COMPLETE)

### Single Choke Point

**Location:** `backend/app/worker/runner.py` step-execution loop (~lines 360-379)

**Rationale:**
- Token consumption is known AFTER each step (`result.side_effects.cost_cents`)
- Can halt BETWEEN steps (never mid-step)
- Partial results are coherent (`tool_calls` list)
- Existing exception boundary exists

### Gap Identified

Current state:
- Step costs are NOT deducted during execution
- Only planner costs are deducted (line 239)
- `deduct_budget()` failure is logged but ignored

---

## Critical Correction Applied

### REJECTED: ENV-based hard mode

```
BUDGET_HARD_MODE=true  # WRONG - violates contracts
```

### APPROVED: PRE-RUN sourced budget mode

```
budget.mode sourced from acknowledged PRE-RUN declaration
Runner enforces, never decides
```

**Rationale:**
- Budget mode is a customer-acknowledged contract
- ENV-based enforcement creates hidden behavior
- Would break predictability built in Phase 4

---

## Steps Remaining

| Step | Description | Status |
|------|-------------|--------|
| Step 1 | Identify single choke point | COMPLETE |
| Step 2 | Implement hard stop at choke point | PENDING |
| Step 3 | Emit budget_enforcement decision | PENDING |
| Step 4 | Emit outcome reconciliation record | PENDING |
| Step 5 | Return partial results cleanly | PENDING |
| Step 6 | Re-run PIN-167 scenarios 1 and 4 | PENDING |

---

## Allowed Changes (Exhaustive)

| File | Change |
|------|--------|
| `runner.py` | Deduct step cost after each step |
| `runner.py` | If `budget.mode == hard` AND exhausted → halt |
| `runner.py` | Emit `budget_enforcement` decision |
| `runner.py` | Return partial results with `status="halted"` |

---

## Forbidden Changes

- Soft budget behavior
- Simulation logic
- Cost estimation math
- Recovery behavior
- CARE routing
- Policy posture
- Alerts, UI, dashboards

---

## Decision Record Required

When hard budget enforcement halts execution:

```
decision_type: budget_enforcement
decision_source: system
decision_trigger: reactive
decision_outcome: execution_halted
```

---

## Outcome Reconciliation Required

```
outcome_status: halted
halt_reason: hard_budget_limit
execution_completion: partial
budget:
  mode: hard
  limit: <declared limit>
  consumed: <actual consumption at halt>
```

---

## Stop Conditions

Phase 5A must halt immediately if:
- New ledger entry appears
- Soft budget behavior changes
- Enforcement differs from PRE-RUN declaration
- Silent halt (no decision record)
- Scope creep suggestions

---

## Related Documents

- PIN-170: System Contract Governance Framework
- PIN-171: Phase 4B/4C - Causal Binding & Customer Visibility
- `docs/contracts/PHASE_5_PLAN.md`
- `docs/contracts/CONSTRAINT_DECLARATION_CONTRACT.md`

---

## Resume Point

Next session: Implement Step 2 (hard stop at choke point) with budget mode sourced from acknowledged PRE-RUN declaration.
