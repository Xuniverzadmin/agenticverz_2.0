# PIN-175: Phase 5B & Phase 5C Complete - Recovery Without Lying

**Status:** COMPLETE
**Category:** Milestone / Behavioral Changes
**Created:** 2025-12-26
**Closed:** 2025-12-26
**Session:** Phase 5B + Phase 5C Implementation

---

## Executive Summary

This session completed the last two trust-critical behavioral phases:

1. **Phase 5B Policy Pre-Check** - 18/18 tests pass
2. **Phase 5C Recovery Automation** - 19/19 tests pass

The system can now **fail, stop, block, and recover honestly**.

---

## Phase 5B: Policy Pre-Check (COMPLETE)

### Implementation

| File | Change |
|------|--------|
| `app/contracts/decisions.py` | Added `POLICY_PRE_CHECK` DecisionType |
| `app/contracts/decisions.py` | Added `POLICY_BLOCKED`, `POLICY_UNAVAILABLE` DecisionOutcomes |
| `app/contracts/decisions.py` | Added `emit_policy_precheck_decision()` helper |
| `app/policy/engine.py` | Added `pre_check()` method |
| `app/api/workers.py` | Wired pre-check into `/run` endpoint |
| `app/api/workers.py` | Added `PolicyStatusModel` and `policy_status` to response |

### Frozen Emission Rule

```
EMIT decision record IF AND ONLY IF:
  - posture == strict
  - AND (pre_check_failed OR policy_service_unavailable)

DO NOT EMIT decision record IF:
  - pre_check passed (default path)
  - posture == advisory (warnings go in PRE-RUN declaration)
```

### Test Results

```
18 tests collected
18 PASSED, 0 FAILED
```

---

## Phase 5C: Recovery Automation (COMPLETE)

### Implementation

| File | Change |
|------|--------|
| `app/contracts/decisions.py` | Added `RECOVERY_EVALUATION` DecisionType |
| `app/contracts/decisions.py` | Added `RECOVERY_APPLIED`, `RECOVERY_SUGGESTED`, `RECOVERY_SKIPPED` outcomes |
| `app/contracts/decisions.py` | Added `_check_recovery_evaluation_exists()` idempotency guard |
| `app/contracts/decisions.py` | Added `emit_recovery_evaluation_decision()` helper |
| `tests/contracts/test_g5c_recovery_automation.py` | Wired to real emission function |

### Recovery Taxonomy (Frozen)

| Class | Name | Auto-Apply | Human Approval | Reason |
|-------|------|------------|----------------|--------|
| R1 | Safe & Idempotent | YES | Not Required | Deterministic, no side effects, bounded |
| R2 | Risky | NO | Required | May have side effects, requires judgment |
| R3 | Forbidden | NEVER | N/A | Violates contracts, trust, or safety |

### Key Safety Rules

1. **429 Rate Limit Handling**:
   - With `Retry-After` header → R1 (auto-apply)
   - Without `Retry-After` header → R2 (suggest only)

2. **Partial Execution Failure Rule**:
   > Partial execution failure is R3 by default unless strictly step-local and idempotent.

3. **Max 1 Retry**: R1 auto-applies exactly once, then escalates

4. **No Recovery Loops**: Recovery attempt failure → R3 (hard stop)

### Decision Emission Rule

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

### Test Results

```
19 tests collected
19 PASSED, 0 FAILED
```

---

## Locked Invariants (Irreversible)

### Recovery

- Exactly **three classes**: R1 / R2 / R3
- **R1** auto-applies **once** → then escalates
- **R2** suggests only (founder-visible)
- **R3** is a hard stop (policy/budget/partial execution/loops)
- **Every recovery evaluation emits a decision**
- **No silent retries**, **no recovery loops**
- **`causal_role = post_run`** always

### Policy Pre-Check

- Policy success is silent (no POLICY_ALLOWED noise)
- Strict posture blocks before run creation
- Advisory posture never blocks
- All policy decisions have `causal_role = pre_run`
- Blocked runs have no `run_id`
- `request_id` enables timeline reconstruction

### Narrative Honesty

- Original failure remains visible
- Recovery attempts are explicit
- Customers see outcomes, not mechanics

---

## Current Position

```
✓ Phase 5A — Hard enforcement (budget)
✓ Phase 5B — Intent-time blocking (policy)
✓ Phase 5C — Honest, bounded recovery
→ Phase 5D — CARE optimization (learning)
→ WRAP — Beta readiness & market entry
```

From here, changes are **optimizations**, not **governance risks**.

---

## What This Unlocks

The system can now:
- **Fail** without hiding
- **Stop** without apologizing
- **Block** before damage
- **Recover** without lying

This is the bar for closed beta.

---

## Related PINs

| PIN | Title | Status |
|-----|-------|--------|
| [PIN-173](PIN-173-phase-5b-policy-pre-check-matrix.md) | Phase 5B Policy Pre-Check Matrix | COMPLETE |
| [PIN-174](PIN-174-phase-5c-recovery-automation-matrix.md) | Phase 5C Recovery Automation Matrix | COMPLETE |

---

## Session Discipline Maintained

- Test-first development (red → green)
- Contracts frozen before behavior changed
- Decision emission rules verified
- No ledger expansion
- No execution-time leakage
- Customer visibility preserved
- Founder timeline intact
- No regressions (5B tests still pass)
