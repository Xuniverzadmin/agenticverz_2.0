# Phase-R: Architecture Realignment to Governance

**STATUS: ACTIVE**

**Date Declared:** 2026-01-01
**Declared By:** Maheshwar VM (Founder / System Owner)
**Purpose:** Make implementation obey declared layer rules

---

## 1. Phase Declaration

```
PHASE-R DECLARATION

Phase-2 enforcement is PAUSED.
Phase-R: Architecture Realignment to Governance is ACTIVE.

Goal: Make implementation obey declared layer rules.
Scope: Resolve BLCA-governance discrepancy before enforcement.

This preserves integrity.
```

---

## 2. Context

### 2.1 The Discrepancy

| Source | L5 Allowed Imports |
|--------|-------------------|
| **CLAUDE.md (Governance)** | L6 only |
| **BLCA (layer_validator.py)** | L4, L5, L6 |

### 2.2 Why This Matters

Enforcement without alignment means:
- CI would pass violations (false negatives)
- Or we'd weaken governance to match broken code

Neither is acceptable.

---

## 3. Phase-R Principles

### 3.1 What Phase-R Allows

| Action | Status |
|--------|--------|
| Classify violations (observation) | ALLOWED |
| Analyze why L5 imports L4 | ALLOWED |
| Propose structural fixes | ALLOWED |
| Create repair plan | ALLOWED |

### 3.2 What Phase-R Forbids

| Action | Status | Reason |
|--------|--------|--------|
| Re-export hacks | FORBIDDEN | Cosmetic, not structural |
| Import indirection tricks | FORBIDDEN | Hides violation |
| "utils.py" dumping | FORBIDDEN | Creates new violations |
| Silencing CI | FORBIDDEN | Defeats purpose |

---

## 4. Repair Taxonomy

### 4.1 Allowed Fix Types

| Fix Type | Description | When to Use |
|----------|-------------|-------------|
| **Move Down** | L4 logic → L5 | If L4 code is really execution logic |
| **Thin Interface** | Add L6 interface | If both layers need same capability |
| **Push Up** | Orchestration → L4 | If L5 is making decisions it shouldn't |
| **Dependency Inversion** | L5 receives from L4 | If L5 needs L4 data at call time |

### 4.2 Forbidden Fix Types

| Fix Type | Why Forbidden |
|----------|---------------|
| Re-export | Doesn't fix structure, just hides import |
| Wrapper module | Creates indirection without clarity |
| Catch-all utils | Becomes new coupling point |
| Accept violation | Weakens governance |

---

## 5. Phase-R Sequence

```
STEP 1: Declare Phase-R ✅ (this document)
STEP 2: Classify every L5→L4 violation (observation, no code)
STEP 3: Fix structurally, not cosmetically
STEP 4: Fix E2E deterministically
STEP 5: Only AFTER repair: enforce
```

---

## 6. Exit Criteria

Phase-R is complete when:

| Criterion | Status |
|-----------|--------|
| L5→L4 violations = 0 | PENDING |
| E2E tests meaningful | PENDING |
| CI failures reflect real violations | PENDING |
| BLCA matches governance | PENDING |
| Enforcement can proceed with confidence | PENDING |

---

## 7. Governance Continuity

Phase-R does not suspend:
- Code registration rules
- Change record requirements
- Artifact governance
- Self-audit requirements

Phase-R only pauses:
- Phase-2 enforcement rollout
- Wave-1 CI job creation

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-01 | Phase-R declared |

---

**PHASE-R ACTIVE — ARCHITECTURE REALIGNMENT IN PROGRESS**
