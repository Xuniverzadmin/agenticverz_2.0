# Phase 2 Retrospective

**Date:** 2025-12-30
**Duration:** Single session
**Reference:** PIN-250

---

## What We Did

Extracted 34 DB write sites from 9 API files into 8 dedicated L4 services.

| Metric | Value |
|--------|-------|
| API files refactored | 9 |
| Write sites extracted | 34 |
| Services created | 8 |
| Behavioral changes | 0 |

---

## What We Intentionally Deferred

### 1. Async/Sync Alignment

**Observation:** Recovery files (`recovery_ingest.py`, `recovery.py`) use sync `Session(engine)` inside `async def` routes.

**Decision:** Preserve as-is. Create sync `RecoveryWriteService`.

**Rationale:** Changing execution model is semantic work, not structural. Phase 2 extracts; it does not normalize.

### 2. Auth L3/L4 Split

**Observation:** `auth/` mixes JWT parsing (L3) with RBAC rules (L4).

**Decision:** Defer to Phase 2C.

**Rationale:** Auth requires careful semantic analysis. Write extraction could proceed independently.

### 3. Cosmetic Naming Debt

**Observation:** `planner/` vs `planners/` duplication; `workers/` vs `worker/` collision.

**Decision:** Defer to Phase 2D.

**Rationale:** Naming changes are high-churn, low-structural-value. Do after CI is in place.

---

## Why CI Was Not Introduced Earlier

**Principle:** CI must measure truth, not encode assumptions.

Before Phase 2:
- API files contained DB writes → L2 collapse
- Import-time execution existed → Hidden side effects
- Write ownership was ambiguous → What would CI even check?

After Phase 2:
- Clear invariant: "No DB writes in L2"
- Clear ownership: "Services own writes"
- CI can now assert real properties

**Lesson:** Premature CI encodes lies at scale. CI discovery requires structural stability first.

---

## Why Extraction ≠ Refactoring

| Extraction | Refactoring |
|------------|-------------|
| Move code to different file | Change code behavior |
| Preserve exact SQL text | Optimize or normalize SQL |
| Call-path relocation | Interface redesign |
| No new logic | Add validation, error handling |

**Phase 2 constraint:** Every write site was relocated with zero semantic change.

**Evidence:**
- SQL text preserved verbatim (verified)
- UPSERT logic unchanged
- Transaction boundaries unchanged
- No new error handling added

---

## Key Learning

> **Structure must be understood before it can be measured.**
> **Structure must be aligned before CI can enforce.**
> **CI discovery is observation, not enforcement.**

These are not temporary rules. They are the ladder.

---

## Next Phase

Phase 3 (CI Discovery) can now begin because:

1. Structural guarantees exist (PHASE2_COMPLETION_GATE.md)
2. Truth map is current (STRUCTURAL_TRUTH_MAP.md)
3. No structural work remains in Phase 2B
4. Deferred items are explicitly documented

CI discovery will produce a **CI Candidate Matrix** — observational only, no enforcement.
