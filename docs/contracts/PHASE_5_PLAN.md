# Phase 5: Behavioral Changes Plan

**Created:** 2025-12-25
**Status:** DRAFT - Awaiting founder review
**Prerequisite:** `contracts-stable-v1` tag (COMPLETE)

---

## Entry Criteria

Phase 5 may only begin after:

| Criterion | Status |
|-----------|--------|
| Phase 4 complete | COMPLETE |
| Contracts frozen | COMPLETE |
| Git tagged `contracts-stable-v1` | COMPLETE |
| Customer visibility validated | COMPLETE (Phase 4C-2) |
| Founder timeline validated | COMPLETE (Phase 4C-1) |

---

## Phase 5 Overview

**Purpose:** Transform contracts from visibility-only to enforcement.

Phase 4 made decisions visible. Phase 5 makes them binding.

| Phase | Focus | Risk Level |
|-------|-------|------------|
| 5A | Budget Enforcement | LOW (clear violation = clear stop) |
| 5B | Policy Pre-Checks | MEDIUM (blocking before execution) |
| 5C | Recovery Automation | MEDIUM (automated actions) |
| 5D | CARE Optimization | HIGH (requires trust from 5A-5C) |

---

## Phase 5A: Budget Enforcement

### Objective

Make `budget_enforcement: HARD` actually stop execution.

### Contract Reference

From `CONSTRAINT_DECLARATION_CONTRACT.md`:

> If `budget_enforcement = HARD`:
> - Execution MUST STOP when budget exhausted
> - No "advisory only" behavior

### Current State

- Budget tracking exists (`app/utils/budget_tracker.py`)
- `emit_budget_decision()` records decisions
- Enforcement is advisory (soft mode only)

### Changes Required

| Component | Change |
|-----------|--------|
| `budget_tracker.py` | Add `hard_budget_remaining()` check |
| `budget_tracker.py` | Raise `BudgetExhaustedException` when hard limit hit |
| Workflow engine | Catch exception, emit `budget_halt` decision |
| Customer visibility | Show `budget_halt` in outcome reconciliation |

### Validation Criteria

1. Run with hard budget, consume 100% → execution stops mid-run
2. Decision record shows `decision_type: budget`, `outcome: halt`
3. Customer outcome shows `budget: { status: "halted", reason: "limit_reached" }`
4. Founder timeline shows halt decision with causal chain

### Implementation Order

1. Add `BudgetExhaustedException`
2. Modify `enforce_budget()` to check hard mode
3. Update workflow engine exception handler
4. Update customer outcome endpoint
5. Write integration test

### Rollback Plan

If issues arise:
- Toggle `BUDGET_ENFORCEMENT_HARD=false` in env
- Existing soft mode continues

---

## Phase 5B: Policy Pre-Checks

### Objective

Block execution BEFORE start if policy posture is `strict` and violation detected.

### Contract Reference

From `PRE_RUN_CONTRACT.md`:

> Execution MUST NOT begin unless this contract is acknowledged.

From `CONSTRAINT_DECLARATION_CONTRACT.md`:

> If `budget_enforcement = HARD`: Execution MUST NOT proceed

### Current State

- Policy engine evaluates during execution (`app/policy/engine.py`)
- `emit_policy_decision()` records violations
- No pre-execution check exists

### Changes Required

| Component | Change |
|-----------|--------|
| `customer_visibility.py` | Add policy pre-check in `/pre-run` |
| `policy/engine.py` | Add `pre_check()` method (intent-only, no execution) |
| Acknowledgement flow | Require acknowledgement if strict policy applies |
| Goal endpoint | Check acknowledgement before creating run |

### Validation Criteria

1. Strict policy + violating intent → `/pre-run` shows `policy_blocked: true`
2. Without acknowledgement → `/agents/{id}/goals` rejects with clear error
3. Decision record shows `decision_type: policy`, `causal_role: pre_run`
4. Customer sees policy block reason BEFORE any execution

### Implementation Order

1. Add `policy/engine.py:pre_check()` method
2. Integrate into `/cus/pre-run`
3. Add `policy_blocked` to PreRunDeclaration model
4. Modify acknowledgement to require policy consent
5. Update goal endpoint to verify acknowledgement
6. Write integration test

### Rollback Plan

If issues arise:
- Set `POLICY_PRE_CHECK_ENABLED=false`
- Existing runtime-only evaluation continues

---

## Phase 5C: Recovery Automation

### Objective

Automatically execute safe recoveries without human approval.

### Contract Reference

From `DECISION_RECORD_CONTRACT.md`:

> `decision_source: system` - Decision made autonomously by system

### Current State

- Recovery evaluator suggests actions (`app/worker/recovery_evaluator.py`)
- `emit_recovery_decision()` records suggestions
- All recoveries require human approval

### Changes Required

| Component | Change |
|-----------|--------|
| `recovery_evaluator.py` | Add `is_safe_recovery()` classification |
| Recovery taxonomy | Define safe vs unsafe recoveries |
| Workflow engine | Auto-execute if `is_safe_recovery() == True` |
| Decision record | Emit `decision_source: system` for auto-recoveries |

### Safe Recovery Taxonomy

| Recovery Type | Safe? | Reason |
|---------------|-------|--------|
| Retry same step | YES | Idempotent, no side effects |
| Skip optional step | YES | Declared optional |
| Rollback to checkpoint | YES | Explicit state restoration |
| Invoke fallback skill | NO | May have side effects |
| Escalate to human | NO | Requires human decision |
| Modify input data | NO | Data integrity risk |

### Validation Criteria

1. Transient failure → automatic retry → success without human
2. Decision record shows `decision_source: system`, `decision_trigger: reactive`
3. Unsafe recovery → still requires human approval
4. Founder timeline shows automatic vs human-approved distinction

### Implementation Order

1. Define `RecoverySafetyClass` enum
2. Add `classify_safety()` to recovery evaluator
3. Implement auto-execution for safe class
4. Update decision emission with source/trigger
5. Write integration tests for each safety class

### Rollback Plan

If issues arise:
- Set `RECOVERY_AUTO_EXECUTE=false`
- All recoveries revert to human approval

---

## Phase 5D: CARE Optimization

### Objective

Tune CARE routing based on historical decision data.

### Contract Reference

From `DECISION_RECORD_CONTRACT.md`:

> `decision_trigger: autonomous` - Decision triggered by internal system logic

### Current State

- CARE routing works (`app/routing/care.py`)
- `emit_routing_decision()` records choices
- No learning from historical data

### Why Last

CARE optimization requires:
1. Trust in budget enforcement (5A) - know runs complete
2. Trust in policy pre-checks (5B) - know violations are caught
3. Trust in recovery automation (5C) - know failures are handled

Without 5A-5C trust, CARE optimization may route to unreliable agents.

### Changes Required

| Component | Change |
|-----------|--------|
| `routing/care.py` | Add `learn_from_outcomes()` method |
| Decision analysis | Query historical routing decisions |
| Affinity scoring | Update based on outcome correlation |
| Emission | Record `decision_trigger: autonomous` for learned routing |

### Learning Sources

| Source | Signal |
|--------|--------|
| Outcome reconciliation | Success rate per agent |
| Budget decisions | Cost efficiency per agent |
| Recovery decisions | Failure rate per agent |
| Policy decisions | Compliance rate per agent |

### Validation Criteria

1. Historical data influences routing weight
2. Decision record shows `decision_trigger: autonomous`
3. Founder timeline shows learning correlation
4. No routing to agents with poor outcome history

### Implementation Order

1. Build outcome aggregation query
2. Implement affinity score updater
3. Integrate into CARE routing
4. Add learning decision emission
5. Write validation tests

### Rollback Plan

If issues arise:
- Set `CARE_LEARNING_ENABLED=false`
- Static affinity scores used

---

## Phase 5 Execution Rules

### No Code Without Contract Check

Before any Phase 5 implementation:

```
1. Which contract obligation does this enforce?
2. Is the enforcement mode documented in the contract?
3. Does the implementation match the obligation exactly?
```

### No Contract Modification

Phase 5 implements frozen contracts. If a contract gap is discovered:

1. Document the gap
2. Propose delta in `OBLIGATION_DELTAS.md`
3. Founder review required
4. Only then modify contract

### Incremental Validation

Each phase must be validated before the next begins:

| Phase | Validation Gate |
|-------|-----------------|
| 5A | Budget halt observed in production |
| 5B | Policy block observed in production |
| 5C | Safe recovery auto-executed in production |
| 5D | Learned routing decision observed |

---

## Risk Assessment

| Phase | Risk | Mitigation |
|-------|------|------------|
| 5A | Runs halt unexpectedly | Soft mode fallback, clear customer messaging |
| 5B | Legitimate requests blocked | Advisory mode first, strict mode opt-in |
| 5C | Unsafe recovery auto-executed | Conservative taxonomy, human escalation default |
| 5D | Poor routing due to bad data | Minimum sample size, confidence thresholds |

---

## Timeline

No time estimates provided. Implementation order is strict:

```
5A → 5B → 5C → 5D
```

Each phase requires validation gate before proceeding.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `CONSTRAINT_DECLARATION_CONTRACT.md` | Budget/policy enforcement rules |
| `DECISION_RECORD_CONTRACT.md` | Decision source/trigger requirements |
| `PRE_RUN_CONTRACT.md` | Acknowledgement requirements |
| `OUTCOME_RECONCILIATION_CONTRACT.md` | Outcome decomposition rules |
| `PIN-171` | Phase 4B/4C implementation reference |

---

## Approval

This plan requires founder review before Phase 5A implementation begins.

| Reviewer | Status | Date |
|----------|--------|------|
| Founder | PENDING | - |
