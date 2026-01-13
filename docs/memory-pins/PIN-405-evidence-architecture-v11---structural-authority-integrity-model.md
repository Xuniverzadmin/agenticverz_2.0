# PIN-405: Evidence Architecture v1.1 - Structural Authority & Integrity Model

**Status:** ✅ COMPLETE
**Created:** 2026-01-12
**Category:** Architecture / Evidence System

---

## Summary

Implemented Evidence Architecture v1.1 with ExecutionCursor structural authority, split integrity computation (Assembler/Evaluator), and failure resolution semantics.

---

## Details

## Overview

Evidence Architecture v1.1 implements a truth-grade evidence system for execution observability. This PIN documents the complete implementation including Phase-1 wiring and Category B/C structural fixes.

## What Was Built

### Phase-1: Evidence Capture Wiring

Wired five evidence types through ExecutionContext:

| Class | Evidence Type | Trigger |
|-------|--------------|---------|
| H | environment_evidence | Run creation |
| B | activity_evidence | LLM/tool calls |
| G | provider_evidence | Provider response |
| D | policy_decisions | Policy evaluation |
| J | integrity_evidence | Terminal state |

### Watch-out Implementations

**Watch-out #1: Step Index Authority**
- Only executor may advance steps
- Implemented via ExecutionCursor (structural, not convention)

**Watch-out #3: Capture Failures in Integrity**
- Created evidence_capture_failures table
- Failures surface in integrity evidence
- Added resolution semantics (transient/permanent/superseded)

## Architectural Fixes (Category B & C)

### Category B1: Activity Evidence Taxonomy
Activity evidence is only for externally consequential actions:
- llm_invoke: YES (decision-bearing)
- http_call: YES (external effect)
- json_transform: NO (pure transform)

### Category B2: Integrity State Model
Separated execution outcome from integrity:
- IntegrityState: PENDING | SEALED (completeness)
- IntegrityGrade: PASS | WARN | FAIL (quality)
- These are distinct from execution status

### Category C1: ExecutionCursor Pattern
Structural step authority replaces string-based guards:
- ExecutionCursor owns step advancement
- Evidence writers receive read-only context
- Old next_step() emits deprecation warning

### Category C2: Split Integrity Computation
Split compute_integrity() into:
- IntegrityAssembler: Gathers facts from tables
- IntegrityEvaluator: Applies policy for grade

### Category C3: Failure Resolution Semantics
Formalized failure interpretation:
- TRANSIENT: May recover (network blip)
- PERMANENT: Cannot recover (schema mismatch)
- SUPERSEDED: Later capture succeeded

## Key Files

| File | Purpose |
|------|---------|
| app/core/execution_context.py | ExecutionContext + ExecutionCursor |
| app/evidence/capture.py | Evidence capture functions |
| app/evidence/integrity.py | Split integrity (Assembler/Evaluator) |
| app/evidence/__init__.py | Module exports |
| alembic/versions/084_*.py | evidence_capture_failures table |
| alembic/versions/085_*.py | resolution column |

## Verification Tests

All tests passed:
1. Plain production execution - PASSED
2. Mid-execution failure (Watch-out #3) - PASSED
3. Terminal integrity - PASSED
4. SDSR run - PASSED
5. ExecutionCursor authority - PASSED
6. IntegrityAssembler/Evaluator - PASSED
7. Failure resolution semantics - PASSED

## Migration Progress

### STEP 1: runner.py Migration - COMPLETE (2026-01-12)

Migrated `app/worker/runner.py` to use ExecutionCursor structural authority:

**Changes Made:**
- Import: `ExecutionCursor` instead of `ExecutionContext`
- Creation: `ExecutionCursor.create()` instead of `ExecutionContext.create()`
- Step advancement: `cursor.advance()` instead of `exec_ctx.next_step(_caller="executor")`
- Context passing: `cursor.context` (read-only) to evidence writers
- Phase transitions: `cursor.with_phase()` for RUNNING/TERMINAL states
- Variable renamed: `exec_ctx` to `cursor` throughout

**Verification:**
- Syntax check: PASSED
- Import check: PASSED
- `next_step()` not used in hot path: CONFIRMED (only deprecation warning remains)

### STEP 2: executor.py Migration - COMPLETE (2026-01-12)

Verified and documented `app/skills/executor.py` v1.1 compliance:

**Already Correct Design:**
- Receives `ExecutionContext` from `cursor.context` (read-only)
- Does NOT advance steps (no `next_step` or `advance` calls)
- Uses context for Activity (B) and Provider (G) evidence capture

**Documentation Updates:**
- Added layer header (L5 - Execution & Workers)
- Updated docstrings to reference v1.1 architecture
- Clarified read-only context usage in comments
- Added explicit note: "Executor MUST NOT advance steps"

**Verification:**
- Syntax check: PASSED
- Import check: PASSED
- No step advancement calls: CONFIRMED

### STEP 3: compute_integrity Delegation - COMPLETE (2026-01-12)

Updated `app/evidence/capture.py` to delegate to v2 split architecture:

**Changes Made:**
- `compute_integrity()` now imports and calls `compute_integrity_v2()`
- Updated file header reference to v1.1
- Updated module docstring with v1.1 changes
- Removed ~90 lines of duplicated logic

**Backward Compatibility:**
- Returns same dict structure as v1.0
- Original keys: `expected_artifacts`, `observed_artifacts`, `missing_artifacts`, `missing_reasons`, `capture_failures`, `integrity_score`, `integrity_status`
- New keys (additive): `integrity_state`, `integrity_grade`, `explanation`

**Architecture:**
```
compute_integrity(run_id)
    └──► compute_integrity_v2(run_id)
              └──► IntegrityAssembler.gather(run_id)  → IntegrityFacts
              └──► IntegrityEvaluator.evaluate(facts) → IntegrityEvaluation
```

**Verification:**
- Syntax check: PASSED
- Import check: PASSED
- v2 delegation: CONFIRMED

### STEP 4: inject_synthetic.py Cleanup - COMPLETE (2026-01-12)

Removed duplicate evidence capture from `scripts/sdsr/inject_synthetic.py`:

**SDSR Contract Compliance:**
- "Scenarios inject causes. Engines create effects."
- Evidence is an EFFECT, not a CAUSE
- Worker/runner creates evidence via canonical `app/evidence/capture.py`

**Changes Made:**
- Removed ~500 lines of duplicate evidence capture functions
- Removed `capture_full_taxonomy_evidence()` call from `materialize_and_emit_truth()`
- Removed dead code that collected observability evidence for the removed call
- Added comment blocks explaining the removal

**Removed Functions (now canonical in app/evidence/capture.py):**
- `capture_activity_evidence()`
- `capture_policy_decision()`
- `capture_provider_evidence()`
- `capture_environment_evidence()`
- `capture_integrity_evidence()`
- `capture_full_taxonomy_evidence()`

**Verification:**
- Syntax check: PASSED
- No runtime imports of removed functions
- SDSR contract compliant

### PHASE-1 FINAL CLOSURE: No Context → No Evidence - COMPLETE (2026-01-12)

Implemented hard runtime guard to enforce "No Context → No Evidence" invariant.

**Why Required:**
- The rule existed by convention, not by force
- Evidence functions accepting `None` context = forgery vector
- Must fail fast, fail loud, emit error artifact

**Changes Made:**
- Added `EvidenceContextError` exception class
- Added `_assert_context_exists()` hard guard function
- Guard added to all context-requiring evidence capture functions:
  - `capture_environment_evidence()` ✓
  - `capture_activity_evidence()` ✓
  - `capture_provider_evidence()` ✓
  - `capture_policy_decision_evidence()` ✓
- `capture_integrity_evidence()` takes `run_id` directly (by design)
- Exported `EvidenceContextError` from module `__init__.py`

**Guard Behavior:**
```python
if ctx is None:
    raise EvidenceContextError(
        evidence_type="...",
        message="Evidence capture blocked: ExecutionContext is None. "
                "No context → No evidence. This is a hard failure, not best-effort."
    )
```

**Verification:**
- All four guards tested: PASSED
- Exception raised correctly for None context
- Error logging with severity=CRITICAL

---

## PHASE-1 EXIT CRITERIA CHECKLIST

| Criteria | Status |
|----------|--------|
| ExecutionCursor is sole step authority | ✅ DONE |
| runner.py migrated to ExecutionCursor | ✅ DONE |
| executor.py migrated (documented, already correct) | ✅ DONE |
| inject_synthetic captures **no evidence** | ✅ DONE |
| Evidence capture **fails hard without context** | ✅ DONE |

**PHASE-1 STATUS: COMPLETE**

---

## Post-Phase-1 Steps (FROZEN until SDSR integration)

1. ~~Migrate runner.py to ExecutionCursor~~ DONE
2. ~~Migrate executor.py to use cursor pattern~~ DONE
3. ~~Update compute_integrity to delegate to v2~~ DONE
4. ~~Remove evidence capture from inject_synthetic.py~~ DONE
5. ~~Enforce no-context-no-evidence invariant~~ DONE (Phase-1 Closure)
6. Wire policy_decision evidence into policy engine (POST-SDSR)
7. Integrity scoring refinements (POST-SDSR)

**⚠️ EVIDENCE LAYER FROZEN** - Next focus: SDSR Integration

## Design Principles

```
ExecutionContext is the spine of execution truth.
ExecutionCursor is the heartbeat of execution progress.
Integrity explains failure, it does not hide it.
Authority is structural, not conventional.
Success is data, not silence.
```

---

## PIN-407 Correction: Complete Governance Footprint

**Status:** LOCKED (2026-01-12)

### Core Semantic Fix

The system is **EVENT-COMPLETE**, not event-sparse.

> **Every run produces activity, incident, policy, and logs.**
> The VALUES differ based on outcome. EXISTENCE does not vary.

### Evidence Capture Requirements (v1.1 UPDATED)

For **every run**, regardless of outcome:

| Evidence Type | Class | Mandatory | Description |
|--------------|-------|-----------|-------------|
| Activity | B | YES | Run is itself an activity record |
| Incident | - | YES | Outcome: SUCCESS, FAILURE, PARTIAL, BLOCKED |
| Policy | D | YES | Outcome: NO_VIOLATION, VIOLATION, ADVISORY, NOT_APPLICABLE |
| Logs | - | YES | Entry + exit logs correlated by run_id |
| Traces | - | YES | Finalized as COMPLETE or ABORTED |
| Integrity | J | YES | Computed at terminal state |

### Orthogonality Rule (CLARIFIED)

> Evidence **content** varies by run type.
> Evidence **existence** does not.

Pure transforms (e.g., `json_transform`):
- ✅ Activity exists (execution occurred)
- ✅ Incident exists (SUCCESS outcome)
- ✅ Policy exists (NO_VIOLATION)
- ❌ No external activity_evidence (no LLM call)
- ❌ No provider_evidence (no provider)
- ✅ Logs exist
- ✅ Traces exist

### Missing Success Records = Capture Failure

If success records are missing, this is a **capture failure**, not "nothing to capture".

Integrity evaluator MUST treat missing success artifacts as incomplete capture, not as valid absence.

