# PIN-257: Phase E-4 Domain Extractions - Critical Findings

**Status:** ✅ COMPLETE
**Created:** 2025-12-31
**Category:** Architecture / Governance
**Milestone:** Phase E

---

## Summary

Tracks Phase E-4 domain extractions, critical governance lessons learned, and institutionalized rules.

---

## Details

## Overview

Phase E-4 implements domain extractions to resolve layer violations identified in Phase E.
This PIN tracks extractions, critical findings, and governance lessons institutionalized.

**Governing Documents:**
- `docs/governance/PHASE_E_FIX_DESIGN.md` — Master extraction plan
- `docs/governance/DOMAIN_EXTRACTION_TEMPLATE.md` — Binding extraction template
- PIN-256 — Raw Architecture Extraction Exercise

---

## Extraction Status

| # | Source (L5) | Engine (L4) | Status | Date |
|---|-------------|-------------|--------|------|
| 1 | failure_aggregation.py | failure_classification_engine.py | ✓ VALIDATED | 2025-12-31 |
| 2 | graduation_evaluator.py | graduation_engine.py (purity fix) | ✓ VALIDATED | 2025-12-31 |
| 3 | recovery_evaluator.py | recovery_rule_engine.py (enhancement) | ✓ VALIDATED | 2025-12-31 |
| 4 | recovery_claim_worker.py | claim_decision_engine.py (new) | ✓ VALIDATED | 2025-12-31 |

---

## Critical Findings

### Finding #1: Function Injection is Semantic Laundering (Extraction #1)

**Problem:** Initial implementation passed callback functions from L5 into L4:
```python
# WRONG - L5 injecting behavior into L4
aggregate_patterns(raw_patterns, category_fn=suggest_category, recovery_fn=suggest_recovery)
```

**Why It's Wrong:**
- Authority appears to move to L4, but control remains in L5
- L4 executes L5-authored logic → dual-role violation
- Breaks Interface Contract (no callbacks allowed)

**Correct Pattern:**
- L4 imports classification authority from OTHER L4 modules (L4 → L4 allowed)
- L5 passes DATA ONLY, receives DECISIONS
- No executable code crosses the L5 → L4 boundary

**Institutionalized:** BLCA-E4-06 (Behavioral Injection Prohibition)

### Finding #2: L4 Engines Must Be Pure From Inception (Extraction #2)

**Problem:** graduation_engine.py was labeled L4 but contained:
- Async methods (fetch_from_database, persist_graduation_status)
- DB imports (sqlalchemy)
- Database read/write operations

**Why It's Wrong:**
- L4 engines must be synchronous (REQUIRED)
- L4 engines must have no side effects
- DB operations are L5/L6 responsibility

**Correct Pattern:**
- L5 fetches evidence FROM database
- L5 calls L4.compute(evidence) — pure, sync
- L5 persists results TO database
- L4 only does domain computation

**Lesson:** Even correctly-named L4 modules can harbor L5/L6 behavior. Purity enforcement is critical.

### Finding #3: Enhancement is Valid Extraction (Extraction #3)

**Context:** Unlike Extractions #1 and #2, `recovery_rule_engine.py` already existed as a properly classified L4 engine with most domain logic correctly placed.

**Problem:** L5 `recovery_evaluator.py` contained inline domain decisions:
```python
# WRONG - Domain decision formula in L5
combined_confidence = (rule_result.confidence + match_result.confidence) / 2

# WRONG - Domain threshold hardcoded in L5
if combined_confidence >= MIN_CONFIDENCE and suggested_action:
```

**Why It's Wrong:**
- Formula for combining confidences is a domain decision
- Threshold for action selection is a domain decision
- L5 should only orchestrate, not decide

**Correct Pattern:**
- Add `combine_confidences()` to existing L4 engine
- Add `should_select_action()` to existing L4 engine
- L5 calls L4 functions, receives decisions
- L4 owns the threshold constants

**Key Insight:** Extraction doesn't always mean creating NEW files. Sometimes it means enhancing existing L4 with missing domain logic from L5.

### Finding #4: Thresholds in SQL Must Reference L4 (Extraction #4)

**Context:** `recovery_claim_worker.py` uses SQL with `FOR UPDATE SKIP LOCKED` for concurrent-safe batch claiming.

**Problem:** Domain threshold hardcoded directly in SQL:
```sql
-- WRONG - Domain threshold hardcoded in SQL
WHERE confidence IS NULL OR confidence <= 0.2
```

**Why It's Wrong:**
- Threshold `0.2` is a domain decision (what qualifies as "unevaluated")
- SQL should receive the threshold as a parameter from L4
- Changing the threshold requires finding and updating SQL strings

**Correct Pattern:**
```python
# L5 imports L4 constant
from app.services.claim_decision_engine import CLAIM_ELIGIBILITY_THRESHOLD

# SQL uses parameter from L4
session.execute(query, {"threshold": CLAIM_ELIGIBILITY_THRESHOLD})
```

**Key Insight:** SQL statements are execution (L5), but the threshold VALUES are domain decisions (L4). L5 must parameterize SQL with L4 constants.

---

## Files Modified

### Extraction #1
- `backend/app/jobs/failure_classification_engine.py` — NEW L4 engine created
- `backend/app/jobs/failure_aggregation.py` — L5 wrapper updated
- `scripts/ops/layer_validator.py` — L4 classification added

### Extraction #2
- `backend/app/integrations/graduation_engine.py` — L4 purified (async/DB removed)
- `backend/app/jobs/graduation_evaluator.py` — L5 updated with DB fetch logic
- `scripts/ops/layer_validator.py` — L4 classification added

### Extraction #3
- `backend/app/services/recovery_rule_engine.py` — L4 enhanced with:
  - `combine_confidences()` — Confidence combination formula
  - `should_select_action()` — Action selection threshold
  - `ACTION_SELECTION_THRESHOLD` — Domain constant (0.3)
- `backend/app/worker/recovery_evaluator.py` — L5 refactored to call L4 functions
- Header updated to reference L4 domain engine

### Extraction #4
- `backend/app/services/claim_decision_engine.py` — NEW L4 engine created with:
  - `is_candidate_claimable()` — Claim eligibility decision
  - `determine_claim_status()` — Status from evaluation result
  - `get_result_confidence()` — Confidence extraction
  - `CLAIM_ELIGIBILITY_THRESHOLD` — Domain constant (0.2)
- `backend/app/worker/recovery_claim_worker.py` — L5 refactored to:
  - Use L4 functions for status determination
  - Parameterize SQL with L4 threshold constant
  - Header updated to reference L4 domain engine
- `scripts/ops/layer_validator.py` — L4 classification added

### Governance Documents
- `docs/governance/DOMAIN_EXTRACTION_TEMPLATE.md` — Added BLCA-E4-06, callable prohibition
- `docs/governance/PHASE_E_FIX_DESIGN.md` — Extraction records added

---

## Institutionalized Rules

### BLCA-E4-06: Behavioral Injection Prohibition

**Rule:** L4 engine must not:
- Accept callable parameters (functions, lambdas, callbacks)
- Execute behavior passed in from callers
- Use `Callable` type hints in public interfaces
- Accept `_fn` suffixed parameters

**Detection:**
- grep for `Callable`, `callable`, `_fn=`, `_fn:`
- AST scan for function-type parameters

**Enforcement:** BLOCKING

---

## BLCA Status

After Extraction #2: **16 violations** (all pre-existing L2 → L5)
- No new violations introduced by extractions
- Violation count stable (not increased)

After Extraction #3: **16 violations** (all pre-existing L2 → L5)
- No new violations introduced by Extraction #3
- Violation count stable (same as after #2)
- L5 → L4 imports are ALLOWED per layer rules

After Extraction #4: **16 violations** (all pre-existing L2 → L5)
- No new violations introduced by Extraction #4
- Violation count stable (same as after #3)
- **ALL EXTRACTIONS COMPLETE**

---

## Next Steps

1. ~~Extraction #1: `failure_aggregation.py` → `failure_classification_engine.py`~~ ✓ VALIDATED
2. ~~Extraction #2: `graduation_evaluator.py` → `graduation_engine.py`~~ ✓ VALIDATED
3. ~~Extraction #3: `recovery_evaluator.py` → `recovery_rule_engine.py`~~ ✓ VALIDATED
4. ~~Extraction #4: `recovery_claim_worker.py` → `claim_decision_engine.py`~~ ✓ VALIDATED
5. **READY FOR PHASE E CLOSURE** — Request authorization for Phase E ratification

---

## Key Governance Principles Reinforced

1. **L4 receives facts. L4 returns decisions. Nothing executable crosses the boundary.**
2. **Extraction reveals truth, not relocates code.**
3. **Reclassification is not a fix — extraction is.**
4. **Sequential extraction only — BLCA must pass between each.**
5. **L4 purity is absolute — async, DB, I/O are L5/L6 responsibilities.**

---


---

## Phase E Complete History

### Update (2025-12-31)

## Phase E Complete History

### E-1: Violation Analysis (COMPLETE)

**10 violations identified** across 4 root causes:

| Root Cause | Violations | Pattern |
|------------|------------|---------|
| RC-1: Domain logic in execution layer | 001, 002 (partial), 006 | A, C |
| RC-2: Execution importing domain layer | 002 (remaining), 003 | A |
| RC-3: Governance influence without signals | 004, 005 | B |
| RC-4: Semantic interpretation without ownership | 007, 008, 009, 010 | D |

**Key insight:** 10 violations collapsed into 4 root causes.

---

### E-2: Fix Design (COMPLETE, RATIFIED)

**4 fixes designed** to address all 10 violations:

| Fix | Name | Target Root Cause |
|-----|------|-------------------|
| FIX-01 | Domain Orchestrator Elevation | RC-1 |
| FIX-02 | Pre-Computed Authorization | RC-2 |
| FIX-03 | Governance Signal Persistence | RC-3 |
| FIX-04 | Interpretation Authority Contract | RC-4 |

**Constraints Met:**
- Fewer artifacts than violations (4 < 10)
- No behavior change
- No new authority

**Status:** RATIFIED with binding constraint on FIX-01 (strict purity test)

---

### E-3: Implementation (COMPLETE)

**Implementation Order:** Structure before boundaries

| Order | Fix | Type | Status |
|-------|-----|------|--------|
| 1 | FIX-03 | Add structure | ✓ COMPLETE |
| 2 | FIX-02 | Add structure | ✓ COMPLETE |
| 3 | FIX-04 | Add structure | ✓ COMPLETE |
| 4 | FIX-01 | Move boundaries | ✓ PARTIAL (1 reclassified, 4 deferred) |

**Artifacts Created:**
- Migration: `064_phase_e_governance_signals.py`
- Migration: `065_precomputed_auth.py`
- Migration: `066_interpretation_ownership.py`
- Model: `app/models/governance.py`
- Model: `app/models/external_response.py`
- Service: `app/services/governance_signal_service.py`
- Service: `app/services/external_response_service.py`

**FIX-01 Strict Purity Test Results:**

| File | Passed 10-Point Test | Action |
|------|---------------------|--------|
| simulate.py | ✓ YES (all 10) | RECLASSIFIED L5→L4 |
| failure_aggregation.py | ✗ NO (#6: filesystem) | DEFERRED to E-4 |
| graduation_evaluator.py | ✗ NO (#7: async-only) | DEFERRED to E-4 |
| recovery_evaluator.py | ✗ NO (#7: async-only) | DEFERRED to E-4 |
| recovery_claim_worker.py | ✗ NO (#5: locks, #6: DB) | DEFERRED to E-4 |

**BLCA after E-3:** PASS (20/20)

---

### E-4: Domain Extractions (IN PROGRESS)

**Rationale:** Files that failed purity test require extraction, not reclassification.

**Extraction Queue:**

| # | Source (L5) | Engine (L4) | Status |
|---|-------------|-------------|--------|
| 1 | failure_aggregation.py | failure_classification_engine.py | ✓ VALIDATED |
| 2 | graduation_evaluator.py | graduation_engine.py (purity fix) | ✓ VALIDATED |
| 3 | recovery_evaluator.py | recovery_rule_engine.py (enhancement) | ✓ VALIDATED |
| 4 | recovery_claim_worker.py | claim_decision_engine.py (new) | ✓ VALIDATED |

**BLCA after E-4 (final):** 16 violations (all pre-existing L2→L5)
- No new violations introduced by Phase E-4
- All extractions complete
- **PHASE E-4: COMPLETE**

## Related PINs

- [PIN-256](PIN-256-.md)
- [PIN-240](PIN-240-.md)
- [PIN-245](PIN-245-.md)
- [PIN-248](PIN-248-.md)
