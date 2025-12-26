# PIN-174: Phase 5C - Recovery Automation Matrix

**Status:** COMPLETE
**Category:** Contracts / Behavioral Changes
**Created:** 2025-12-26
**Frozen:** 2025-12-26
**Milestone:** Post-M28 Behavioral Changes (Final Behavioral Phase)

---

## Scope Lock

> **This matrix is FROZEN as of 2025-12-26.**
> Any modification requires a delta proposal reviewed against the contract framework.
> No exceptions.
>
> Recovery is the last dangerous phase. If done wrong, it re-introduces silent behavior.
> If done right, the system becomes self-correcting without lying.

---

## Executive Summary

Phase 5C implements controlled recovery - the third and final behavioral change after contract freeze. When execution fails, the system must evaluate recovery options and either auto-apply (safe cases only), suggest (risky cases), or skip (forbidden cases). Every evaluation emits a decision. Silence is forbidden.

---

## Prerequisites

| Prerequisite | Status |
|--------------|--------|
| Phase 5A complete (budget enforcement) | COMPLETE |
| Phase 5B complete (policy pre-check) | COMPLETE |
| Contracts frozen (`contracts-stable-v1`) | COMPLETE |
| Decision emission infrastructure | COMPLETE |
| Failure catalog infrastructure | COMPLETE |

---

## Phase 5C Objective (Singular)

> **After execution fails, evaluate recovery options and either apply (R1), suggest (R2), or skip (R3) - always with a decision record.**

Nothing more. No other behavioral changes allowed.

---

## What Recovery IS and IS NOT

### Recovery IS

- A **post-failure option**, never pre-execution
- Explicitly **evaluated**, not implicit
- **Bounded**, **observable**, and **reversible**
- Either **auto-applied** (safe) or **human-approved** (risky)
- Always accompanied by a decision record

### Recovery is NOT

- Silent retries
- "Best effort" retries
- Implicit fallbacks
- Heuristics that skip decision emission
- Anything that runs without being explainable in the founder timeline
- Self-triggering (no recovery loops)

**If recovery is invisible, it is a bug.**

---

## Recovery Taxonomy (Frozen)

| Class | Name | Auto-Apply | Human Approval | Reason |
|-------|------|------------|----------------|--------|
| R1 | Safe & Idempotent | YES | Not Required | Deterministic, no side effects, bounded |
| R2 | Risky | NO | Required | May have side effects, requires judgment |
| R3 | Forbidden | NEVER | N/A | Violates contracts, trust, or safety |

No recovery exists outside these three classes.

---

## R1: Safe & Idempotent (Auto-Apply Allowed)

### Definition

Recovery that is:
- **Idempotent**: Same input, same output, no accumulated side effects
- **Bounded**: Maximum one retry per failure
- **Deterministic**: Outcome is predictable
- **Reversible**: No permanent state changes on failure

### Examples

| Scenario | Recovery Action | Why R1 |
|----------|-----------------|--------|
| Transient network timeout | Retry same request | Idempotent, bounded |
| Rate limit (429) **with** `Retry-After` header | Wait specified time + retry | Bounded, guided by upstream |
| Context window exceeded | Retry with smaller chunk | Deterministic reduction |
| Temporary service unavailable (503) | Retry after delay | Transient, idempotent |

**Note:** 429 without `Retry-After` is **R2**, not R1 (see below).

### Auto-Apply Rules

1. Auto-apply **exactly once** per failure
2. Create new **attempt_id** for the retry
3. Preserve original **request_id** and **run_id**
4. Emit decision with `recovery_applied`
5. If retry fails, do NOT retry again (escalate to R2 or fail)

---

## R2: Risky (Human Approval Required)

### Definition

Recovery that:
- **May have side effects**: Different tool, different model, different approach
- **Requires judgment**: Trade-offs exist
- **Is not guaranteed**: Success uncertain
- **Cannot be auto-reversed**: Needs human oversight

### Examples

| Scenario | Recovery Suggestion | Why R2 |
|----------|---------------------|--------|
| Rate limit (429) **without** `Retry-After` | Suggest wait + retry | No guidance, may worsen load |
| Tool consistently fails | Suggest alternative tool | Different behavior possible |
| Model returns poor quality | Suggest different model | Cost/quality trade-off |
| R1 retry also failed | Suggest manual intervention | Exhausted safe options |

### Suggestion Rules

1. Emit decision with `recovery_suggested`
2. **Do NOT auto-apply**
3. Surface suggestion to **founder only** (not customer)
4. Include: what failed, what's suggested, what's the trade-off
5. Await explicit approval before any action
6. If approved, create new attempt with `recovery_approved_by: founder_id`

---

## R3: Forbidden (Never Recover)

### Definition

Recovery that:
- **Violates contracts**: Would break PRE-RUN, CONSTRAINT, DECISION, or OUTCOME
- **Violates trust**: Would hide information from founder or customer
- **Violates safety**: Would bypass policy or budget
- **Creates loops**: Would trigger another recovery evaluation

### Examples

| Scenario | Why R3 |
|----------|--------|
| Policy violation caused failure | Retry would re-violate |
| Budget exhausted caused halt | Retry would exceed budget |
| Safety rule triggered | Retry would bypass safety |
| Recovery already attempted | Would create loop |
| Failure was in recovery code itself | Infinite recursion risk |
| **Partial execution failure** | May duplicate side effects |

### Partial Execution Failure Rule (MANDATORY)

> **Partial execution failure is R3 by default unless the failure is strictly step-local and idempotent.**

This means:
- If some steps succeeded before failure, **do not auto-retry**
- Retry could duplicate completed work (side effects)
- Retry creates timeline ambiguity ("half-healed" runs)
- Only if the failed step is **provably isolated and idempotent** may it be classified as R1

This is a **hard safety boundary**, not an optimization.

### Forbidden Rules

1. Emit decision with `recovery_skipped`
2. Include reason: which contract/rule would be violated
3. **No retry**, **no suggestion**, **no override**
4. Final failure stands
5. Log for founder visibility

---

## Decision Types (Frozen)

```python
class DecisionType(str, Enum):
    # ... existing ...
    RECOVERY_EVALUATION = "recovery_evaluation"  # Phase 5C: Post-failure recovery check

class DecisionOutcome(str, Enum):
    # ... existing ...
    RECOVERY_APPLIED = "recovery_applied"      # R1: Auto-recovery executed
    RECOVERY_SUGGESTED = "recovery_suggested"  # R2: Human approval needed
    RECOVERY_SKIPPED = "recovery_skipped"      # R3: Forbidden or not applicable
```

---

## Decision Emission Rule (Frozen)

```
ALWAYS emit exactly one RECOVERY_EVALUATION decision after any:
  - execution_halted
  - execution_failed

Outcome mapping:
  - R1 and applied → recovery_applied
  - R2 and suggested → recovery_suggested
  - R3 or no applicable recovery → recovery_skipped

NEVER:
  - Skip emission (silence is forbidden)
  - Emit multiple recovery decisions for same failure
  - Emit recovery decision without preceding failure
```

---

## Recovery Decision Record (When Emitted)

```python
DecisionRecord(
    decision_type=DecisionType.RECOVERY_EVALUATION,
    decision_source="system",
    decision_trigger="reactive",  # Recovery is always reactive to failure
    decision_outcome=DecisionOutcome.RECOVERY_APPLIED,  # or SUGGESTED or SKIPPED
    decision_reason="R1: Transient network timeout, retry applied",
    decision_inputs={
        "failure_type": "network_timeout",
        "failure_step": 3,
        "recovery_class": "R1",
        "recovery_action": "retry_same_request",
        "attempt_number": 2,
    },
    run_id="<original_run_id>",
    request_id="<original_request_id>",
    causal_role=CausalRole.POST_RUN,  # Always post-failure
    details={
        "original_failure": {...},
        "recovery_bounded": True,
        "max_attempts": 2,
    }
)
```

---

## Execution Rules (Hard Guards)

### Rule 1 - No Recovery Without a Failure

Recovery evaluation occurs **only after**:
- `execution_halted` (budget, policy, safety)
- `execution_failed` (error, timeout, external failure)

Never on success. Never pre-emptively.

### Rule 2 - Auto-Recovery Only for R1

```
IF recovery_class == R1:
    auto_apply = True
    max_attempts = 2  # Original + 1 retry
    emit(recovery_applied)
ELSE:
    auto_apply = False
```

### Rule 3 - Human Approval for R2

```
IF recovery_class == R2:
    emit(recovery_suggested)
    DO NOT RETRY
    surface_to_founder(suggestion)
    await_approval()  # May never come
```

Customers never see recovery suggestions. Customers never approve recoveries.

### Rule 4 - R3 Is a Hard Stop

```
IF recovery_class == R3:
    emit(recovery_skipped)
    reason = "Violates: {contract/rule}"
    NO RETRY
    NO SUGGESTION
    NO OVERRIDE
```

### Rule 5 - No Recovery Loops

```
IF current_execution.is_recovery_attempt:
    recovery_class = R3  # Force forbidden
    emit(recovery_skipped, reason="loop_prevention")
```

A recovery attempt that fails cannot trigger another recovery.

---

## Outcome Reconciliation (Required)

After recovery evaluation, the outcome must show:

| Field | Description |
|-------|-------------|
| `original_failure` | What failed and why |
| `recovery_evaluated` | True (always) |
| `recovery_class` | R1, R2, or R3 |
| `recovery_applied` | True if R1 executed |
| `recovery_succeeded` | True if retry fixed issue |
| `final_status` | Actual end state |

No "healed" narratives. Only facts.

### Visibility Rules

| Audience | Sees |
|----------|------|
| Founder | Full recovery timeline: failure, evaluation, action, outcome |
| Customer | Final outcome only, with honest status (no hidden mechanics) |

---

## Stop Conditions (Automatic Phase Halt)

Phase 5C implementation must **stop immediately** if:

1. A retry occurs without a decision record
2. A recovery modifies the original failure record
3. A customer sees recovery mechanics (R1/R2/R3 classification)
4. Recovery triggers another recovery (loop detected)
5. Decision record count grows unexpectedly (noise)
6. Recovery bypasses policy or budget

If any condition occurs: **rollback**.

---

## Frozen Behavioral Matrix

| ID | Behavior | Class | Contract | Decision Outcome |
|----|----------|-------|----------|------------------|
| 5C-01 | Auto-retry transient failure | R1 | OUTCOME | recovery_applied |
| 5C-02 | Suggest alternative after R1 exhausted | R2 | DECISION | recovery_suggested |
| 5C-03 | Skip recovery after policy violation | R3 | CONSTRAINT | recovery_skipped |
| 5C-04 | Skip recovery after budget halt | R3 | PRE-RUN | recovery_skipped |
| 5C-05 | Skip recovery after safety trigger | R3 | CONSTRAINT | recovery_skipped |
| 5C-06 | Prevent recovery loop | R3 | DECISION | recovery_skipped |
| 5C-07 | Emit decision on every failure | any | DECISION | (any) |
| 5C-08 | Surface recovery to founder timeline | any | OUTCOME | (visibility) |
| 5C-09 | Hide recovery mechanics from customer | any | PRE-RUN | (visibility) |
| 5C-10 | Preserve original failure in outcome | any | OUTCOME | (reconciliation) |

---

## E2E Test Matrix (Design)

| Test ID | Scenario | Expected Outcome |
|---------|----------|------------------|
| G5C-01 | Transient timeout, R1 applies | Decision: recovery_applied, retry succeeds |
| G5C-02 | Transient timeout, R1 retry also fails | Decision: recovery_applied, then recovery_suggested (R2) |
| G5C-03 | Tool failure, R2 suggested | Decision: recovery_suggested, no auto-retry |
| G5C-04 | Policy violation failure | Decision: recovery_skipped (R3), no retry |
| G5C-05 | Budget halt failure | Decision: recovery_skipped (R3), no retry |
| G5C-06 | Recovery attempt fails | Decision: recovery_skipped (R3 loop prevention) |
| G5C-07 | Success path | No recovery_evaluation decision |
| G5C-08 | Failure without recovery candidate | Decision: recovery_skipped (no applicable) |
| G5C-09 | Founder timeline shows recovery | Timeline includes all recovery decisions |
| G5C-10 | Customer outcome is reconciled | Final status shown, mechanics hidden |
| G5C-11 | No silent retries | Every retry has decision record |
| G5C-12 | No recovery loops | Second failure in retry → R3 |
| G5C-13 | 429 with Retry-After header | Decision: recovery_applied (R1), wait + retry |
| G5C-14 | 429 without Retry-After header | Decision: recovery_suggested (R2), no auto-retry |
| G5C-15 | Partial execution failure (steps succeeded before fail) | Decision: recovery_skipped (R3), no retry |

---

## Explicit Non-Goals (Forbidden in Phase 5C)

1. **No policy logic changes** - Policy is frozen (5B)
2. **No budget behavior changes** - Budget is frozen (5A)
3. **No CARE routing changes** - Routing is unchanged
4. **No learning/adaptation** - Recovery is static classification
5. **No customer-facing approval UI** - Founders only
6. **No infinite retry mechanisms** - Max 1 retry (R1)
7. **No recovery heuristics** - Classification is deterministic
8. **No recovery across runs** - Recovery is per-execution only

---

## Implementation Order

| Step | Task | Status |
|------|------|--------|
| 1 | Freeze PIN-174 matrix | COMPLETE |
| 2 | Add RECOVERY_EVALUATION to DecisionType | COMPLETE |
| 3 | Add recovery outcomes to DecisionOutcome | COMPLETE |
| 4 | Create recovery classifier (R1/R2/R3) | COMPLETE |
| 5 | Add emit_recovery_evaluation_decision() helper | COMPLETE |
| 6 | Wire recovery evaluation into test harness | COMPLETE |
| 7 | Write E2E tests (red first) | COMPLETE |
| 8 | Implement until green | COMPLETE |
| 9 | Verify no regressions (5B tests) | COMPLETE |

---

## Why This Is the Last Hard Part

After Phase 5C:
- The system can fail, stop, block, and recover **honestly**
- Founders can delegate trust (R1 is safe)
- Beta users won't hit mysterious behavior
- CARE optimization becomes safe (Phase 5D)

This is where most systems lie. We are explicitly designing not to.

---

## Completion Note

Phase 5C implementation complete (2025-12-26).

Test results:
- 19/19 Phase 5C tests pass
- 18/18 Phase 5B tests pass (no regressions)

The system can now fail, stop, block, and recover honestly.
