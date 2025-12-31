# CI Scope Freeze

**Status:** FROZEN
**Date:** 2025-12-30
**Reference:** PIN-250, CI_CANDIDATE_MATRIX.md

---

## Purpose

This document declares the CI scope as frozen during product work.

**Core Principle:**
> CI's job is to protect value, not prove theoretical purity.

---

## Promoted Signals (Rung 3 — Soft Gates)

The following signals are now enforced:

| Signal | Gate Script | Behavior |
|--------|-------------|----------|
| No import-time DB connection | `structural_gates.sh` | Fail on new violations |
| No circular dependencies | `structural_gates.sh` | Fail on new violations |
| tasks/ module wired | `structural_gates.sh` | Fail on new violations |

**Enforcement:** These gates will fail CI if violated.

---

## Deferred Signals (NOT Enforced)

The following signals remain documented but unenforced:

| Signal | Reason | Status |
|--------|--------|--------|
| No DB writes in L2 APIs | Check pattern too broad | Needs refinement |
| Transaction ownership | Scope mismatch | Needs refinement |
| Service write boundaries | High false positive rate | Needs major refinement |

**Enforcement:** None. These signals are observational only.

---

## Freeze Rules

### What Is Frozen

1. **No new CI signals** will be added during product work
2. **No refinement work** on deferred signals
3. **No changes to gate behavior** without governance approval

### What Is Allowed

1. Running existing gates (`structural_gates.sh`)
2. Viewing dry-run reports (`structural_dryrun.sh`)
3. Bug fixes to gate scripts (if gates produce false failures)

### Duration

This freeze remains in effect until:
- Product work phase completes, OR
- A structural regression is detected, OR
- Human explicitly unfreezes

---

## Scripts

| Script | Purpose | Behavior |
|--------|---------|----------|
| `scripts/ci/structural_gates.sh` | Rung 3 enforcement | Fails on violations |
| `scripts/ci/structural_dryrun.sh` | Rung 2 observation | Warns only, never fails |

---

## Rationale

**Why freeze CI scope?**

1. **Momentum over perfection:** 3 strong guardrails are enough to move safely
2. **Avoid churn:** Refining noisy signals now would stall product work
3. **CI pain-driven refinement:** Noisy signals are better refined when they cause real friction

**Why NOT refine noisy signals now?**

1. Refinement is structural/tooling heavy work
2. No product value unlocked by refinement
3. Deferred signals don't protect product work today

---

## References

- `docs/architecture/CI_CANDIDATE_MATRIX.md` — Signal discovery
- `docs/architecture/CI_DRYRUN_EVALUATION_REPORT.md` — Signal quality analysis
- PIN-250 — Structural Truth Extraction Lifecycle
