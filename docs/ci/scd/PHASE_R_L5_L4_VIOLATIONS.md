# Phase-R: L5→L4 Violation Classification

**STATUS: OBSERVATION COMPLETE**

**Date:** 2026-01-01
**Phase:** Phase-R (Architecture Realignment)
**Reference:** PHASE_R_ARCHITECTURE_REALIGNMENT.md

---

## 1. Summary

```
L5→L4 VIOLATION INVENTORY

Total Violations: 11 import locations
Unique L4 Modules: 6
L5 Files Affected: 3

Classification Status: COMPLETE
Code Changes: NONE (observation only)
```

---

## 2. Violation Inventory

### 2.1 By File

| # | L5 File | Line | L4 Import | L4 Module Layer |
|---|---------|------|-----------|-----------------|
| 1 | `worker/runner.py` | 31 | `from ..contracts.decisions import emit_budget_enforcement_decision` | L4 (confirmed) |
| 2 | `worker/runner.py` | 380 | `from ..memory import get_retriever` | L4 (domain context) |
| 3 | `worker/runner.py` | 381 | `from ..planners import get_planner` | L4 (domain planning) |
| 4 | `worker/recovery_claim_worker.py` | 147 | `from app.services.claim_decision_engine import CLAIM_ELIGIBILITY_THRESHOLD` | L4 (confirmed) |
| 5 | `worker/recovery_claim_worker.py` | 268 | `from app.services.claim_decision_engine` | L4 (confirmed) |
| 6 | `worker/recovery_evaluator.py` | 54 | `from app.contracts.decisions import emit_recovery_decision` | L4 (confirmed) |
| 7 | `worker/recovery_evaluator.py` | 215 | `from app.services.recovery_rule_engine` | L4 (confirmed) |
| 8 | `worker/recovery_evaluator.py` | 234 | `from app.services.recovery_matcher import RecoveryMatcher` | L4 (confirmed) |
| 9 | `worker/recovery_evaluator.py` | 254 | `from app.services.recovery_rule_engine import combine_confidences` | L4 (confirmed) |
| 10 | `worker/recovery_evaluator.py` | 273 | `from app.services.recovery_rule_engine import should_select_action` | L4 (confirmed) |
| 11 | `worker/recovery_evaluator.py` | 316 | `from app.services.recovery_rule_engine import should_auto_execute` | L4 (confirmed) |

### 2.2 By L4 Module

| L4 Module | Layer Header | Import Count | L5 Callers |
|-----------|--------------|--------------|------------|
| `contracts.decisions` | L4 (confirmed) | 2 | runner.py, recovery_evaluator.py |
| `memory` (retriever) | **NO HEADER** (domain) | 1 | runner.py |
| `planners` | **NO HEADER** (domain) | 1 | runner.py |
| `services.claim_decision_engine` | L4 (confirmed) | 2 | recovery_claim_worker.py |
| `services.recovery_rule_engine` | L4 (confirmed) | 4 | recovery_evaluator.py |
| `services.recovery_matcher` | L4 (confirmed) | 1 | recovery_evaluator.py |

---

## 3. Classification Analysis

### 3.1 Classification Questions

For each violation, we ask:
1. **Why is L5 importing L4?**
2. **Is L4 acting as:** domain engine (correct) / utility (misplaced) / shortcut for missing interface?
3. **What is the fix type?**

### 3.2 Violation #1-3: runner.py

| # | Import | Why L5 Imports L4 | L4 Role | Fix Type |
|---|--------|-------------------|---------|----------|
| 1 | `emit_budget_enforcement_decision` | L5 needs to emit a decision record | Domain Engine | **Push Up**: L4 should call L5, not vice versa |
| 2 | `get_retriever` | L5 needs memory context for planning | Domain Engine | **Push Up**: Planning belongs in L4, not L5 |
| 3 | `get_planner` | L5 generates execution plan inline | Domain Engine | **Push Up**: Plan generation is L4 logic |

**Analysis for runner.py:**

The runner is doing TOO MUCH. It's not just executing - it's:
- Making budget enforcement decisions (line 31)
- Retrieving memory context (line 380)
- Generating execution plans (line 381)

**Root Cause:** L5 is acting as both DECIDER and EXECUTOR.

**Structural Fix:**
```
CURRENT (violation):
  L2 creates Run → L5 RunRunner generates plan → L5 executes plan

CORRECT (no violation):
  L2 creates Run → L4 PlanGenerator generates plan → L5 executes plan
  L5 RunRunner receives plan from L4, only executes
```

### 3.3 Violation #4-5: recovery_claim_worker.py

| # | Import | Why L5 Imports L4 | L4 Role | Fix Type |
|---|--------|-------------------|---------|----------|
| 4 | `CLAIM_ELIGIBILITY_THRESHOLD` | L5 needs threshold constant | Domain Engine | **Dependency Inversion**: Pass threshold to L5 |
| 5 | `claim_decision_engine` | L5 evaluates claim eligibility | Domain Engine | **Push Up**: Claim evaluation is L4 logic |

**Analysis for recovery_claim_worker.py:**

The worker is importing domain THRESHOLDS and DECISION logic. This means L5 is making claim decisions instead of just claiming work.

**Root Cause:** Claim eligibility logic leaked into L5.

**Structural Fix:**
```
CURRENT (violation):
  L5 worker imports L4 threshold → L5 decides if claim is eligible

CORRECT (no violation):
  L4 claim_decision_engine marks claims as eligible → L5 worker just claims eligible ones
```

### 3.4 Violation #6-11: recovery_evaluator.py

| # | Import | Why L5 Imports L4 | L4 Role | Fix Type |
|---|--------|-------------------|---------|----------|
| 6 | `emit_recovery_decision` | L5 emits decision records | Domain Engine | **Push Up**: L4 should emit, not L5 |
| 7 | `recovery_rule_engine` | L5 evaluates recovery rules | Domain Engine | **Push Up**: Rule evaluation is L4 |
| 8 | `RecoveryMatcher` | L5 matches failure patterns | Domain Engine | **Push Up**: Pattern matching is L4 |
| 9 | `combine_confidences` | L5 combines confidence scores | Domain Engine | **Push Up**: Score combination is L4 |
| 10 | `should_select_action` | L5 decides action selection | Domain Engine | **Push Up**: Selection decision is L4 |
| 11 | `should_auto_execute` | L5 decides auto-execution | Domain Engine | **Push Up**: Execution decision is L4 |

**Analysis for recovery_evaluator.py:**

This is the most severe violation. The "evaluator" is entirely domain logic dressed as a worker. It:
- Evaluates rules (domain)
- Matches patterns (domain)
- Combines confidences (domain)
- Decides actions (domain)
- Decides auto-execution (domain)

**Root Cause:** Domain engine was placed in L5 instead of L4.

**Structural Fix:**
```
CURRENT (violation):
  L5 recovery_evaluator.py imports 6 L4 modules → makes all decisions

CORRECT (no violation):
  L4 RecoveryEvaluationEngine (new) contains all decision logic
  L5 recovery_worker.py just picks up evaluated work and executes it
```

---

## 4. Classification Summary

### 4.1 By Fix Type

| Fix Type | Count | Violations |
|----------|-------|------------|
| **Push Up** (orchestration → L4) | 10 | #1-3, #5-11 |
| **Dependency Inversion** (pass to L5) | 1 | #4 |
| Move Down (L4 → L5) | 0 | - |
| Thin Interface (add L6) | 0 | - |

### 4.2 By Root Cause

| Root Cause | Count | Files |
|------------|-------|-------|
| L5 making decisions it shouldn't | 9 | runner.py, recovery_evaluator.py |
| Domain threshold in L5 | 1 | recovery_claim_worker.py |
| Decision emission from L5 | 2 | runner.py, recovery_evaluator.py |

---

## 5. Missing Layer Headers

The following L4 modules lack explicit layer headers:

| Module | Actual Role | Required Header |
|--------|-------------|-----------------|
| `planners/__init__.py` | Domain planning | `# Layer: L4 — Domain Engine` |
| `memory/__init__.py` | Domain context retrieval | `# Layer: L4 — Domain Engine` |
| `memory/retriever.py` | Domain context building | `# Layer: L4 — Domain Engine` |

**Action:** Add layer headers to confirm L4 classification.

---

## 6. Proposed Repair Sequence

Based on the classification:

### 6.1 Phase R-1: recovery_evaluator.py (Highest Impact)

**Current:** 6 L4 imports, entire file is domain logic
**Fix:** Extract to L4 `RecoveryEvaluationEngine`, L5 just executes

This fixes violations #6-11 (6 violations).

### 6.2 Phase R-2: runner.py Planning Logic

**Current:** Inline plan generation in L5
**Fix:** Move planning to L4, L5 receives plan as input

This fixes violations #2-3 (2 violations).

### 6.3 Phase R-3: runner.py Decision Emission

**Current:** L5 emits budget decisions
**Fix:** L4 service calls emit, L5 reports status

This fixes violation #1 (1 violation).

### 6.4 Phase R-4: recovery_claim_worker.py

**Current:** Threshold constant imported from L4
**Fix:** Pass threshold as configuration or move eligibility check to L4

This fixes violations #4-5 (2 violations).

---

## 7. Verification Checklist

After repairs:

| Check | Status |
|-------|--------|
| `recovery_evaluator.py` has 0 L4 imports | PENDING |
| `runner.py` has 0 L4 imports | PENDING |
| `recovery_claim_worker.py` has 0 L4 imports | PENDING |
| BLCA reports 0 L5→L4 violations | PENDING |
| E2E tests pass | PENDING |
| Layer headers added to planners/memory | PENDING |

---

## 8. Next Steps (After Classification Approval)

1. **Human Decision:** Approve classification and repair sequence
2. **Step 3:** Fix structurally per PHASE_R_ARCHITECTURE_REALIGNMENT.md
3. **Step 4:** Fix E2E deterministically
4. **Step 5:** Enable enforcement

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-01 | L5→L4 violation classification complete |

---

**OBSERVATION COMPLETE — AWAITING APPROVAL FOR STRUCTURAL REPAIR**
